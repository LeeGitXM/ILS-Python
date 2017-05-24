'''
Created on Dec 17, 2015

@author: rforbes

'''

import system, time, string
from system.ils.sfc import getManualDataEntryConfig 
from ils.sfc.common.util import isEmpty
from ils.common.cast import isFloat, isInteger
from ils.sfc.gateway.util import getStepId, registerWindowWithControlPanel, deleteAndSendClose, \
    getControlPanelId, getControlPanelName, getStepProperty, getTimeoutTime, logStepDeactivated, \
    dbStringForFloat, handleUnexpectedGatewayError, getTopChartRunId, getOriginator
from ils.sfc.gateway.api import getChartLogger, getDatabaseName, getProviderName, parseValue, getUnitsPath, \
    getProject, sendMessageToClient, getProject
from ils.sfc.recipeData.api import s88Set, s88Get, s88GetTargetStepUUID, s88SetWithUnits, s88GetWithUnits, s88GetType
from ils.sfc.common.constants import WAITING_FOR_REPLY, TIMEOUT_TIME, WINDOW_ID, TIMED_OUT,  \
    AUTO_MODE, AUTOMATIC, DATA, BUTTON_LABEL, POSITION, SCALE, WINDOW_TITLE, REQUIRE_ALL_INPUTS, MANUAL_DATA_CONFIG, \
    DEACTIVATED, ACTIVATED, PAUSED, CANCELLED, DATABASE, CONTROL_PANEL_ID, IS_SFC_WINDOW, \
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
        cleanup(chartScope, stepProperties, stepScope)
        return False
        
    try:   
        workDone = False
        waitingForReply = stepScope.get(WAITING_FOR_REPLY, False);
     
        if not waitingForReply:
            logger.trace("Initializing Manual Data Entry step: %s" % (stepName))
            autoMode = getStepProperty(stepProperties, AUTO_MODE)
            configJson = getStepProperty(stepProperties, MANUAL_DATA_CONFIG)
            config = getManualDataEntryConfig(configJson)
            provider = getProviderName(chartScope)
            database = getDatabaseName(chartScope)

            if autoMode == AUTOMATIC:
                for row in config.rows:
                    if string.upper(row.destination) == "TAG":
                        tagPath = "[%s]%s" % (provider, row.key)
                        system.tag.write(tagPath, row.defaultValue)
                    elif row.units == "": 
                        s88Set(chartScope, stepScope, row.key, row.defaultValue, row.destination)
                    else:
                        s88SetWithUnits(chartScope, stepScope, row.key, row.defaultValue, row.destination, row.units)
                workDone = True
            else:
                stepScope[WAITING_FOR_REPLY] = True
                controlPanelId = getControlPanelId(chartScope)
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

                logger.trace("...inserting Manual Data Entry record without a timeout...")
                system.db.runUpdateQuery("insert into SfcManualDataEntry (windowId, requireAllInputs, complete) values ('%s', %d, 0)" % (windowId, requireAllInputs), database)
                
                rowNum = 0
                for row in config.rows:
                    logger.tracef("Getting the default value for row: %d <%s>", rowNum, str(row.defaultValue))
                    if row.defaultValue in [None, "None"]:
                        logger.tracef("   ...using <None> as the default value... ")
                        defaultValue = ""
                    
                    elif str(row.defaultValue).strip() == "":
                        logger.tracef("...reading the current value from destination: %s", row.destination)
                        if string.upper(row.destination) == "TAG":
                            tagPath = "[%s]%s" % (provider, row.key)
                            logger.tracef("...reading the current value from tagPath: %s", tagPath)
                            qv = system.tag.read(tagPath)
                            if qv.quality.isGood():
                                defaultValue = qv.value
                            else:
                                defaultValue = ""
                                logger.warnf("Unable to acquire a defualt value for %s whose value is bad", tagPath)
                            logger.tracef("   ...using the CURRENT value from a tag: <%s>", str(defaultValue))
                        else:
                            if row.units == "":
                                defaultValue = s88Get(chartScope, stepScope, row.key, row.destination)
                                logger.tracef("   ...using the CURRENT value from Recipe Data: <%s>", defaultValue)
                            else:
                                defaultValue = s88GetWithUnits(chartScope, stepScope, row.key, row.destination, row.units)
                                defaultValue = "%.4f" % (defaultValue)  # Since there are units, it must be numeric??
                                logger.tracef("   ...using the CURRENT value from Recipe Data with units: <%s> (%s)" % (defaultValue, row.units))

                    else:
                        defaultValue = str(row.defaultValue)
                        logger.trace("   ...using the supplied default value: <%s>" % (defaultValue))

                    if isFloat(defaultValue):
                        valueType = "Float"
                    elif isInteger(defaultValue):
                        valueType = "Integer"
                    else:
                        valueType = "String"
                    
                    if string.upper(row.destination) == "TAG":
                        targetStepUUID = ''
                    else:
                        targetStepUUID = s88GetTargetStepUUID(chartScope, stepScope, row.destination)
                        
                    lowLimitDbStr = dbStringForFloat(row.lowLimit)
                    highLimitDbStr = dbStringForFloat(row.highLimit)
                    SQL = "insert into SfcManualDataEntryTable (windowId, rowNum, description, value, units, lowLimit, highLimit, dataKey, "\
                        "destination, targetStepUUID, type, recipeUnits) values ('%s', %d, '%s', '%s', '%s', %s, %s, '%s', '%s', '%s', '%s', '%s')" \
                        % (windowId, rowNum, row.prompt, defaultValue, row.units, lowLimitDbStr, highLimitDbStr, row.key, row.destination, targetStepUUID, valueType, row.units)
                    logger.tracef(SQL)
                    system.db.runUpdateQuery(SQL, database)
                    rowNum = rowNum + 1

                # This step does not communicate back though recipe data, rather it uses the step configuration data in the Manuald Data Entry table,
                # So we don't really need to pass the id and key but we need to keep the API happy.
                payload = {WINDOW_ID: windowId, WINDOW_PATH: windowPath, TARGET_STEP_UUID: stepId, KEY: "", IS_SFC_WINDOW: True}
                sendMessageToClient(chartScope, messageHandler, payload)
        else:
            windowId = stepScope[WINDOW_ID]
            database = getDatabaseName(chartScope)
            windowId = stepScope[WINDOW_ID]
            pds=system.db.runQuery("select complete from SfcManualDataEntry where windowId = '%s'" % (windowId), database=database)
            if len(pds) != 1:
                complete = True
            else:
                record = pds[0]
                complete = record["complete"]

            if complete:
                logger.trace("Manual Data Entry step %s has completed!" % (stepName))
                workDone = True

    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in manualDataEntry.py', logger)
        workDone = True
    finally:
        if workDone:
            cleanup(chartScope, stepProperties, stepScope)
        return workDone


def cleanup(chartScope, stepProperties, stepScope):
    try:
        database = getDatabaseName(chartScope)
        project = getProject(chartScope)
        windowId = stepScope.get(WINDOW_ID, '???')
        system.db.runUpdateQuery("delete from SfcManualDataEntryTable where windowId = '%s'" % (windowId), database)
        system.db.runUpdateQuery("delete from SfcManualDataEntry where windowId = '%s'" % (windowId), database)
        deleteAndSendClose(project, windowId, database)
    except:
        chartLogger = getChartLogger(chartScope)
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in cleanup in manualDataEntry.py', chartLogger)

