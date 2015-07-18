'''
Functions that are shared by custom and pre-defined steps

Created on Oct 30, 2014

@author: rforbes
'''

def getProviderName(chartProperties):
    from system.ils.sfc import getProviderName, getIsolationMode
    return getProviderName(getIsolationMode(chartProperties))

def s88DataExists(chartProperties, stepProperties, valuePath, location):
    from system.ils.sfc import getRecipeDataTagPath
    from ils.sfc.common.recipe import recipeDataTagExists
    provider = getProviderName(chartProperties)
    tagPath = getRecipeDataTagPath(chartProperties, stepProperties, location)
    return recipeDataTagExists(provider, tagPath);
  
def s88Get(chartProperties, stepProperties, valuePath, location):
    from system.ils.sfc import getRecipeDataTagPath
    from ils.sfc.common.recipe import getRecipeData
    provider = getProviderName(chartProperties)
    print 's88Get', valuePath, location
    stepPath = getRecipeDataTagPath(chartProperties, stepProperties, location)
    fullPath = stepPath + "/" + valuePath
    return getRecipeData(provider, fullPath);

def s88Set(chartProperties, stepProperties, valuePath, value, location):
    from system.ils.sfc import getRecipeDataTagPath
    from ils.sfc.common.recipe import setRecipeData
    provider = getProviderName(chartProperties)
    print 's88Set', valuePath, location
    stepPath = getRecipeDataTagPath(chartProperties, stepProperties, location)
    fullPath = stepPath + "/" + valuePath
    setRecipeData(provider, fullPath, value, True);
    
def getUnitsPath(valuePath):
    '''Get the units associated with a value; None if not found'''
    valueKeyIndex = valuePath.find(".value")
    if valueKeyIndex > 0:
        return valuePath[0 : valueKeyIndex] + ".units"
    else:
        raise Exception("no value field to get units for in " + valuePath)

def s88GetWithUnits(chartProperties, stepProperties, valuePath, location, returnUnitsName):
    from ils.common.units import Unit
    from ils.sfc.common.util import getDatabaseName
    value = s88Get(chartProperties, stepProperties, valuePath, location)
    unitsPath = getUnitsPath(valuePath)
    existingUnitsName = s88Get(chartProperties, stepProperties, unitsPath, location)
    database = getDatabaseName(chartProperties)
    Unit.lazyInitialize(database)
    existingUnits = Unit.getUnit(existingUnitsName)
    if(existingUnits == None):
        raise Exception("No unit found for " + existingUnitsName)
    returnUnits = Unit.getUnit(returnUnitsName)
    if(returnUnits == None):
        raise Exception("No unit found for " + returnUnitsName)
    convertedValue = existingUnits.convertTo(returnUnits, value)
    return convertedValue

def s88SetData(chartProperties, stepProperties, valuePath, value, location):
    s88Set(chartProperties, stepProperties, valuePath, value, location)
    
def s88SetWithUnits(chartProperties, stepProperties, valuePath, value, location, newUnitsName):
    s88Set(chartProperties, stepProperties, valuePath, value, location)
    #TODO: fix the unit conversion
    #unitsPath = getUnitsPath(valuePath)
    #s88Set(chartProperties, stepProperties, unitsPath, location, newUnitsName)
        
def pauseChart(chartProperties):
    '''pause the entire chart hierarchy--we pause the top level chart and expect
       the eclosed charts to pause as well'''
    from system.sfc import pauseChart
    from ils.sfc.common.util import getTopChartRunId
    chartRunId = getTopChartRunId(chartProperties)
    pauseChart(chartRunId)
    
def resumeChart(chartProperties):
    '''resume the entire chart hierarchy--we pause the top level chart and expect
       the eclosed charts to pause as well'''
    from system.sfc import resumeChart
    from ils.sfc.common.util import getTopChartRunId
    chartRunId = getTopChartRunId(chartProperties)
    resumeChart(chartRunId)

def cancelChart(chartProperties):
    '''cancel the entire chart hierarchy--we pause the top level chart and expect
       the eclosed charts to pause as well'''
    from system.sfc import cancelChart
    from ils.sfc.common.util import getTopChartRunId
    chartRunId = getTopChartRunId(chartProperties)
    cancelChart(chartRunId)

def addControlPanelMessage(chartProperties, message, ackRequired):
    from ils.sfc.common.sessions import addControlPanelMessage 
    from ils.sfc.common.util import getDatabaseName
    from ils.sfc.gateway.util import escapeSingleQuotes, getTopChartRunId, sendUpdateControlPanelMsg
    escapedMessage = escapeSingleQuotes(message)
    chartRunId = getTopChartRunId(chartProperties)
    database = getDatabaseName(chartProperties)
    msgId = addControlPanelMessage(escapedMessage, ackRequired, chartRunId, database)
    sendUpdateControlPanelMsg(chartProperties)
    return msgId

def getCurrentMessageQueue(chartProperties):
    from ils.sfc.common.constants import MESSAGE_QUEUE
    from ils.sfc.common.util import getTopLevelProperties
    topScope = getTopLevelProperties(chartProperties)
    return topScope[MESSAGE_QUEUE]

def setCurrentMessageQueue(chartProperties, queue):
    from ils.sfc.common.constants import MESSAGE_QUEUE
    from ils.sfc.common.util import getTopLevelProperties
    topScope = getTopLevelProperties(chartProperties)
    topScope[MESSAGE_QUEUE] = queue

