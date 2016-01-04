'''
Lower-level utilities supporting sfcs

Created on Sep 30, 2014

@author: rforbes
'''
from system.ils.sfc import getResponse
from ils.sfc.common.constants import *
from ils.sfc.gateway.api import cancelChart, sendMessageToClient

# client message handlers
SHOW_QUEUE_HANDLER = 'sfcShowQueue'
#YES_NO_HANDLER = 'sfcYesNo'
DELETE_DELAY_NOTIFICATIONS_HANDLER = 'sfcDeleteDelayNotifications'
POST_DELAY_NOTIFICATION_HANDLER = 'sfcPostDelayNotification'
DIALOG_MSG_HANDLER = 'sfcDialogMessage'
TIMED_DELAY_HANDLER = 'sfcTimedDelay'
SELECT_INPUT_HANDLER = 'sfcSelectInput'
LIMITED_INPUT_HANDLER = 'sfcLimitedInput'
INPUT_HANDLER = 'sfcInput'
ENABLE_DISABLE_HANDLER = 'sfcEnableDisable'
SAVE_DATA_HANDLER = 'sfcSaveData'
PRINT_FILE_HANDLER = 'sfcPrintFile'
PRINT_WINDOW_HANDLER = 'sfcPrintWindow'
#CP_UPDATE_HANDLER = 'sfcUpdateControlPanel'
#UPDATE_CHART_STATUS_HANDLER = 'sfcUpdateChartStatus'
#UPDATE_CURRENT_OPERATION_HANDLER = 'sfcUpdateCurrentOperation'
REVIEW_DATA_HANDLER = 'sfcReviewData'
NEWLINE = '\n\r'

def printCounter():
    global counter
    print counter
    counter = counter + 1
    
def getWithPath(properties, key):
    '''
    Get a value using a potentially compound key
    '''
        
def getStepId(stepProperties):
    # need to translate the UUID to a string:
    if stepProperties != None:
        return str(getStepProperty(stepProperties, ID))
    else:
        return None

def getTopChartRunId(chartProperties):
    '''Get the run id of the chart at the TOP enclosing level'''
    return str(getTopLevelProperties(chartProperties)[INSTANCE_ID])

def getSessionId(chartProperties):
    '''Get the run id of the chart at the TOP enclosing level'''
    return str(getTopLevelProperties(chartProperties)[SESSION_ID])
    
def getTopLevelProperties(chartProperties):
    while chartProperties.get(PARENT, None) != None:
        chartProperties = chartProperties.get(PARENT)
    return chartProperties

def getRecipeScope(stepProperties):
    return getStepProperty(stepProperties, RECIPE_LOCATION) 

def getStepProperty(stepProperties, pname):
    for prop in stepProperties.getProperties():
        if prop.getName() == pname:
            return stepProperties.getOrDefault(prop)
    return None

def getStepName(stepProperties):
    return getStepProperty(stepProperties, NAME)

def hasStepProperty(stepProperties, pname):
    # Why isn't there a dictionary so we don't have to loop ?!
    for prop in stepProperties.getProperties():
        if prop.getName() == pname:
            return True
    return False

def transferStepPropertiesToMessage(stepProperties, payload):
    for prop in stepProperties.getProperties():
        # omit the associated-data as the JSONObject causes a serialization error
        if not (prop.getName() == 'associated-data'):
            payload[prop.getName()] = stepProperties.getOrDefault(prop)
 
def waitOnResponse(requestId, chartScope, timeoutTime=None):
    '''
    Sleep until a response to the given request
    has been received. Callers should be
    prepared for a None return, which means
    the chart has been canceled/paused/aborted
    '''
    import time
    responsePayload = None
    maxCycles = 5 * 60 / SLEEP_INCREMENT
    cycle = 0
    while responsePayload == None and cycle < maxCycles:
        if (timeoutTime != None) and (timeoutTime > 0.) and (time.time() >= timeoutTime):
            break
        time.sleep(SLEEP_INCREMENT);
        cycle = cycle + 1
        # chartState = chartScope[CHART_STATE]
        # if chartState == Canceling or chartState == Pausing or chartState == Aborting:
            # TODO: log that we're bailing
        # return None
        responsePayload = getResponse(requestId)

    if responsePayload == None:
        handleUnexpectedGatewayError(chartScope, "timed out waiting for response for requestId" + requestId)
        return None
    else:
        print 'returning response'
        return responsePayload[RESPONSE]
    
def getChartPath(chartProperties):
    return chartProperties.chartPath
    
def escapeSingleQuotes(msg):
    return msg.replace("'", "''")

def handleUnexpectedGatewayError(chartScope, msg, logger=None):
    from  ils.sfc.gateway.api import sendMessageToClient
    UNEXPECTED_ERROR_HANDLER = 'sfcUnexpectedError'
    '''
    Report an unexpected error so that it is visible to the operator--
    e.g. put in a message queue
    '''
    if logger != None:
        logger.error(msg)
    cancelChart(chartScope)
    payload = dict()
    payload[MESSAGE] = msg
    sendMessageToClient(chartScope, UNEXPECTED_ERROR_HANDLER, payload)

def copyRowToDict(dbRows, rowNum, pdict, create):
    columnCount = dbRows.getColumnCount()
    for colNum in range(columnCount):
        colName = dbRows.getColumnName(colNum)
        if colName in pdict.keys() or create:
            value = dbRows.getValueAt(rowNum, colNum)
            pdict[colName] = value

def writeSpace(level, file):
    for i in range(level):
        file.write('   '),
        
def writeObj(obj, level, file):
    if hasattr(obj, 'keys'):
        file.write(NEWLINE) 
        for key in obj:
            writeSpace(level, file)
            file.write(str(key))
            writeObj(obj[key], level + 1, file)
    else:
        #printSpace(level)
        file.write( ': ')
        file.write(str(obj))
        file.write(NEWLINE)

def dictToString(dict):
    '''
    print a java dictionary into a nice, readable indented form
    returns a string containing the pretty-printed representation
    '''
    import StringIO
    out = StringIO.StringIO()
    for key, value in dict.items():
        out.write(key)
        out.write(': ')
        out.write(value)
        out.write(NEWLINE)
    result = out.getvalue()
    out.close()
    return result

def printSpace(level, out):
    for i in range(level):
        out.write('   '),

def getDefaultMessageQueueScope():
    return OPERATION_SCOPE

#def sendChartStatus(projectName, payload):
#    from system.util import sendMessage
#    payload[MESSAGE] = UPDATE_CHART_STATUS_HANDLER
#    sendMessage(projectName, 'sfcMessage', payload, "C")
    
#def sendCurrentOperation(projectName, payload):
#    from system.util import sendMessage
#    payload[MESSAGE] = UPDATE_CURRENT_OPERATION_HANDLER
#    sendMessage(projectName, 'sfcMessage', payload, "C")
    
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

def createFilepath(chartScope, stepProperties, includeExtension):
    '''Create a filepath from dir/file/suffix in step properties'''
    import time
    from ils.sfc.gateway.api import getChartLogger
    logger = getChartLogger(chartScope)
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
            logger.error("directory key " + directory + " not found")
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

def getControlPanelId(chartScope):
    topScope = getTopLevelProperties(chartScope)
    return topScope.get(CONTROL_PANEL_ID,None)

def getTimeoutTime(chartScope, stepProperties):
    '''For steps that time out, get the time in epoch seconds when the timeout expires.
       Take the isolation mode time factor into account'''
    from ils.sfc.gateway.api import getTimeFactor
    import time
    timeFactor = getTimeFactor(chartScope)
    timeoutTime = None
    timeout = getStepProperty(stepProperties, TIMEOUT)
    if timeout != None and timeout > 0.:
        timeoutUnit = getStepProperty(stepProperties, TIMEOUT_UNIT)
        timeoutSeconds = getDelaySeconds(timeout, timeoutUnit)
        timeoutSeconds *= timeFactor
        timeoutTime = time.time() + timeoutSeconds
    return timeoutTime
    
def queueMessage(chartScope, msg, priority):
    '''insert a message in the current message queue'''
    from ils.sfc.gateway.api import getCurrentMessageQueue, getDatabaseName
    from ils.queue.message import insert
    currentMsgQueue = getCurrentMessageQueue(chartScope)
    database = getDatabaseName(chartScope)
    insert(currentMsgQueue, priority, msg, database) 

def checkForCancelOrPause(chartScope, logger):
    '''some commonly-used code to check for chart cancellation or pause in the midst 
       of long-running loops. A True return should cause a return from the step method'''
    from ils.sfc.common.constants import SLEEP_INCREMENT
    from system.ils.sfc import getCancelRequested, getPauseRequested
    import time
    topRunId = getTopChartRunId(chartScope)
    if getCancelRequested(topRunId):
        logger.debug("chart terminal; exiting step code")
        return True
    elif getPauseRequested(topRunId):
        # We had hoped to loop here until the chart was resumed, like this:
        # while getPauseRequested(topRunId):
        #    logger.debug("chart paused; holding in do-nothing loop")
        #    time.sleep(SLEEP_INCREMENT)
        # Unfortunately, the IA SFC engine appears to stay in Pausing state until the 
        # step method returns. So we have to exit in order to allow the Resume to 
        # work. ?!
        return True
    else:
        return False
    
def writeTestRamp(controllers, durationSecs, increment):
    '''bring the current value up to the setpoint in increments over the given time .'''
    from ils.sfc.gateway.abstractSfcIO import AbstractSfcIO
    import time

    startTime = time.time()
    endTime = startTime + durationSecs
    while time.time() < endTime:
        for i in range(len(controllers)):
            controller = controllers[i]
            currentValue = controller.getCurrentValue()
            setpoint = controller.getSetpoint()
            if currentValue < setpoint:
                sign = 1
            elif currentValue > setpoint:
                sign = -1
            else:
                sign = 0
            absDiff = abs(currentValue - setpoint) 
            adjustment = sign * min(increment, absDiff)
            controller.setCurrentValue(currentValue + adjustment)
        time.sleep(5)


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

#    if DEBUG-MODE then post "*** PV = [1PV], Target = [TARGET], High Limit = [HIGH-LIMIT], Low Limit = [Low-Limit] ****";

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

def basicPauseChart(topChartRunId):
    import system.sfc
    from system.ils.sfc import setPauseRequested
    setPauseRequested(topChartRunId)
    system.sfc.pauseChart(topChartRunId)
    
def basicResumeChart(topChartRunId):
    import system.sfc
    system.sfc.resumeChart(topChartRunId)

def basicCancelChart(topChartRunId):
    import system.sfc
    from system.ils.sfc import setCancelRequested
    setCancelRequested(topChartRunId)
    system.sfc.cancelChart(topChartRunId)
    
def createWindowRecord(controlPanelId, window, buttonLabel, position, scale, title, database):
    import system.db
    from ils.sfc.common.util import createUniqueId
    windowId = createUniqueId()
    system.db.runUpdateQuery("Insert into SfcWindow (windowId, controlPanelId, type, buttonLabel, position, scale, title) values ('%s', %d, '%s', '%s', '%s', %f, '%s')" % (windowId, controlPanelId, window, buttonLabel, position, scale, title), database)
    return windowId
    
def sendOpenWindow(chartScope, windowId, stepId, database):
    from system.ils.sfc import addRequestId
    addRequestId(windowId, stepId)
    sendMessageToClient(chartScope, 'sfcOpenWindow', {WINDOW_ID: windowId, DATABASE: database})

def deleteAndSendClose(chartScope, windowId, database):
    '''Delete the common window record and message the client to close the window'''
    import system.db
    system.db.runUpdateQuery("delete from SfcWindow where windowId = '%s'" % (windowId), database)
    sendMessageToClient(chartScope, 'sfcCloseWindow', {WINDOW_ID: windowId})

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