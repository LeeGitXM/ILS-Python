'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties, deactivate):    
    from system.ils.sfc.common.Constants import MANUAL_DATA_CONFIG, AUTO_MODE, AUTOMATIC, DATA, \
    BUTTON_LABEL, POSITION, SCALE, WINDOW_TITLE, REQUIRE_ALL_INPUTS
    from system.ils.sfc import getManualDataEntryConfig 
    from ils.sfc.common.util import isEmpty
    from ils.sfc.gateway.util import getStepId, sendOpenWindow, createWindowRecord, \
        getControlPanelId, getStepProperty, getTimeoutTime, \
        dbStringForFloat, handleUnexpectedGatewayError
    from ils.sfc.gateway.api import getChartLogger, getDatabaseName, s88GetType, parseValue, \
    getUnitsPath, s88Set, s88Get, s88SetWithUnits
    from ils.sfc.common.constants import WAITING_FOR_REPLY, TIMEOUT_TIME, TIMEOUT_RESPONSE, WINDOW_ID
    from ils.sfc.gateway.util import checkForResponse
    import system.db
   
    try:
        chartScope = scopeContext.getChartScope()
        stepScope = scopeContext.getStepScope()
        chartLogger = getChartLogger(chartScope)
    
        workDone = False
        waitingForReply = stepScope.get(WAITING_FOR_REPLY, False);
     
        if not waitingForReply:
            autoMode = getStepProperty(stepProperties, AUTO_MODE)
            configJson = getStepProperty(stepProperties, MANUAL_DATA_CONFIG)
            config = getManualDataEntryConfig(configJson)
            if autoMode == AUTOMATIC:
                for row in config.rows:
                    s88Set(chartScope, stepScope, row.key, row.defaultValue, row.destination)
            else:
                stepScope[WAITING_FOR_REPLY] = True
                timeoutTime = getTimeoutTime(chartScope, stepProperties)
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
                system.db.runUpdateQuery("insert into SfcManualDataEntry (windowId, requireAllInputs) values ('%s', %d)" % (windowId, requireAllInputs), database)
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
                    ++rowNum
                sendOpenWindow(chartScope, windowId, stepId, database)
            
        else:
            response = checkForResponse(chartScope, stepScope, stepProperties, TIMEOUT_RESPONSE)                
            if response != None:
                if response != TIMEOUT_RESPONSE:
                    returnDataset = response[DATA]
                    # Note: all values are returned as strings; we depend on s88Set to make the conversion
                    for row in range(returnDataset.rowCount):
                        strValue = returnDataset.getValueAt(row, 1)
                        units = returnDataset.getValueAt(row, 2)
                        key = returnDataset.getValueAt(row, 5)
                        destination = returnDataset.getValueAt(row, 6)
                        valueType = returnDataset.getValueAt(row, 7)
                        value = parseValue(strValue, valueType)
                        if isEmpty(units):
                            s88Set(chartScope, stepScope, key, value, destination)
                        else:
                            s88SetWithUnits(chartScope, stepScope, key, value, destination, units)
                    workDone = True
                else:
                    # timeout!! --is some action needed?
                    workDone = True
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in manualDataEntry.py', chartLogger)
        workDone = True
    finally:
        if workDone:
            cleanup(chartScope, stepScope)
        return workDone
   
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

