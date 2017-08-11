'''
Functions that are shared by custom and pre-defined steps

Created on Oct 30, 2014

@author: rforbes
'''
    
import system, string, time
from ils.sfc.recipeData.core import getTargetStep, getChartUUID, getStepUUID, splitKey
from ils.sfc.common.util import isEmpty, boolToBit, logExceptionCause
from ils.sfc.common.constants import MESSAGE_QUEUE, MESSAGE, NAME, CONTROL_PANEL_ID, ORIGINATOR, HANDLER, DATABASE, CONTROL_PANEL_NAME, \
    DELAY_UNIT_SECOND, DELAY_UNIT_MINUTE, DELAY_UNIT_HOUR, WINDOW_ID, TIMEOUT, TIMEOUT_UNIT, TIMEOUT_TIME, RESPONSE, TIMED_OUT
from ils.common.ocAlert import sendAlert
from ils.common.util import substituteProvider
from ils.sfc.client.windows.controlPanel import getControlPanelIdForChartRunId
NEWLINE = '\n\r'
logger=system.util.getLogger("com.ils.sfc.gateway.api")


'''
This is called from the gateway by a running chart, it does not have a window handle or rootContainer.  In fact there may not be 
a window.  Display a message on the control panel
'''
def addControlPanelMessage(chartProperties, message, priority, ackRequired):
    escapedMessage = escapeSingleQuotes(message)
    chartRunId = getTopChartRunId(chartProperties)
    database = getDatabaseName(chartProperties)
    controlPanelId=getControlPanelIdForChartRunId(chartRunId, database)
    
    if controlPanelId == None:
        msgId = None
        print "Unable to insert a control panel message because the control panel was not found, hopefully because we are in test mode."
    else:
        SQL = "insert into SfcControlPanelMessage (controlPanelId, message, priority, createTime, ackRequired) "\
           "values (%s,'%s','%s',getdate(),%d)" % (str(controlPanelId), escapedMessage, priority, boolToBit(ackRequired) )
        msgId = system.db.runUpdateQuery(SQL, database, getKey=True)

    return msgId


def cancelChart(chartProperties):
    '''cancel the entire chart hierarchy'''
    topChartRunId = getTopChartRunId(chartProperties)
    logger.infof("Cancelling chart with id: %s", str(topChartRunId))
    system.sfc.cancelChart(topChartRunId)

def checkForResponse(chartScope, stepScope, stepProperties):
    '''Common code for processing responses from client. Returns true if work was
       completed, i.e. either response was received or timed out'''
    timeoutTime = stepScope[TIMEOUT_TIME]
    stepScope[TIMED_OUT] = False

    # PETE - not sure who uses this or what this did - I don't think we need this with the new style of windows.
#    responsePayload = getResponse(windowId)
    responsePayload = {}
    if responsePayload != None:
        response = responsePayload[RESPONSE]
    elif timeoutTime != None and time.time() > timeoutTime:
        stepScope[TIMED_OUT] = True
        response = TIMED_OUT        
    else:
        response = None
    return response

def compareValueToTarget(pv, target, tolerance, limitType, toleranceType, logger):
    ''' This is is mainly by PV monitoring but is pretty generic '''

    logger.trace("Comparing value to target - PV: %s, Target %s, Tolerance: %s, Limit-Type: %s, Tolerance: %s" % (str(pv), str(target), str(tolerance), limitType, toleranceType))

    txt = ""
    valueOk = True
    
    if target == 0.0:
        toleranceType = "Abs"
    
    #Depending on the limit type we may not use both the high and low limits, but we can always calculate them both
    if toleranceType == "Pct":
        highLimit = target + abs(tolerance * target) / 100.0;
        lowLimit = target - abs(tolerance * target) / 100.0;
    else:
        highLimit = target + tolerance;
        lowLimit = target - tolerance;

    logger.tracef("    PV=%f, Target=%f, High Limit=%f, Low Limit=%f", pv, target, highLimit, lowLimit)

    if limitType == "High/Low":
        if pv > highLimit or pv < lowLimit:
            valueOk = False
            txt = "%s is outside the limits of %s to %s" % (str(pv), str(lowLimit), str(highLimit))
    elif limitType == "High":    
        if pv < lowLimit:
            valueOk = False
            txt = "%s is below the low limit of %s (Target - Tolerance)" % (str(pv), str(lowLimit), str(highLimit))
    elif limitType == "Low":
        if pv > highLimit:
            valueOk = False
            txt = "%s is above the high limit of %s (Target + Tolerance)" % (str(pv), str(highLimit))
    else:
        return False, "Illegal limit type: <%s>" % (limitType)

    logger.trace("Returning %s-%s" % (str(valueOk), txt))
    
    return valueOk, txt

def copyRowToDict(dbRows, rowNum, pdict, create):
    columnCount = dbRows.getColumnCount()
    for colNum in range(columnCount):
        colName = dbRows.getColumnName(colNum)
        if colName in pdict.keys() or create:
            value = dbRows.getValueAt(rowNum, colNum)
            pdict[colName] = value

def createFilepath(chartScope, stepProperties, includeExtension):
    '''Create a filepath from dir/file/suffix in step properties'''
    from ils.sfc.common.constants import DIRECTORY, FILENAME, EXTENSION, TIMESTAMP
    import time

    directory = getStepProperty(stepProperties, DIRECTORY) 
    fileName = getStepProperty(stepProperties, FILENAME) 
    if includeExtension:
        extension = getStepProperty(stepProperties, EXTENSION) 
    else:
        extension = ''
    # lookup the directory if it is a variab,e
    if directory.startswith('['):
        directory = chartScope.get(directory, None)
        if directory == None:
            print "ERROR: directory key " + directory + " not found"
    doTimestamp = getStepProperty(stepProperties, TIMESTAMP) 
    if doTimestamp == None:
        doTimestamp = False
    # create timestamp if requested
    if doTimestamp: 
        timestamp = "-" + time.strftime("%Y%m%d%H%M")
    else:
        timestamp = ""
    filepath = directory + '/' + fileName + timestamp + extension
    return filepath

def createWindowRecord(chartRunId, controlPanelId, window, buttonLabel, position, scale, title, database):
    print "********************************************************************************"
    print "***** THIS IS AN OBSOLETE API PLEASE USE registerWindowWithControlPanel() ******"
    print "********************************************************************************"
    registerWindowWithControlPanel(chartRunId, controlPanelId, window, buttonLabel, position, scale, title, database)

def createSaveDataRecord(windowId, dataText, filepath, computer, printFile, showPrintDialog, viewFile, database):
    print 'windowId', windowId, 'dataText', dataText, 'filepath', filepath, 'computer', computer, 'printFile', printFile, 'showPrintDialog', showPrintDialog, 'viewFile', viewFile
    system.db.runUpdateQuery("insert into SfcSaveData (windowId, text, filePath, computer, printText, showPrintDialog, viewText) values ('%s', '%s', '%s', '%s', %d, %d, %d)" % (windowId, dataText, filepath, computer, printFile, showPrintDialog, viewFile), database)

def dbStringForString(strValue):
    '''return a string representation of the given string suitable for a nullable SQL varchar column'''
    if strValue != None:
        return "'" + strValue + "'"
    else:
        return 'null'  
    
def dbStringForFloat(numberValue):
    '''return a string representation of the given number suitable for a nullable SQL float column'''
    if numberValue != None:
        return str(numberValue)
    else:
        return 'null'

def deleteAndSendClose(project, windowId, database):
    '''Delete the common window record and message the client to close the window'''
    system.db.runUpdateQuery("delete from SfcWindow where windowId = '%s'" % (windowId), database)
    payload = {WINDOW_ID: windowId, HANDLER: 'sfcCloseWindow', DATABASE: database}
    system.util.sendMessage(project, 'sfcMessage', payload, scope="C")
    
def dictToString(aDict):
    '''
    print a java dictionary into a nice, readable indented form
    returns a string containing the pretty-printed representation
    '''
    import StringIO
    out = StringIO.StringIO()
    for key, value in aDict.items():
        out.write(key)
        out.write(': ')
        out.write(value)
        out.write(NEWLINE)
    result = out.getvalue()
    out.close()
    return result

def dumpProperties(properties):
    for k in properties.keys():
        print k
        
def escapeSingleQuotes(msg):
    return msg.replace("'", "''")

def getChartLogger(chartScope):
    '''Get the logger associated with this chart'''
    pypath = getChartPath(chartScope).replace("/",".")
    return system.util.getLogger(pypath)

def getChartPath(chartProperties):
    return chartProperties.chartPath 

def getControlPanelId(chartScope):
    topScope = getTopLevelProperties(chartScope)
    controlPanelId=topScope.get(CONTROL_PANEL_ID,None)
    #TODO This is a hack to facilitate testing from the designer - need to do something better
    if controlPanelId == None:
        controlPanelId = 6
    return controlPanelId

def getControlPanelName(chartScope):
    topScope = getTopLevelProperties(chartScope)
    controlPanelName=topScope.get(CONTROL_PANEL_NAME,None)
    #TODO This is a hack to facilitate testing from the designer - need to do something better
    if controlPanelName == None:
        controlPanelName = "PolymerizeEpdm"
    return controlPanelName

def getCurrentMessageQueue(chartProperties):
    '''Get the currently used message queue'''
    topScope = getTopLevelProperties(chartProperties)
    return topScope[MESSAGE_QUEUE]

def getDatabaseName(chartProperties):
    '''Get the name of the database this chart is using, taking isolation mode into account'''
    isolationMode = getIsolationMode(chartProperties)
    
    ''' Leave this include here to avoid name clash '''
    from system.ils.sfc import getDatabaseName
    return getDatabaseName(isolationMode)  

def getDelaySeconds(delay, delayUnit):
    '''get the delay time and convert to seconds'''
    if delayUnit == DELAY_UNIT_SECOND:
        delaySeconds = delay
    elif delayUnit == DELAY_UNIT_MINUTE:
        delaySeconds = delay * 60
    elif delayUnit == DELAY_UNIT_HOUR:
        delaySeconds = delay * 3600
    else:
        print "*** Unexpected delay units: <%s> ***" % (str(delayUnit))
        delaySeconds = delay

    return delaySeconds

def getHistoryProviderName(chartProperties):
    #TODO Figure this out
    return "XOMhistory"

def getIsolationMode(chartProperties):
    '''Returns true if the chart is running in isolation mode'''
    from ils.sfc.common.constants import ISOLATION_MODE
    topProperties = getTopLevelProperties(chartProperties)
    return topProperties[ISOLATION_MODE]

def getOriginator(chartScope):
    topScope = getTopLevelProperties(chartScope)
    return topScope.get(ORIGINATOR,None)

def getPostForControlPanelName(controlPanelName, db=""):
    SQL = "select Post from SfcControlPanel CP, TkPost P where CP.PostId = P.PostId and ControlPanelName = '%s'" % (controlPanelName)
    postId = system.db.runScalarQuery(SQL, db)
    return postId

def getProject(chartProperties):
    '''Get the project associated with the client side of this SFC (not the global project!)'''
    from ils.sfc.common.constants import PROJECT
    return str(getTopLevelProperties(chartProperties)[PROJECT])

def getProviderName(chartProperties):
    '''Get the name of the tag provider for this chart, taking isolation mode into account'''
    from system.ils.sfc import getProviderName, getIsolationMode
    return getProviderName(getIsolationMode(chartProperties))

#returns with square brackets
def getProvider(chartProperties):
    '''Like getProviderName(), but puts brackets around the provider name'''
    provider = getProviderName(chartProperties)
    return "[" + provider + "]"
  
def getSessionId(chartProperties):
    '''Get the run id of the chart at the TOP enclosing level'''
    from ils.sfc.common.constants import SESSION_ID
    return str(getTopLevelProperties(chartProperties)[SESSION_ID])        

def getStepId(stepProperties):
    # need to translate the UUID to a string:
    from ils.sfc.common.constants import ID
    if stepProperties != None:
        return str(getStepProperty(stepProperties, ID))
    else:
        return None

def getStepProperty(stepProperties, pname):
    for prop in stepProperties.getProperties():
        if prop.getName() == pname:
            return stepProperties.getOrDefault(prop)
    return None

def getTimeoutTime(chartScope, stepProperties):
    '''For steps that time out, get the time in epoch seconds when the timeout expires.
       Take the isolation mode time factor into account'''

    timeFactor = getTimeFactor(chartScope)
    timeoutTime = None
    timeout = getStepProperty(stepProperties, TIMEOUT)
    if timeout != None and timeout > 0.:
        timeoutUnit = getStepProperty(stepProperties, TIMEOUT_UNIT)
        timeoutSeconds = getDelaySeconds(timeout, timeoutUnit)
        timeoutSeconds *= timeFactor
        timeoutTime = time.time() + timeoutSeconds
    return timeoutTime
   
def getTimeFactor(chartProperties):
    '''Get the factor by which all times should be multiplied (typically used to speed up tests)'''
    from system.ils.sfc import getTimeFactor
    isolationMode = getIsolationMode(chartProperties)
    return getTimeFactor(isolationMode)

def getTopChartRunId(chartProperties):
    '''Get the run id of the chart at the TOP enclosing level'''
    from ils.sfc.common.constants import INSTANCE_ID
    return str(getTopLevelProperties(chartProperties)[INSTANCE_ID])

def getTopChartStartTime(chartProperties):
    '''Get timespamp for chart start'''
    topProps = getTopLevelProperties(chartProperties)
    return topProps['startTime']

def getTopLevelProperties(chartProperties):
#    print "------------------"
#    print "In getTopLevelProperties..."
    from ils.sfc.common.constants import PARENT
#    print "Checking: ", chartProperties.get(PARENT, None)
#    print "   level: ", chartProperties.get("s88Level", None)
    while chartProperties.get(PARENT, None) != None:
#        print chartProperties
        chartProperties = chartProperties.get(PARENT)
#        print "Checking: ", chartProperties.get(PARENT, None)
#        print "   level: ", chartProperties.get("s88Level", None)
#    print " --- returning --- "
    return chartProperties

def getWithPath(properties, key):
    '''
    Get a value using a potentially compound key
    '''

def handleUnexpectedGatewayError(chartScope, stepProperties, msg, logger=None):
    '''
    Report an unexpected error so that it is visible to the operator--
    e.g. put in a message queue. Then cancel the chart.
    '''  
    notifyGatewayError(chartScope, stepProperties, msg, logger)
    
    if logger <> None:
        logger.error("Canceling the chart due to an error.")
    else:
        print "Canceling the chart due to an error."
    cancelChart(chartScope)

def notifyGatewayError(chartScope, stepProperties, msg, logger=None):
    '''  Report an unexpected error so that it is visible to the operator.  '''
    fullMsg, tracebackMsg, javaCauseMsg = logExceptionCause(msg, logger)
    chartPath = chartScope.get("chartPath", "")
    stepName = getStepProperty(stepProperties, NAME)
    payloadMsg = "%s\nChart path: %s\nStep Name: %s\n\nException details:%s\n%s\n%s" % (msg, chartPath, stepName, fullMsg, tracebackMsg, javaCauseMsg)
    payload = dict()
    payload[MESSAGE] = payloadMsg
    sendMessageToClient(chartScope, 'sfcUnexpectedError', payload)
    
def hasStepProperty(stepProperties, pname):
    # Why isn't there a dictionary so we don't have to loop ?!
    for prop in stepProperties.getProperties():
        if prop.getName() == pname:
            return True
    return False

def logStepDeactivated(chartScope, stepProperties):
    chartLogger = getChartLogger(chartScope)
    chartPath = getChartPath(chartScope)
    stepName = getStepProperty(stepProperties, NAME)
    chartLogger.info("Step %s in %s deactivated before completing" % (stepName, chartPath))

def pauseChart(chartProperties):
    '''  pause the entire chart hierarchy  '''
    topChartRunId = getTopChartRunId(chartProperties)
    system.sfc.pauseChart(topChartRunId)

def postToQueue(chartScope, status, message, queueKey=None):
    '''  Post a message to a queue from an SFC.
    If the queueKey is left blank then the current default queue for the unit procedure is used.
    Expected status are Info, Warning, or Error.  If the queue was not specified then use the current default queue.  '''
    if queueKey == None:
        queueKey=getCurrentMessageQueue(chartScope)

    db=getDatabaseName(chartScope)
    from ils.queue.message import insert as insertQueueMessage
    insertQueueMessage(queueKey, status, message, db)

def printSpace(level, out):
    for i in range(level):
        out.write('   '),

def readTag(chartScope, tagPath):
    '''  Read a tag substituting provider according to isolation mode.  '''
    provider = getProviderName(chartScope)
    fullPath = substituteProvider(tagPath, provider)
    qv = system.tag.read(fullPath)
    return qv.value

def registerWindowWithControlPanel(chartRunId, controlPanelId, windowPath, buttonLabel, position, scale, title, database):
    sql = "Insert into SfcWindow (chartRunId, controlPanelId, windowPath, buttonLabel, position, scale, title) "\
        "values (?, ?, ?, ?, ?, ?, ?)"
    windowId = system.db.runPrepUpdate(sql, [chartRunId, controlPanelId, windowPath, buttonLabel, position, scale, title], database, getkey=True)
    return windowId

def resumeChart(chartProperties):
    '''resume the entire chart hierarchy'''
    topChartRunId = getTopChartRunId(chartProperties)
    system.sfc.resumeChart(topChartRunId)

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

def sendOCAlert(chartProperties, stepProperties, post, topMessage, bottomMessage, buttonLabel, callback=None, callbackPayloadDictionary=None, timeoutEnabled=False, timeoutSeconds=0):
    '''Send an OC alert'''
    project=getProject(chartProperties)
    sendAlert(project, post, topMessage, bottomMessage, buttonLabel, callback, callbackPayloadDictionary, timeoutEnabled, timeoutSeconds)

def sendMessageToClient(chartScope, messageHandler, payload):
    '''Send a message to the client(s) of this chart'''
    print "Sending a message..."
    logger.trace("Sending a %s SFC message... " % (str(messageHandler)))
    controlPanelId = getControlPanelId(chartScope)
    controlPanelName = getControlPanelName(chartScope)
    project = getProject(chartScope)
    db = getDatabaseName(chartScope)
    post = getPostForControlPanelName(controlPanelName, db)
    originator = getOriginator(chartScope)
    payload[HANDLER] = messageHandler
    payload[DATABASE] = db
    payload[CONTROL_PANEL_ID] = controlPanelId
    payload[CONTROL_PANEL_NAME] = controlPanelName
    payload[ORIGINATOR] = originator
    logger.tracef("   payload: %s" , str(payload))

    from ils.common.notification import notify
    notify(project, 'sfcMessage', payload, post, db)

def setCurrentMessageQueue(chartProperties, queue):
    '''Set the currently used message queue'''
    topScope = getTopLevelProperties(chartProperties)
    topScope[MESSAGE_QUEUE] = queue
    database = getDatabaseName(chartProperties)
    controlPanelId = getControlPanelId(chartProperties)
    system.db.runUpdateQuery("update SfcControlPanel set msgQueue = '%s' where controlPanelId = %d" % (queue, controlPanelId), database)

def writeLoggerMessage(chartScope, post, message):
    '''Write a message to the system log file from an SFC.'''
    db = getDatabaseName(chartScope)
    from ils.common.operatorLogbook import insertForPost
    insertForPost(post, message, db)

def standardDeviation(dataset, column):
    '''calculate the standard deviation of the given column of the dataset'''
    import org.apache.commons.math3.stat.descriptive.moment.StandardDeviation as StandardDeviation
    import jarray
    stdDev = StandardDeviation()
    pvalues = []
    for i in range(dataset.rowCount):
        value = dataset.getValueAt(i, column)
        pvalues.append(value)
    jvalues = jarray.array(pvalues, 'd')
    return stdDev.evaluate(jvalues)

def transferStepPropertiesToMessage(stepProperties, payload):
    for prop in stepProperties.getProperties():
        # omit the associated-data as the JSONObject causes a serialization error
        if not (prop.getName() == 'associated-data'):
            payload[prop.getName()] = stepProperties.getOrDefault(prop)

def writeObj(obj, level, aFile):
    if hasattr(obj, 'keys'):
        aFile.write(NEWLINE) 
        for key in obj:
            writeSpace(level, file)
            aFile.write(str(key))
            writeObj(obj[key], level + 1, file)
    else:
        #printSpace(level)
        aFile.write( ': ')
        aFile.write(str(obj))
        aFile.write(NEWLINE)

def writeSpace(level, aFile):
    for i in range(level):
        aFile.write('   '),
