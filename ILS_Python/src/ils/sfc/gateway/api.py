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
    from ils.sfc.common.util import isEmpty
    fullTagPath = s88GetFullTagPath(chartProperties, stepProperties, valuePath, location)
    qv = system.tag.read(fullTagPath)
    value = qv.value
    # we're not doing unit conversion here, but if there happens to be a time
    # unit then we want to do the isolation mode time scaling:
    if isValueKey(valuePath):
        unitName = getAssociatedUnitName(chartProperties, stepProperties, valuePath, location)
        if not isEmpty(unitName):
            unit = getUnitByName(chartProperties, unitName)
            value = scaleTimeForIsolationMode(chartProperties, value, unit)
    return value

def isValueKey(key):
    '''return true if the given key references the "value" attribute'''
    return key.endswith('.value') or key.endswith('.Value')
    
def s88GetType(chartProperties, stepProperties, valuePath, location):
    '''Get the underlying recipe data type; return one of STRING, INT, FLOAT, or BOOLEAN from ils.sfc.common.constants'''
    fullTagPath = s88GetFullTagPath(chartProperties, stepProperties, valuePath, location)
    return getTagType(fullTagPath);

def s88Set(chartProperties, stepProperties, valuePath, value, location):
    '''Set the given recipe data's value'''
    import system.tag
    fullTagPath = s88GetFullTagPath(chartProperties, stepProperties, valuePath, location)
    try:
        system.tag.writeSynchronous(fullTagPath, value)
        # print "ils.sfc.api.s88Set: Write to ",fullTagPath
    except:
        print "ils.sfc.api.s88Set: Failed to write to ",fullTagPath

def s88GetWithUnits(chartProperties, stepProperties, valuePath, location, returnUnitsName):
    '''Like s88Get, but adds a conversion to the given units'''
    value = s88Get(chartProperties, stepProperties, valuePath, location)
    existingUnitsName = getAssociatedUnitName(chartProperties, stepProperties, valuePath, location)
    convertedValue = convertUnits(chartProperties, value, existingUnitsName, returnUnitsName)
    return convertedValue

def getAssociatedUnitName(chartProperties, stepProperties, valuePath, location):
    '''given a value key, get associated unit name, or None if there is none.'''
    unitsKey = getUnitsPath(valuePath)
    if unitsKey != None:
        unitsName = s88Get(chartProperties, stepProperties, unitsKey, location)
        return unitsName
    else:
        return None

def getUnitByName(chartProperties, unitName):
    '''Given the name of a unit, get the Unit object for it.'''
    from ils.common.units import Unit
    database = getDatabaseName(chartProperties)
    Unit.lazyInitialize(database)
    unit = Unit.getUnit(unitName)
    if(unit == None):
        raise Exception("No unit found for " + unitName)
    return unit

def convertUnits(chartProperties, value, fromUnitName, toUnitName):    
    '''Convert a value from one unit to another'''
    fromUnit = getUnitByName(chartProperties, fromUnitName)
    toUnit = getUnitByName(chartProperties, toUnitName)
    convertedValue = fromUnit.convertTo(toUnit, value)
    convertedValue = scaleTimeForIsolationMode(chartProperties, convertedValue, fromUnit)
    return convertedValue

def scaleTimeForIsolationMode(chartProperties, value, unit):
    '''If the supplied unit is a time unit and we are in isolation mode,
       scale the value appropriately--otherwise, just return the value'''
    if unit.type == 'TIME' and getIsolationMode(chartProperties):
        timeFactor = getTimeFactor(chartProperties)
        logger = getChartLogger(chartProperties)
        logger.debug('multiplying time by isolation time factor %f' % timeFactor)
        value *= timeFactor
        logger.debug('the scaled time is %f' % value)
    return value

def s88SetWithUnits(chartProperties, stepProperties, valuePath, value, location, valueUnitsName):
    '''Like s88Set, but adds a conversion from the given units'''
    from ils.sfc.common.util import isEmpty
    existingUnitsKey = getUnitsPath(valuePath)
    existingUnitsName = s88Get(chartProperties, stepProperties, existingUnitsKey, location)
    if not isEmpty(existingUnitsName):
        convertedValue = convertUnits(chartProperties, value, valueUnitsName, existingUnitsName)
    else:
        logger = getChartLogger(chartProperties)
        logger.warn("No units in recipe data %s; no conversion done from %s" % (valuePath, valueUnitsName))
        convertedValue = value
    s88Set(chartProperties, stepProperties, valuePath, convertedValue, location)
        
def pauseChart(chartProperties):
    '''pause the entire chart hierarchy'''
    from ils.sfc.gateway.util import getTopChartRunId
    import system.sfc
    topChartRunId = getTopChartRunId(chartProperties)
    system.sfc.pauseChart(topChartRunId)
    
def resumeChart(chartProperties):
    '''resume the entire chart hierarchy'''
    from ils.sfc.gateway.util import getTopChartRunId
    import system.sfc
    topChartRunId = getTopChartRunId(chartProperties)
    system.sfc.resumeChart(topChartRunId)

def cancelChart(chartProperties):
    '''cancel the entire chart hierarchy'''
    from ils.sfc.gateway.util import getTopChartRunId
    import system.sfc
    topChartRunId = getTopChartRunId(chartProperties)
    system.sfc.cancelChart(topChartRunId)

def addControlPanelMessage(chartProperties, message, ackRequired):
    '''display a message on the control panel'''
    from ils.sfc.common.cpmessage import addControlPanelMessage 
    from ils.sfc.gateway.util import escapeSingleQuotes, getTopChartRunId
    escapedMessage = escapeSingleQuotes(message)
    chartRunId = getTopChartRunId(chartProperties)
    database = getDatabaseName(chartProperties)
    msgId = addControlPanelMessage(escapedMessage, ackRequired, chartRunId, database)
    #sendUpdateControlPanelMsg(chartProperties)
    return msgId

def getCurrentMessageQueue(chartProperties):
    '''Get the currently used message queue'''
    from ils.sfc.common.constants import MESSAGE_QUEUE
    from ils.sfc.gateway.util import getTopLevelProperties
    topScope = getTopLevelProperties(chartProperties)
    return topScope[MESSAGE_QUEUE]

def setCurrentMessageQueue(chartProperties, queue):
    '''Set the currently used message queue'''
    from ils.sfc.common.constants import MESSAGE_QUEUE
    from ils.sfc.gateway.util import getTopLevelProperties, getControlPanelId
    import system.db
    topScope = getTopLevelProperties(chartProperties)
    topScope[MESSAGE_QUEUE] = queue
    database = getDatabaseName(chartProperties)
    controlPanelId = getControlPanelId(chartProperties)
    system.db.runUpdateQuery("update SfcControlPanel set msgQueue = '%s' where controlPanelId = %d" % (queue, controlPanelId), database)

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
    '''Get timespamp for chart start'''
    from ils.sfc.gateway.util import getTopLevelProperties
    topProps = getTopLevelProperties(chartProperties)
    return topProps['startTime']

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

def sendMessageToClient(project, handler, payload, clientSessionId=None):
    '''Send a message to the client(s) of this chart'''
    from ils.sfc.common.constants import MESSAGE_ID, HANDLER
    from system.util import sendMessage
    from ils.sfc.common.util import createUniqueId
    messageId = createUniqueId()
    payload[MESSAGE_ID] = messageId 
    payload[HANDLER] = handler
    # print 'sending message to client', project, handler, payload
    if clientSessionId != None:
        sendMessage(project, 'sfcMessage', payload, "C", clientSessionId)
    else:
        sendMessage(project, 'sfcMessage', payload, "C")
    return messageId
def getChartLogger(chartScope):
    '''Get the logger associated with this chart'''
    from system.util import getLogger
    from ils.sfc.gateway.util import getChartPath
    return getLogger(getChartPath(chartScope))

def getTagType(tagPath): 
    '''Get the value type of a tag; returns one of INT, FLOAT, BOOLEAN, STRING from ils.sfc.common.constants'''
    from system.tag import browseTags
    from ils.sfc.common.constants import INT, FLOAT, BOOLEAN, STRING, DATE_TIME
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
        elif dataType == 'Date':
            return DATE_TIME
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
        return None

def readTag(chartScope, tagPath):
    '''Read an ordinary tag (ie not recipe data), substituting provider
    according to isolation mode setting'''
    from ils.sfc.common.util import substituteProvider
    import system.tag
    fullPath = substituteProvider(chartScope, tagPath)
    qval = system.tag.read(fullPath)
    return qval.value

