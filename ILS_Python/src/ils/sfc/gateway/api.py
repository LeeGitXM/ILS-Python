'''
Functions that are shared by custom and pre-defined steps

Created on Oct 30, 2014

@author: rforbes
'''
    
import system, time, string
from ils.io.util import readTag
from ils.sfc.common.util import boolToBit, logExceptionCause, getChartStatus
from ils.sfc.common.constants import MESSAGE_QUEUE, MESSAGE, NAME, CONTROL_PANEL_ID, ORIGINATOR, HANDLER, DATABASE, CONTROL_PANEL_NAME, \
    DELAY_UNIT_SECOND, DELAY_UNIT_MINUTE, DELAY_UNIT_HOUR, WINDOW_ID, TIMEOUT, TIMEOUT_UNIT, TIMEOUT_TIME, RESPONSE, TIMED_OUT, MAX_CONTROL_PANEL_MESSAGE_LENGTH
from ils.common.ocAlert import sendAlert
from ils.common.util import substituteProvider, escapeSqlQuotes
from ils.queue.constants import QUEUE_ERROR
from ils.sfc.recipeData.api import substituteScopeReferences

SFC_MESSAGE_QUEUE = 'SFC-Message-Queue'
NEWLINE = '\n\r'

from ils.log.LogRecorder import LogRecorder
logger = LogRecorder(__name__)

def abortHandler(chartScope, msg):
    '''
    This API can be used in the OnAbort handler of a chart.
    This will cancel the charts from the bottom up of all charts running under the unit procedure.
    Note: This will cause the CANCEL handlers to be called, not the ABORT handlers.
    This should only be called from an SFC because I hope to be able to figure out how to get the stack trace and include it in the
    client notification. 
    
    This cancels the top chart in an aynchronous thread, with a short wait, to allow the chart on which the error occurred to finish before the cancel command 
    propagates down the tree of active charts in order to avoid a race condition with the abort and cancel states.  The addition of this wait may allow the step 
    following the encapsulation that called the chart with the error to begin to run, but the wait is short and hopefully no damage will be done.   If the wait is not 
    long enough then the charts will ghet stuck in the CANCELLING state forever.
    
    Additionally, we hope to address the shortcoming of the error handling with IA in the 2020 bootcamp.  
    '''
    
    stepProperties = None
    try:
        msg = msg + NEWLINE + chartScope.abortCause
    except:
        try:
            ''' This treats the error as a JythonExecException, but doesn't always work. '''
            abortCause = chartScope.abortCause.getLocalizedMessage()
        except:
            abortCause = "Unknown Error"
            
    msg = msg + NEWLINE + abortCause
    notifyGatewayError(chartScope, stepProperties, msg, logger)
    
    if logger <> None:
        logger.error("Canceling the chart due to an error.")
    else:
        print "*****************************************"
        print "Canceling the chart due to an error."
        print "*****************************************"
    
    '''cancel the entire chart hierarchy'''
    topChartRunId = getTopChartRunId(chartScope)
    chartPath = getChartPath(chartScope)
    
    print "The chart path of the aborting chart is", chartPath
    logger.infof("Cancelling chart with id: %s", str(topChartRunId))
    
    def cancelWork(topChartRunId=topChartRunId, chartPath=chartPath):
        logger.infof("In cancelWork(), an asynchronous thread...")
        
        i = 0
        running = chartIsRunning(chartPath)
        while running:
            logger.tracef("...sleeping...")
            time.sleep(0.1)
            running = chartIsRunning(chartPath)
    
            i = i + 1
            if i > 100:
                running = False
        
        time.sleep(0.1)
        logger.tracef("...the chart is done aborting, i = %d", i)
        logger.tracef("...cancelling...")
        system.sfc.cancelChart(topChartRunId)
        logger.tracef("...the asynchronous thread is complete!")
    
    system.util.invokeAsynchronous(cancelWork)
    
def chartIsRunning(chartPath):
    running = True
    ds = system.sfc.getRunningCharts(chartPath)
    if ds.getRowCount() > 0:
        chartState = ds.getValueAt(0, "chartState")
        if str(chartState) == "Aborted":
            running = False
        logger.tracef("The chart state is: %s", str(chartState)) 
    else:
        running = False
        
    return running
    

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
    if stepProperties == None:
        stepName = "Unknown"
    else:
        stepName = getStepProperty(stepProperties, NAME)
    payloadMsg = "%s\nChart path: %s\nStep Name: %s\n\nException details:%s\n%s\n%s" % (msg, chartPath, stepName, fullMsg, tracebackMsg, javaCauseMsg)
    payload = dict()
    payload[MESSAGE] = payloadMsg
    sendMessageToClient(chartScope, 'sfcUnexpectedError', payload)
    
def handleExpectedGatewayError(chartScope, stepName, msg, logger=None):
    '''
    Report an expected error so that it is visible to the operator--
    e.g. put in a message queue. Then cancel the chart.
    '''

    chartPath = chartScope.get("chartPath", "")
    payloadMsg = "%s\nChart: %s\nStep: %s" % (msg, chartPath, stepName)
    payload = dict()
    payload[MESSAGE] = payloadMsg

    sendMessageToClient(chartScope, 'sfcUnexpectedError', payload)
    
    if logger <> None:
        logger.error("Canceling the chart due to an error.")
    else:
        print "Canceling the chart due to an error."

    cancelChart(chartScope)    


'''
This is used to run a chart from the stop, cancel, or abort end handlers.
The third argument can optionally be used to call one chart from multiple handlers, sort o like the old toolkit.
'''
def endHandlerRunner(chartPath, chartScope, handler=""):
    logger.infof("In %s.endHandlerRunner(), starting %s", __name__, chartPath)
    
    if handler == "":
        payload = {"callerChartScope": chartScope}
    else:
        payload = {"callerChartScope": chartScope, "handler": handler}
        
    sfcId = system.sfc.startChart(chartPath, payload)
    
    logger.tracef("The calling chart scope is: %s", str(chartScope))
    logger.tracef("...started a chart with run Id: %s", sfcId)

    '''
    Wait until the chart completes.
    '''
    time.sleep(0.5)
    while getChartStatus(sfcId) == "Running":
        logger.tracef("The chart status is %s", getChartStatus(sfcId))
        time.sleep(0.5)
    
    logger.tracef("The chart is done!")
    
def endHandlerSetup(chart):
    logger.infof("In %s.endHandlerSetup()...", __name__)
    
    logger.tracef("The chart scope is: %s", str(chart))
    logger.tracef("The caller's chart scope is: %s", str(chart.callerChartScope))
    
    '''
    Get a couple of important properties out of the calling scope and overwrite the current chart scope
    '''
    chart.parent  = chart.callerChartScope.parent
    enclosingStep = chart.callerChartScope.get("enclosingStep", "None")
    if enclosingStep <> "None":
        chart.enclosingStep = enclosingStep
    
    logger.tracef("The NEW chart scope is: %s", str(chart))


'''
This is called from the gateway by a running chart, it does not have a window handle or rootContainer.  In fact there may not be 
a window.  Display a message on the control panel
'''
def addControlPanelMessage(chartProperties, stepScope, message, priority, ackRequired):    
    logger.tracef("The untranslated message is <%s>...", message)
    message = substituteScopeReferences(chartProperties, stepScope, message)
    message = escapeSqlQuotes(message)
    message = message[:MAX_CONTROL_PANEL_MESSAGE_LENGTH]
    
    logger.tracef("...the translated message is <%s>", message)
    
    database = getDatabaseName(chartProperties)
    controlPanelId = getControlPanelId(chartProperties)
#    controlPanelId=getControlPanelIdForChartRunId(chartRunId, database)
    
    if controlPanelId == None:
        msgId = None
        print "Unable to insert a control panel message because the control panel was not found, hopefully because we are in test mode."
    else:
        SQL = "insert into SfcControlPanelMessage (controlPanelId, message, priority, createTime, ackRequired) "\
           "values (%s,'%s','%s',getdate(),%d)" % (str(controlPanelId), message, priority, boolToBit(ackRequired) )
        msgId = system.db.runUpdateQuery(SQL, database, getKey=True)

    return msgId


def cancelChart(chartProperties):
    '''cancel the entire chart hierarchy'''
    topChartRunId = getTopChartRunId(chartProperties)
    logger.infof("Cancelling chart with id: %s", str(topChartRunId))
    system.sfc.cancelChart(topChartRunId)
    raise SystemExit

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
            txt = "%s is below the low limit of %s (Target - Tolerance)" % (str(pv), str(lowLimit))
    elif limitType == "Low":
        if pv > highLimit:
            valueOk = False
            txt = "%s is above the high limit of %s (Target + Tolerance)" % (str(pv), str(highLimit))
    else:
        return False, "Illegal limit type: <%s>" % (limitType)

    logger.trace("Returning %s because %s" % (str(valueOk), txt))
    
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
    filename = getStepProperty(stepProperties, FILENAME) 
    
    ''' Both the directory and filename are required '''
    if directory == "" or filename == "":
        return "", ""
    
    if includeExtension:
        extension = getStepProperty(stepProperties, EXTENSION) 
    else:
        if filename.find(".") > -1:
            extension = filename[filename.find("."):]
            filename = filename[:filename.find(".")]
        else:
            extension = ''
    
    logger.tracef("Filename:  <%s>", filename)
    logger.tracef("Extension: <%s>", extension)
    
    # lookup the directory if it is a variab,e
    if directory.startswith('['):
        directory = chartScope.get(directory, None)
        if directory == None:
            print "ERROR: directory key " + directory + " not found"
            
    doTimestamp = getStepProperty(stepProperties, TIMESTAMP) 
    logger.tracef("Creating a filepath, doTimestamp is: %s", str(doTimestamp))
    if doTimestamp == None:
        doTimestamp = False
    
    # create timestamp if requested
    if doTimestamp: 
        timestamp = "-" + time.strftime("%Y%m%d%H%M")
    else:
        timestamp = ""
    
    filename = filename + timestamp + extension
    
    if directory[len(directory)-1] in ["/", "\\"]:
        filePath = directory + filename
    else:
        filePath = directory + "/" + filename

    return directory, filename, filePath

def createWindowRecord(chartRunId, controlPanelId, window, buttonLabel, position, scale, title, database):
    print "********************************************************************************"
    print "***** THIS IS AN OBSOLETE API PLEASE USE registerWindowWithControlPanel() ******"
    print "********************************************************************************"
    registerWindowWithControlPanel(chartRunId, controlPanelId, window, buttonLabel, position, scale, title, database)

def createSaveDataRecord(windowId, textData, binaryData, filepath, fileLocation, printFile, showPrintDialog, viewFile, database, extension="txt"):
    print 'windowId: ', windowId 
    print 'filepath: ', filepath
    print 'fileLocation:', fileLocation
    print 'printFile: ', printFile
    print 'showPrintDialog: ', showPrintDialog
    print 'viewFile: ', viewFile
    
    if string.upper(fileLocation) == "CLIENT":
            SQL = "insert into SfcSaveData (windowId, filePath, fileLocation, printText, showPrintDialog, viewText) values (?, ?, ?, ?, ?, ?)"
            print SQL
            system.db.runPrepUpdate(SQL, [windowId, filepath, fileLocation, printFile, showPrintDialog, viewFile], database)
    else:
        if string.upper(extension) == "PDF":
            SQL = "insert into SfcSaveData (windowId, binaryData, filePath, fileLocation, printText, showPrintDialog, viewText) values (?, ?, ?, ?, ?, ?, ?)"
            print SQL
            system.db.runPrepUpdate(SQL, [windowId, binaryData, filepath, fileLocation, printFile, showPrintDialog, viewFile], database)
        else:
            SQL = "insert into SfcSaveData (windowId, textData, filePath, fileLocation, printText, showPrintDialog, viewText) values (?, ?, ?, ?, ?, ?, ?)"
            print SQL
            system.db.runPrepUpdate(SQL, [windowId, textData, filepath, fileLocation, printFile, showPrintDialog, viewFile], database)

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

def getChartLogger(chartScope):
    '''Get the logger associated with this chart'''
    pypath = getChartPath(chartScope).replace("/",".")
    return LogRecorder(pypath)

def getChartPath(chartProperties):
    return chartProperties.chartPath 

def getControlPanelId(chartScope):
    topScope = getTopLevelProperties(chartScope)
    controlPanelId=topScope.get(CONTROL_PANEL_ID,None)
    
    if controlPanelId == None:
        database = getDatabaseName(chartScope)
        SQL = "select controlPanelId from SfcControlPanel where ControlPanelName = 'Test'"
        controlPanelId = system.db.runScalarQuery(SQL, database)
        if controlPanelId == None:
            print "Error: Control panel named 'Test' not found in the SfcControlPanel table"
            controlPanelId = -1
    return controlPanelId

def getControlPanelName(chartScope):
    topScope = getTopLevelProperties(chartScope)
    controlPanelName=topScope.get(CONTROL_PANEL_NAME, None)
    
    if controlPanelName == None:
        controlPanelId = getControlPanelId(chartScope)
        database = getDatabaseName(chartScope)
        SQL = "select controlPanelName from SfcControlPanel where ControlPanelId = %s" % (str(controlPanelId))
        controlPanelName = system.db.runScalarQuery(SQL, database)

    return controlPanelName

def getCurrentMessageQueue(chartProperties):
    '''Get the currently used message queue'''
    topScope = getTopLevelProperties(chartProperties)
    return topScope[MESSAGE_QUEUE]

def getDatabaseName(chartProperties):
    '''Get the name of the database this chart is using, taking isolation mode into account'''
    isolationMode = getIsolationMode(chartProperties)
    
    ''' I added some strange looking Python to get this to work from the Test Framework. '''

    if isolationMode:
        IM = True
    else:
        IM = False
    
    ''' Leave this include here to avoid name clash '''
    from system.ils.sfc import getDatabaseName as systemGetDatabaseName
    db = systemGetDatabaseName(IM)
    return db

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

def getConsoleName(chartProperties, db):
    controlPanelId = getControlPanelId(chartProperties)
    SQL = "select ConsoleName from TkConsole C, SfcControlPanel CP "\
        " where CP.PostId = C.PostId and CP.ControlPanelId = %d" % (controlPanelId)
    consoleName = system.db.runScalarQuery(SQL, db) 
    return consoleName


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
    from system.ils.sfc import getTimeFactor as getModuleTimeFactor
    isolationMode = getIsolationMode(chartProperties)
    return getModuleTimeFactor(isolationMode)

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
    project=getProject(chartScope)
    consoleName=getConsoleName(chartScope, db)
    from ils.queue.message import insert as insertQueueMessage
    insertQueueMessage(queueKey, status, message, db, project, consoleName)

def postError(chartScope, message, queueKey=SFC_MESSAGE_QUEUE):
    '''  Post an error message to the SFC Message Queue if no other queue is specified.  '''

    db=getDatabaseName(chartScope)
    project=getProject(chartScope)
    consoleName=getConsoleName(chartScope, db)
    from ils.queue.message import insert as insertQueueMessage
    insertQueueMessage(queueKey, QUEUE_ERROR, message, db, project, consoleName)

def printSpace(level, out):
    for i in range(level):
        out.write('   '),

def readTag(chartScope, tagPath):
    '''  Read a tag substituting provider according to isolation mode.  '''
    provider = getProviderName(chartScope)
    fullPath = substituteProvider(tagPath, provider)
    qv = readTag(fullPath)
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

def sendOCAlert(chartProperties, stepProperties, post, topMessage, bottomMessage, mainMessage, buttonLabel, callback=None, callbackPayloadDictionary=None, 
                timeoutEnabled=False, timeoutSeconds=0, isolationMode=False):
    '''Send an OC alert'''
    project=getProject(chartProperties)
    db = getDatabaseName(chartProperties)
    sendAlert(project, post, topMessage, bottomMessage, mainMessage, buttonLabel, callback, callbackPayloadDictionary, timeoutEnabled, timeoutSeconds, db, isolationMode)

def sendMessageToClient(chartScope, messageHandler, payload):
    '''Send a message to the client(s) of this chart'''
    logger.tracef("In %s.sendMessageToClient() - Sending a %s SFC message... ", __name__, str(messageHandler))
    logger.tracef("The chart scope is: %s", str(chartScope))
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

    from ils.sfc.common.notify import sfcNotify
    sfcNotify(project, 'sfcMessage', payload, post, controlPanelName, controlPanelId, db)

def setCurrentMessageQueue(chartProperties, queue):
    '''Set the currently used message queue'''
    topScope = getTopLevelProperties(chartProperties)
    topScope[MESSAGE_QUEUE] = queue
    database = getDatabaseName(chartProperties)
    controlPanelId = getControlPanelId(chartProperties)
    system.db.runUpdateQuery("update SfcControlPanel set msgQueue = '%s' where controlPanelId = %d" % (queue, controlPanelId), database)

def  writeToOperatorLogbook(chartScope, post, message):
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
