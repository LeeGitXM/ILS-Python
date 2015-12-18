'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):    
    from system.ils.sfc.common.Constants import MANUAL_DATA_CONFIG, AUTO_MODE, AUTOMATIC, DATA
    from system.ils.sfc import getManualDataEntryConfig 
    from system.dataset import toDataSet
    from ils.sfc.common.util import isEmpty
    from ils.sfc.gateway.util import sendMessageToClient, waitOnResponse, getStepProperty, transferStepPropertiesToMessage
    from ils.sfc.gateway.api import s88GetType, parseValue, getUnitsPath, s88Set, s88Get, s88SetWithUnits
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    #logger = getChartLogger(chartScope)
    autoMode = getStepProperty(stepProperties, AUTO_MODE)
    configJson = getStepProperty(stepProperties, MANUAL_DATA_CONFIG)
    config = getManualDataEntryConfig(configJson)
    if autoMode == AUTOMATIC:
        for row in config.rows:
            s88Set(chartScope, stepScope, row.key, row.defaultValue, row.destination)
    else:
        header = ['Description', 'Value', 'Units', 'Low Limit', 'High Limit', 'Key', 'Destination', 'Type', 'Recipe Units']    
        rows = []
        # Note: apparently the IA toDataSet method tries to coerce all column values to
        # the same type and throws an error if that is not possible. Since we potentially
        # have a mixture of float and string values, we convert them all to strings:
        for row in config.rows:
            tagType = s88GetType(chartScope, stepScope, row.key, row.destination)
            if row.defaultValue != None:
                defaultValue = str(row.defaultValue)
            else:
                defaultValue = ""
            existingUnitsKey = getUnitsPath(row.key)
            existingUnitsName = s88Get(chartScope, stepScope, existingUnitsKey, row.destination)
            rows.append([row.prompt, defaultValue, row.units, row.lowLimit, row.highLimit, row.key, row.destination, tagType, existingUnitsName])
        dataset = toDataSet(header, rows)
        payload = dict()
        transferStepPropertiesToMessage(stepProperties, payload)
        payload[DATA] = dataset
        messageId = sendMessageToClient(chartScope, 'sfcManualDataEntry', payload)             
        response = waitOnResponse(messageId, chartScope)
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
