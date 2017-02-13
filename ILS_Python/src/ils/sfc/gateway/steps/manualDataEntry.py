'''
Created on Dec 17, 2015

@author: rforbes
'''

import system, time
from system.ils.sfc import getManualDataEntryConfig 
from ils.sfc.common.util import isEmpty
from ils.sfc.gateway.util import getStepId, registerWindowWithControlPanel, deleteAndSendClose, \
    getControlPanelId, getControlPanelName, getStepProperty, getTimeoutTime, logStepDeactivated, \
    dbStringForFloat, handleUnexpectedGatewayError, getTopChartRunId, getOriginator
from ils.sfc.gateway.api import getChartLogger, getDatabaseName, s88GetType, parseValue, getUnitsPath, \
    s88SetWithUnits, s88GetWithUnits, getProject, sendMessageToClient, getProject
from ils.sfc.recipeData.api import s88Set, s88Get, s88GetTargetStepUUID
from ils.sfc.common.constants import WAITING_FOR_REPLY, TIMEOUT_TIME, WINDOW_ID, TIMED_OUT,  \
    AUTO_MODE, AUTOMATIC, DATA, BUTTON_LABEL, POSITION, SCALE, WINDOW_TITLE, REQUIRE_ALL_INPUTS, MANUAL_DATA_CONFIG, \
    DEACTIVATED, ACTIVATED, PAUSED, CANCELLED, DATABASE, CONTROL_PANEL_ID, \
    CONTROL_PANEL_NAME, ORIGINATOR, WINDOW_PATH, STEP_ID, NAME, TARGET_STEP_UUID, KEY

def activate(scopeContext, stepProperties, state):    
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    stepName=stepScope.get(NAME, "Unknown")
    logger = getChartLogger(chartScope)
    windowPath = "SFC/ManualDataEntry"
    messageHandler = "sfcOpenWindow"

    if state == DEACTIVATED or state == CANCELLED:
        logStepDeactivated(chartScope, stepProperties)
        cleanup(chartScope, stepScope)
        return False
        
    try:   
        workDone = False
        waitingForReply = stepScope.get(WAITING_FOR_REPLY, False);
     
        if not waitingForReply:
            logger.trace("Initializing Manual Data Entry step: %s" % (stepName))
            autoMode = getStepProperty(stepProperties, AUTO_MODE)
            configJson = getStepProperty(stepProperties, MANUAL_DATA_CONFIG)
            config = getManualDataEntryConfig(configJson)

            if autoMode == AUTOMATIC:
                for row in config.rows:
                    s88Set(chartScope, stepScope, row.key, row.defaultValue, row.destination)
                workDone = True
            else:
                stepScope[WAITING_FOR_REPLY] = True
                timeoutTime = getTimeoutTime(chartScope, stepProperties)
                logger.trace("The timeoutTime is: %s" % (str(timeoutTime)))
                stepScope[TIMEOUT_TIME] = timeoutTime
                stepScope[TIMED_OUT] = False
                
                database = getDatabaseName(chartScope)
                originator = getOriginator(chartScope)
                project = getProject(chartScope)
                controlPanelId = getControlPanelId(chartScope)
                controlPanelName = getControlPanelName(chartScope)
                chartRunId = getTopChartRunId(chartScope)
                
                buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL) 
                if isEmpty(buttonLabel):
                    buttonLabel = 'Enter Data'

                position = getStepProperty(stepProperties, POSITION) 
                scale = getStepProperty(stepProperties, SCALE) 
                title = getStepProperty(stepProperties, WINDOW_TITLE) 
                windowId = registerWindowWithControlPanel(chartRunId, controlPanelId, windowPath, buttonLabel, position, scale, title, database)
                stepScope[WINDOW_ID] = windowId
                stepId = getStepId(stepProperties) 
                requireAllInputs = getStepProperty(stepProperties, REQUIRE_ALL_INPUTS)
                if timeoutTime == None:
                    logger.trace("...inserting Manual Data Entry record without a timeout...")
                    system.db.runUpdateQuery("insert into SfcManualDataEntry (windowId, requireAllInputs, complete) values ('%s', %d, 0)" % (windowId, requireAllInputs), database)
                else:
                    logger.trace("...inserting Manual Data Entry record WITH a timeout...")
                    system.db.runUpdateQuery("insert into SfcManualDataEntry (windowId, requireAllInputs, complete, timeout) values ('%s', %d, 0, %s)" % (windowId, requireAllInputs, str(timeoutTime)), database)
                
                rowNum = 0
                for row in config.rows:
                    tagType = s88GetType(chartScope, stepScope, row.key, row.destination)
                    existingUnitsKey = getUnitsPath(row.key)
                    existingUnitsName = s88Get(chartScope, stepScope, existingUnitsKey, row.destination)

                    if row.defaultValue == None or row.defaultValue == "":
                        if row.units == "" or existingUnitsName == "":
                            defaultValue = s88Get(chartScope, stepScope, row.key, row.destination)
                            logger.trace("   Row %i: using the CURRENT value: <%s>" % (rowNum, defaultValue))
                        else:
                            defaultValue = s88GetWithUnits(chartScope, stepScope, row.key, row.destination, row.units)
                            defaultValue = "%.4f" % (defaultValue)
                            logger.trace("   Row %i: using the CURRENT value: <%s> (%s)" % (rowNum, defaultValue, row.units))
                    else:
                        defaultValue = str(row.defaultValue)
                        logger.trace("   Row %i: using the default value: <%s>" % (rowNum, defaultValue))

                    lowLimitDbStr = dbStringForFloat(row.lowLimit)
                    highLimitDbStr = dbStringForFloat(row.highLimit)
                    SQL = "insert into SfcManualDataEntryTable (windowId, rowNum, description, value, units, lowLimit, highLimit, dataKey, "\
                        "destination, type, recipeUnits) values ('%s', %d, '%s', '%s', '%s', %s, %s, '%s', '%s', '%s', '%s')" \
                        % (windowId, rowNum, row.prompt, defaultValue, row.units, lowLimitDbStr, highLimitDbStr, row.key, row.destination, tagType, existingUnitsName)
                    system.db.runUpdateQuery(SQL, database)
                    rowNum = rowNum + 1

                # This step does not communicate back though recipe data, rather it uses the step configuration data in the Manuald Data Entry table,
                # So we don't really need to pass the id and key but we need to keep the API happy.
                payload = {WINDOW_ID: windowId, WINDOW_PATH: windowPath, TARGET_STEP_UUID: stepId, KEY: ""}
                sendMessageToClient(chartScope, messageHandler, payload)
        else:
            windowId = stepScope[WINDOW_ID]
            complete, timedOut = checkIfComplete(chartScope, stepScope, stepProperties)
            if complete:
                logger.trace("Manual Data Entry step %s has completed!" % (stepName))
                workDone = True
                saveResponse(chartScope, stepScope, stepProperties, logger)
                if timedOut:
                    stepScope[TIMED_OUT] = True

            else:
                timeoutTime = stepScope[TIMEOUT_TIME]
                if timeoutTime <> None:
                    cushion = 10.0
                    logger.trace("...checking for a timeout, the block will timeout in %f seconds..." % (timeoutTime - time.time() + cushion))
                    # The timeout is really handled at the client - the client should timeout and update the database before this even
                    # runs because of an added 10 second time buffer.  This will handle the case where there are no clients connected.
                    # The gateway does not have the burden of keeping track of all of the clients. 
                    if timeoutTime < (time.time() - cushion):
                        logger.trace("Manual Data Entry step %s has timed out..." % (stepName))
                        workDone = True
                        # I'm pretty sure that when a block times out we should use whatever the defaults were.
                        # If the user has partially completed the form but not hit OK the partial responses will not be used.
                        saveResponse(chartScope, stepScope, stepProperties, logger)
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in manualDataEntry.py', logger)
        workDone = True
    finally:
        if workDone:
            cleanup(chartScope, stepScope)
        return workDone

def saveResponse(chartScope, stepScope, stepProperties, logger):
    logger.trace("...saving values:")
    pds = getResponse(chartScope, stepScope, stepProperties)

    # Note: all values are returned as strings; we depend on s88Set to make the conversion
    for record in pds:
        strValue = record['value']
        units = record['units']
        key = record['dataKey']
        destination = record['destination']
        valueType = record['type']
        
        logger.trace("  %s: %s %s" % (key, strValue, units))
        
        value = parseValue(strValue, valueType)
        if isEmpty(units):
            s88Set(chartScope, stepScope, key, value, destination)
        else:
            s88SetWithUnits(chartScope, stepScope, key, value, destination, units)

def checkIfComplete(chartScope, stepScope, stepProperties):
    database = getDatabaseName(chartScope)
    windowId = stepScope[WINDOW_ID]
    pds=system.db.runQuery("select complete, timedOut from SfcManualDataEntry where windowId = '%s'" % (windowId), database=database)
    if len(pds) != 1:
        return True, False
    record = pds[0]
    complete = record["complete"]
    timedOut = record["timedOut"]
    return complete, timedOut

def getResponse(chartScope, stepScope, stepProperties):
    database = getDatabaseName(chartScope)
    windowId = stepScope[WINDOW_ID]
    pds=system.db.runQuery("select * from SfcManualDataEntryTable where windowId = '%s'" % (windowId),database=database)
    return pds

def cleanup(chartScope, stepScope):
    try:
        database = getDatabaseName(chartScope)
        project = getProject(chartScope)
        windowId = stepScope.get(WINDOW_ID, '???')
        system.db.runUpdateQuery("delete from SfcManualDataEntryTable where windowId = '%s'" % (windowId), database)
        system.db.runUpdateQuery("delete from SfcManualDataEntry where windowId = '%s'" % (windowId), database)
        deleteAndSendClose(project, windowId, database)
    except:
        chartLogger = getChartLogger(chartScope)
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in cleanup in manualDataEntry.py', chartLogger)

