'''
Functions that are shared by custom and pre-defined steps

Created on Oct 30, 2014

@author: rforbes
'''

def s88GetFullTagPath(chartProperties, stepProperties, valuePath, location):
    '''Get the full path to the recipe data tag, taking isolation mode into account'''
    from ils.sfc.common.recipe import getRecipeDataTagPath, getBasicTagPath
    provider = getProviderName(chartProperties)
    basicTagPath = getBasicTagPath(chartProperties, stepProperties, valuePath, location)
    return getRecipeDataTagPath(provider, basicTagPath)

def s88DataExists(chartProperties, stepProperties, valuePath, location):
    '''Returns true if the the specified recipe data exists'''
    import system.tag
    fullTagPath = s88GetFullTagPath(chartProperties, stepProperties, valuePath, location)
    return system.tag.exists(fullTagPath)
  
def s88Get(chartProperties, stepProperties, valuePath, location):
    '''Get the given recipe data's value'''
    import system.tag
    fullTagPath = s88GetFullTagPath(chartProperties, stepProperties, valuePath, location)
    qv = system.tag.read(fullTagPath)
    return qv.value

def s88GetType(chartProperties, stepProperties, valuePath, location):
    '''Get the underlying recipe data type; return one of STRING, INT, FLOAT, or BOOLEAN from ils.sfc.common.constants'''
    fullTagPath = s88GetFullTagPath(chartProperties, stepProperties, valuePath, location)
    return getTagType(fullTagPath);

def s88Set(chartProperties, stepProperties, valuePath, value, location):
    '''Set the given recipe data's value'''
    import system.tag
    fullTagPath = s88GetFullTagPath(chartProperties, stepProperties, valuePath, location)
    system.tag.writeSynchronous(fullTagPath, value)

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

#
def writeLoggerMessage(chartScope, block, unit, message):
    '''Write a message to the system log file from an SFC.'''
    # The system logbook utility has not been implemented, when it is call it from here
    print "Simulating a write to the system logbook: %s" % (message)


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
    from ils.sfc.common.constants import MESSAGE_ID, MESSAGE, INSTANCE_ID, CLIENT_MSG_HANDLER
    from ils.sfc.common.util import createUniqueId
    from ils.sfc.gateway.util import getTopChartRunId
    from system.util import sendMessage
    project = getProject(chartProperties)
    messageId = createUniqueId()
    payload[INSTANCE_ID] = getTopChartRunId(chartProperties)
    payload[MESSAGE_ID] = messageId 
    payload[CLIENT_MSG_HANDLER] = handler
    # print 'sending message to client', project, handler, payload
    sendMessage(project, 'sfcMessage', payload, "C")
    return messageId

def getChartLogger(chartScope):
    '''Get the logger associated with this chart'''
    from ils.sfc.gateway.util import getFullChartPath
    from system.util import getLogger
    return getLogger(getFullChartPath(chartScope))

def getTagType(tagPath): 
    '''Get the value type of a tag; returns one of INT, FLOAT, BOOLEAN, STRING from ils.sfc.common.constants'''
    from system.tag import browseTags
    from ils.sfc.common.constants import INT, FLOAT, BOOLEAN, STRING
    from ils.sfc.common.util import splitPath
    # unfortunately browseTags() doesn't like a full path to the tag, so we
    # hack that by giving everything up to the last slash as a folder, then
    # use the tag name as a filter.
    prefix, suffix = splitPath(tagPath)  
    tagFilter = '*' + suffix  
    browseTags = browseTags(prefix, tagFilter)
    if len(browseTags) == 1:
        dataType = str(browseTags[0].dataType)
        # print 'dataType', dataType, 'prefix', prefix, 'filter', filter
        # Possible dataTypes: Int1, Int2, Int4, Int8, Float4, Float8, Boolean, String, and DateTime
        if dataType == 'Int1' or dataType == 'Int2' or dataType == 'Int4' or dataType == 'Int8':
            return INT
        elif dataType == 'Float4' or dataType == 'Float8':
            return FLOAT
        elif dataType == 'Boolean':
            return BOOLEAN
        else:
            return STRING
        
    else:
        return None

def parseValue(strValue, tagType):
    '''parse a value of the given type from a string'''
    from ils.sfc.common.constants import INT, FLOAT, BOOLEAN, STRING
    if tagType == INT:
        return int(strValue)
    elif tagType == FLOAT:
        return float(strValue)
    elif tagType == BOOLEAN:
        return bool(strValue)
    elif tagType == STRING:
        return strValue

def convertToTagType(fullTagPath, value):
    '''if necessary, convert a string value to match the tag type'''
    from ils.sfc.common.util import isString
    from ils.sfc.common.constants import STRING
    if isString(value):
        tagType = getTagType(fullTagPath)
        if tagType != STRING:            
            value = parseValue(value, tagType)
    return value

def getUnitsPath(valuePath):
    '''Get the key for the units associated with a recipe data value; None if not found'''
    valueKeyIndex = valuePath.find(".value")
    if valueKeyIndex > 0:
        return valuePath[0 : valueKeyIndex] + ".units"
    else:
        raise Exception("no value field to get units for in " + valuePath)

def readTag(chartScope, tagPath):
    '''Read an ordinary tag (ie not recipe data), substituting provider
    according to isolation mode setting'''
    from ils.sfc.common.util import substituteProvider
    import system.tag
    fullPath = substituteProvider(chartScope, tagPath)
    qval = system.tag.read(fullPath)
    return qval.value

