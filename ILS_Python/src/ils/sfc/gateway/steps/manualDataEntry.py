'''
Created on Dec 17, 2015

@author: rforbes
'''

import system
from system.ils.sfc.common.Constants import MANUAL_DATA_CONFIG, AUTO_MODE, AUTOMATIC, DATA, BUTTON_LABEL, POSITION, SCALE, WINDOW_TITLE, REQUIRE_ALL_INPUTS
from system.ils.sfc.common.Constants import DEACTIVATED, ACTIVATED, PAUSED, CANCELLED
from system.ils.sfc import getManualDataEntryConfig 
from ils.sfc.common.util import isEmpty
from ils.sfc.gateway.util import getStepId, sendOpenWindow, createWindowRecord, \
    getControlPanelId, getStepProperty, getTimeoutTime, logStepDeactivated, \
    dbStringForFloat, handleUnexpectedGatewayError
from ils.sfc.gateway.api import getChartLogger, getDatabaseName, s88GetType, parseValue, getUnitsPath, s88Set, s88Get, s88SetWithUnits
from ils.sfc.common.constants import WAITING_FOR_REPLY, TIMEOUT_TIME, WINDOW_ID, TIMED_OUT
    
def activate(scopeContext, stepProperties, state):    
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    chartLogger = getChartLogger(chartScope)

    if state == DEACTIVATED or state == CANCELLED:
        logStepDeactivated(chartScope, stepProperties)
        cleanup(chartScope, stepScope)
        return False
        
    try:   
        workDone = False
        waitingForReply = stepScope.get(WAITING_FOR_REPLY, False);
     
        if not waitingForReply:
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
                print "The timeoutTime is: ", timeoutTime
                stepScope[TIMEOUT_TIME] = timeoutTime
                database = getDatabaseName(chartScope)
                controlPanelId = getControlPanelId(chartScope)
                buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL) 
                if isEmpty(buttonLabel):
                    buttonLabel = 'Enter Data'
                position = getStepProperty(stepProperties, POSITION) 
                scale = getStepProperty(stepProperties, SCALE) 
                title = getStepProperty(stepProperties, WINDOW_TITLE) 
                windowId = createWindowRecord(controlPanelId, 'SFC/ManualDataEntry', buttonLabel, position, scale, title, database)
                stepScope[WINDOW_ID] = windowId
                stepId = getStepId(stepProperties) 
                requireAllInputs = getStepProperty(stepProperties, REQUIRE_ALL_INPUTS)
                if timeoutTime == None:
                    print "Inserting without a timeout..."
                    system.db.runUpdateQuery("insert into SfcManualDataEntry (windowId, requireAllInputs, complete) values ('%s', %d, 0)" % (windowId, requireAllInputs), database)
                else:
                    print "Inserting WITH a timeout..."
                    system.db.runUpdateQuery("insert into SfcManualDataEntry (windowId, requireAllInputs, complete, timeout) values ('%s', %d, 0, %s)" % (windowId, requireAllInputs, str(timeoutTime)), database)
                rowNum = 0
                for row in config.rows:
                    tagType = s88GetType(chartScope, stepScope, row.key, row.destination)
                    if row.defaultValue != None:
                        defaultValue = str(row.defaultValue)
                    else:
                        defaultValue = ""
                    existingUnitsKey = getUnitsPath(row.key)
                    existingUnitsName = s88Get(chartScope, stepScope, existingUnitsKey, row.destination)
                    lowLimitDbStr = dbStringForFloat(row.lowLimit)
                    highLimitDbStr = dbStringForFloat(row.highLimit)
                    system.db.runUpdateQuery("insert into SfcManualDataEntryTable (windowId, rowNum, description, value, units, lowLimit, highLimit, dataKey, destination, type, recipeUnits) values ('%s', %d, '%s', '%s', '%s', %s, %s, '%s', '%s', '%s', '%s')" % (windowId, rowNum, row.prompt, defaultValue, row.units, lowLimitDbStr, highLimitDbStr, row.key, row.destination, tagType, existingUnitsName), database)
                    rowNum = rowNum + 1
                sendOpenWindow(chartScope, windowId, stepId, database)
            
        else:
            complete = checkIfComplete(chartScope, stepScope, stepProperties)                
            if complete:
                workDone = True
                pds = getResponse(chartScope, stepScope, stepProperties)

                # Note: all values are returned as strings; we depend on s88Set to make the conversion
                for record in pds:
                    strValue = record['value']
                    units = record['units']
                    key = record['dataKey']
                    destination = record['destination']
                    valueType = record['type']
                    
                    value = parseValue(strValue, valueType)
                    if isEmpty(units):
                        s88Set(chartScope, stepScope, key, value, destination)
                    else:
                        s88SetWithUnits(chartScope, stepScope, key, value, destination, units)
            else:
                print "Need to check for a timeout"
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in manualDataEntry.py', chartLogger)
        workDone = True
    finally:
        if workDone:
            cleanup(chartScope, stepScope)
        return workDone

def checkIfComplete(chartScope, stepScope, stepProperties):
    database = getDatabaseName(chartScope)
    windowId = stepScope[WINDOW_ID]
    complete=system.db.runScalarQuery("select complete from SfcManualDataEntry where windowId = '%s'" % (windowId), database=database)
    return complete

def getResponse(chartScope, stepScope, stepProperties):
    database = getDatabaseName(chartScope)
    windowId = stepScope[WINDOW_ID]
    pds=system.db.runQuery("select * from SfcManualDataEntryTable where windowId = '%s'" % (windowId),database=database)
    return pds

def cleanup(chartScope, stepScope):
    import system.db
    from ils.sfc.gateway.util import deleteAndSendClose, handleUnexpectedGatewayError
    from ils.sfc.gateway.api import getDatabaseName, getProject, getChartLogger
    from ils.sfc.common.constants import WINDOW_ID
    try:
        database = getDatabaseName(chartScope)
        project = getProject(chartScope)
        windowId = stepScope.get(WINDOW_ID, '???')
        system.db.runUpdateQuery("delete from SfcManualDataEntryTable where windowId = '%s'" % (windowId), database)
        system.db.runUpdateQuery("delete from SfcManualDataEntry where windowId = '%s'" % (windowId), database)
        project = getProject(chartScope)
        deleteAndSendClose(project, windowId, database)
    except:
        chartLogger = getChartLogger(chartScope)
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in cleanup in manualDataEntry.py', chartLogger)

