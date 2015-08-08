'''
Functions that are shared by custom and pre-defined steps

Created on Oct 30, 2014

@author: rforbes
'''

def s88DataExists(chartProperties, stepProperties, valuePath, location):
    '''Returns true if the the specified recipe data exists'''
    from system.ils.sfc import getRecipeDataTagPath
    from ils.sfc.common.recipe import recipeDataTagExists
    provider = getProviderName(chartProperties)
    location = location.lower()
    tagPath = getRecipeDataTagPath(chartProperties, stepProperties, location)
    return recipeDataTagExists(provider, tagPath);
  
def s88Get(chartProperties, stepProperties, valuePath, location):
    '''Get the given recipe data's value'''
    from system.ils.sfc import getRecipeDataTagPath
    from ils.sfc.common.recipe import getRecipeData
    provider = getProviderName(chartProperties)
    location = location.lower()
    #print 's88Get', valuePath, location
    stepPath = getRecipeDataTagPath(chartProperties, stepProperties, location)
    fullPath = stepPath + "/" + valuePath
    return getRecipeData(provider, fullPath);

def s88Set(chartProperties, stepProperties, valuePath, value, location):
    '''Set the given recipe data's value'''
    from system.ils.sfc import getRecipeDataTagPath
    from ils.sfc.common.recipe import setRecipeData
    provider = getProviderName(chartProperties)
    location = location.lower()
    #print 's88Set', valuePath, location
    stepPath = getRecipeDataTagPath(chartProperties, stepProperties, location)
    fullPath = stepPath + "/" + valuePath
    setRecipeData(provider, fullPath, value, True);
    
def getUnitsPath(valuePath):
    '''Get the key for the units associated with a recipe data value; None if not found'''
    valueKeyIndex = valuePath.find(".value")
    if valueKeyIndex > 0:
        return valuePath[0 : valueKeyIndex] + ".units"
    else:
        raise Exception("no value field to get units for in " + valuePath)

def s88GetWithUnits(chartProperties, stepProperties, valuePath, location, returnUnitsName):
    '''Like s88Get, but adds a conversion to the given units'''
    value = s88Get(chartProperties, stepProperties, valuePath, location)
    existingUnitsKey = getUnitsPath(valuePath)
    existingUnitsName = s88Get(chartProperties, stepProperties, existingUnitsKey, location)
    convertedValue = convertUnits(value, existingUnitsName, returnUnitsName)
    return convertedValue

def convertUnits(chartProperties, value, fromUnitName, toUnitName):    
    '''Convert a value from one unit to another'''
    from ils.common.units import Unit
    database = getDatabaseName(chartProperties)
    Unit.lazyInitialize(database)
    fromUnit = Unit.getUnit(fromUnitName)
    if(fromUnit == None):
        raise Exception("No unit found for " + fromUnitName)
    toUnit = Unit.getUnit(toUnitName)
    if(toUnit == None):
        raise Exception("No unit found for " + toUnitName)
    convertedValue = fromUnit.convertTo(toUnit, value)
    return convertedValue
    
def s88SetWithUnits(chartProperties, stepProperties, valuePath, value, location, valueUnitsName):
    '''Like s88Set, but adds a conversion from the given units'''
    existingUnitsKey = getUnitsPath(valuePath)
    existingUnitsName = s88Get(chartProperties, stepProperties, existingUnitsKey, location)
    convertedValue = convertUnits(chartProperties, value, valueUnitsName, existingUnitsName)
    s88Set(chartProperties, stepProperties, valuePath, convertedValue, location)
        
def pauseChart(chartProperties):
    '''pause the entire chart hierarchy'''
    from system.sfc import pauseChart
    from ils.sfc.gateway.util import getTopChartRunId
    chartRunId = getTopChartRunId(chartProperties)
    pauseChart(chartRunId)
    
def resumeChart(chartProperties):
    '''resume the entire chart hierarchy'''
    from system.sfc import resumeChart
    from ils.sfc.gateway.util import getTopChartRunId
    chartRunId = getTopChartRunId(chartProperties)
    resumeChart(chartRunId)

def cancelChart(chartProperties):
    '''cancel the entire chart hierarchy'''
    from system.sfc import cancelChart
    from ils.sfc.gateway.util import getTopChartRunId
    chartRunId = getTopChartRunId(chartProperties)
    cancelChart(chartRunId)

def addControlPanelMessage(chartProperties, message, ackRequired):
    '''display a message on the control panel'''
    from ils.sfc.common.sessions import addControlPanelMessage 
    from ils.sfc.gateway.util import escapeSingleQuotes, getTopChartRunId, sendUpdateControlPanelMsg
    escapedMessage = escapeSingleQuotes(message)
    chartRunId = getTopChartRunId(chartProperties)
    database = getDatabaseName(chartProperties)
    msgId = addControlPanelMessage(escapedMessage, ackRequired, chartRunId, database)
    sendUpdateControlPanelMsg(chartProperties)
    return msgId

def getCurrentMessageQueue(chartProperties):
    '''Get the currently used message queue'''
    from ils.sfc.common.constants import MESSAGE_QUEUE
    from ils.sfc.gateway.util import getTopLevelProperties
    topScope = getTopLevelProperties(chartProperties)
    print 'current queue', topScope[MESSAGE_QUEUE]
    return topScope[MESSAGE_QUEUE]

def setCurrentMessageQueue(chartProperties, queue):
    '''Set the currently used message queue'''
    from ils.sfc.common.constants import MESSAGE_QUEUE
    from ils.sfc.gateway.util import getTopLevelProperties
    topScope = getTopLevelProperties(chartProperties)
    topScope[MESSAGE_QUEUE] = queue

def sendOCAlert(chartProperties, stepProperties, post, topMessage, bottomMessage, buttonLabel, callback=None, callbackPayloadDictionary=None, timeoutEnabled=False, timeoutSeconds=0):
    '''Send an OC alert'''
    from ils.common.ocAlert import sendAlert
    project=getProject(chartProperties)
    sendAlert(project, post, topMessage, bottomMessage, buttonLabel, callback, callbackPayloadDictionary, timeoutEnabled, timeoutSeconds)

def postToQueue(chartScope, status, message, queueKey=None):
    '''Post a message to a queue from an SFC.
    If the queueKey is left blank then the current default queue for the unit procedure is used.
    Expected status are Info, Warning, or Error'''
    # If the queue was not specified then use the current default queue
    if queueKey == None:
        queueKey=getCurrentMessageQueue(chartScope)

    db=getDatabaseName(chartScope)
    from ils.queue.message import insert
    insert(queueKey, status, message, db)

def getProject(chartProperties):
    '''Get the project associated with the client side of this SFC (not the global project!)'''
    from ils.sfc.common.constants import PROJECT
    from ils.sfc.gateway.util import getTopLevelProperties
    return str(getTopLevelProperties(chartProperties)[PROJECT])

def getIsolationMode(chartProperties):
    '''Returns true if the chart is running in isolation mode'''
    from ils.sfc.common.constants import ISOLATION_MODE
    from ils.sfc.gateway.util import getTopLevelProperties
    topProperties = getTopLevelProperties(chartProperties)
    return topProperties[ISOLATION_MODE]

def getTopChartStartTime(chartProperties):
    '''Get the epoch time the chart was started in seconds (float value)'''
    from ils.sfc.gateway.util import getTopLevelProperties
    topProps = getTopLevelProperties(chartProperties)
    javaDate = topProps['startTime']
    return javaDate.getTime() * .001

def getDatabaseName(chartProperties):
    '''Get the name of the database this chart is using, taking isolation mode into account'''
    from system.ils.sfc import getDatabaseName
    isolationMode = getIsolationMode(chartProperties)
    return getDatabaseName(isolationMode)

def getProviderName(chartProperties):
    '''Get the name of the tag provider for this chart, taking isolation mode into account'''
    from system.ils.sfc import getProviderName, getIsolationMode
    return getProviderName(getIsolationMode(chartProperties))

#returns with square brackets
def getProvider(chartProperties):
    '''Like getProviderName(), but puts brackets around the provider name'''
    provider = getProviderName(chartProperties)
    return "[" + provider + "]"
   
def getTimeFactor(chartProperties):
    '''Get the factor by which all times should be multiplied (typically used to speed up tests)'''
    from system.ils.sfc import getTimeFactor
    isolationMode = getIsolationMode(chartProperties)
    return getTimeFactor(isolationMode)

def sendMessageToClient(chartProperties, handler, payload):
    '''Send a message to the client(s) of this chart'''
    # TODO: check returned list of recipients
    # TODO: restrict to a particular client session
    from ils.sfc.common.constants import MESSAGE_ID, MESSAGE, INSTANCE_ID
    from ils.sfc.common.util import createUniqueId
    from ils.sfc.gateway.util import getTopChartRunId
    from system.util import sendMessage
    project = getProject(chartProperties)
    messageId = createUniqueId()
    payload[INSTANCE_ID] = getTopChartRunId(chartProperties)
    payload[MESSAGE_ID] = messageId 
    # print 'sending message to client', project, handler, payload
    sendMessage(project, handler, payload, "C")
    return messageId

def getChartLogger(chartScope):
    '''Get the logger associated with this chart'''
    from ils.sfc.gateway.util import getFullChartPath
    from system.util import getLogger
    return getLogger(getFullChartPath(chartScope))
