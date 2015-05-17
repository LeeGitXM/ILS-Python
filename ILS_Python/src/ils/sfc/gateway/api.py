'''
Functions that are shared by custom and pre-defined steps

Created on Oct 30, 2014

@author: rforbes
'''

def s88DataExists(chartProperties, stepProperties, valuePath, location):
    from system.ils.sfc import s88DataExists
    return s88DataExists(chartProperties, stepProperties, valuePath, location)
  
def s88Get(chartProperties, stepProperties, valuePath, location):
    from system.ils.sfc import s88BasicGet
    return s88BasicGet(chartProperties, stepProperties, valuePath, location)

def getUnitsPath(valuePath):
    '''Get the units associated with a value; None if not found'''
    valueKeyIndex = valuePath.find(".value")
    if valueKeyIndex > 0:
        return valuePath[0 : valueKeyIndex] + ".units"
    else:
        raise Exception("no value field to get units for in " + valuePath)

def s88GetWithUnits(chartProperties, stepProperties, valuePath, location, returnUnitsName):
    from ils.common.units import Unit
    from system.ils.sfc import s88BasicGet
    from ils.sfc.common.util import getDatabaseName
    value = s88BasicGet(chartProperties, stepProperties, valuePath, location)
    unitsPath = getUnitsPath(valuePath)
    existingUnitsName = s88BasicGet(chartProperties, stepProperties, unitsPath, location)
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
    
def s88Set(chartProperties, stepProperties, valuePath, value, location):
    from system.ils.sfc import s88BasicSet
    s88BasicSet(chartProperties, stepProperties, valuePath, location, value)
     
def s88SetWithUnits(chartProperties, stepProperties, valuePath, value, location, newUnitsName):
    from system.ils.sfc import s88BasicSet
    s88BasicSet(chartProperties, stepProperties, valuePath, location, value)
    unitsPath = getUnitsPath(valuePath)
    s88BasicSet(chartProperties, stepProperties, unitsPath, location, newUnitsName)
        
def pauseChart(chartProperties):
    from system.sfc import pauseChart
    from ils.sfc.common.constants import INSTANCE_ID
    chartRunId = str(chartProperties[INSTANCE_ID])
    pauseChart(chartRunId)
    
def resumeChart(chartProperties):
    from system.sfc import resumeChart
    from ils.sfc.common.constants import INSTANCE_ID
    chartRunId = str(chartProperties[INSTANCE_ID])
    resumeChart(chartRunId)

def cancelChart(chartProperties):
    from system.sfc import cancelChart
    from ils.sfc.common.constants import INSTANCE_ID
    chartRunId = str(chartProperties[INSTANCE_ID])
    cancelChart(chartRunId)

def addControlPanelMessage(chartProperties, message, ackRequired):
    from ils.sfc.common.sessions import addControlPanelMessage 
    from ils.sfc.common.util import getDatabaseName
    from ils.sfc.gateway.util import escapeSingleQuotes, getChartRunId, sendUpdateControlPanelMsg
    escapedMessage = escapeSingleQuotes(message)
    chartRunId = getChartRunId(chartProperties)
    database = getDatabaseName(chartProperties)
    msgId = addControlPanelMessage(escapedMessage, ackRequired, chartRunId, database)
    sendUpdateControlPanelMsg(chartProperties)
    return msgId

def getCurrentMessageQueue(chartProperties):
    from ils.sfc.common.constants import MESSAGE_QUEUE
    from ils.sfc.common.util import getTopLevelProperties
    topScope = getTopLevelProperties(chartProperties)
    return topScope[MESSAGE_QUEUE]
