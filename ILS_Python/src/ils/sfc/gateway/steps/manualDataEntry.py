'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, step):    
    from system.ils.sfc.common.Constants import MANUAL_DATA_CONFIG, AUTO_MODE, AUTOMATIC, DATA, \
    BUTTON_LABEL, POSITION, SCALE, WINDOW_TITLE, REQUIRE_ALL_INPUTS
    from system.ils.sfc import getManualDataEntryConfig 
    from ils.sfc.common.util import isEmpty
    from ils.sfc.gateway.util import getStepId, sendOpenWindow, createWindowRecord, \
        getControlPanelId, waitOnResponse, getStepProperty, deleteAndSendClose, getTimeoutTime, \
        dbStringForFloat, handleUnexpectedGatewayError
    from ils.sfc.gateway.api import getChartLogger, getDatabaseName, s88GetType, parseValue, \
    getUnitsPath, s88Set, s88Get, s88SetWithUnits, getProject
    import system.db
    
    try:
        chartScope = scopeContext.getChartScope()
        stepScope = scopeContext.getStepScope()
        stepProperties = step.getProperties();
        chartLogger = getChartLogger(chartScope)
    
        # window common properties:
     
        #logger = getChartLogger(chartScope)
        autoMode = getStepProperty(stepProperties, AUTO_MODE)
        configJson = getStepProperty(stepProperties, MANUAL_DATA_CONFIG)
        config = getManualDataEntryConfig(configJson)
        if autoMode == AUTOMATIC:
            for row in config.rows:
                s88Set(chartScope, stepScope, row.key, row.defaultValue, row.destination)
        else:
            database = getDatabaseName(chartScope)
            controlPanelId = getControlPanelId(chartScope)
            buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL) 
            if isEmpty(buttonLabel):
                buttonLabel = 'Enter Data'
            position = getStepProperty(stepProperties, POSITION) 
            scale = getStepProperty(stepProperties, SCALE) 
            title = getStepProperty(stepProperties, WINDOW_TITLE) 
            windowId = createWindowRecord(controlPanelId, 'SFC/ManualDataEntry', buttonLabel, position, scale, title, database)
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
            
            timeoutTime = getTimeoutTime(chartScope, stepProperties)
            response = waitOnResponse(windowId, chartScope, timeoutTime)
            
            if response != None:
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
            else:
                pass
                # timeout--is some action needed?
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in manualDataEntry.py', chartLogger)
    finally:
        system.db.runUpdateQuery("delete from SfcManualDataEntryTable where windowId = '%s'" % (windowId), database)
        system.db.runUpdateQuery("delete from SfcManualDataEntry where windowId = '%s'" % (windowId), database)
        project = getProject(chartScope)
        deleteAndSendClose(project, windowId, database)
