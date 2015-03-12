'''
Lower-level utilities supporting sfcs

Created on Sep 30, 2014

@author: rforbes
'''
from system.ils.sfc import getResponse
from ils.sfc.common.constants import *
from ils.sfc.common.util import getChartRunId

# client message handlers
SHOW_QUEUE_HANDLER = 'sfcShowQueue'
YES_NO_HANDLER = 'sfcYesNo'
DELETE_DELAY_NOTIFICATIONS_HANDLER = 'sfcDeleteDelayNotifications'
DELETE_DELAY_NOTIFICATION_HANDLER = 'sfcDeleteDelayNotification'
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
CLOSE_WINDOW_HANDLER = 'sfcCloseWindow'
SHOW_WINDOW_HANDLER = 'sfcShowWindow'
CP_UPDATE_HANDLER = 'sfcUpdateControlPanel'
UPDATE_CHART_STATUS_HANDLER = 'sfcUpdateChartStatus'
UPDATE_CURRENT_OPERATION_HANDLER = 'sfcUpdateCurrentOperation'
REVIEW_DATA_HANDLER = 'sfcReviewData'

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

def getRecipeScope(stepProperties):
    return getStepProperty(stepProperties, RECIPE_LOCATION)

def getStepProperty(stepProperties, pname):
    # Why isn't there a dictionary so we don't have to loop ?!
    for prop in stepProperties.getProperties():
        if prop.getName() == pname:
            return stepProperties.getOrDefault(prop)
    return None

def hasStepProperty(stepProperties, pname):
    # Why isn't there a dictionary so we don't have to loop ?!
    for prop in stepProperties.getProperties():
        if prop.getName() == pname:
            return True
    return False

def transferStepPropertiesToMessage(stepProperties, payload):
    for prop in stepProperties.getProperties():
        payload[prop.getName()] = stepProperties.getOrDefault(prop)
 
def waitOnResponse(requestId, chartScope):
    '''
    Sleep until a response to the given request
    has been received. Callers should be
    prepared for a None return, which means
    the chart has been canceled/paused/aborted
    '''
    import time
    response = None
    #TODO: have some configurable timeout logic here
    sleepTime = 10 # seconds
    maxCycles = 5 * 60 / sleepTime
    cycle = 0
    while response == None and cycle < maxCycles:
        time.sleep(sleepTime);
        cycle = cycle + 1
        # chartState = chartScope[CHART_STATE]
        # if chartState == Canceling or chartState == Pausing or chartState == Aborting:
            # TODO: log that we're bailing
        # return None
        response = getResponse(requestId)
    if response == None:
        handleUnexpectedGatewayError(chartScope, "timed out waiting for response for requestId" + requestId)
    return response
    
def sendUpdateControlPanelMsg(chartProperties):
    from ils.sfc.common.util import sendMessageToClient
    sendMessageToClient(chartProperties, CP_UPDATE_HANDLER, dict())

def getFullChartPath(chartProperties):
    if(chartProperties.parent != None):
        return getFullChartPath(chartProperties.parent) + '/' + chartProperties.chartPath
    else:
        return chartProperties.chartPath
    
def escapeSingleQuotes(msg):
    return msg.replace("'", "''")

def addControlPanelMessage(chartProperties, message, ackRequired):
    from ils.sfc.common.sessions import addControlPanelMessage 
    from ils.sfc.common.util import getDatabaseName
    escapedMessage = escapeSingleQuotes(message)
    chartRunId = getChartRunId(chartProperties)
    database = getDatabaseName(chartProperties)
    msgId = addControlPanelMessage(escapedMessage, ackRequired, chartRunId, database)
    sendUpdateControlPanelMsg(chartProperties)
    return msgId

def handleUnexpectedGatewayError(chartProps, msg):
    from ils.sfc.common.util import getLogger
    from ils.sfc.common.util import sendMessageToClient
    UNEXPECTED_ERROR_HANDLER = 'sfcUnexpectedError'
    '''
    Report an unexpected error so that it is visible to the operator--
    e.g. put in a message queue
    '''
    getLogger().error(msg)
    payload = dict()
    payload[MESSAGE] = msg
    sendMessageToClient(chartProps, UNEXPECTED_ERROR_HANDLER, payload)

def copyData(pyDataSet, rowIndex, toDict):
    '''
    Copy data from one row of a PyDataSet into a dictionary,
    using the column names as the keys
    '''
    for colIndex in range(pyDataSet.columnCount):
        key = pyDataSet.getColumnName(colIndex)
        value = pyDataSet.getValueAt(rowIndex, colIndex)
        toDict[key] = value

def writeSpace(level, file):
    for i in range(level):
        file.write('   '),
        
def writeObj(obj, level, file):
    if hasattr(obj, 'keys'):
        file.write('\n') # newline
        for key in obj:
            writeSpace(level, file)
            file.write(key)
            writeObj(obj[key], level + 1, file)
    else:
        #printSpace(level)
        file.write( ': ')
        file.write(str(obj))
        file.write('\n')

def prettyPrintDict(dict):
    '''
    print a java dictionary into a nice, readable indented form
    returns a string containing the pretty-printed representation
    '''
    import StringIO
    out = StringIO.StringIO()
    printObj(dict, 0, out)
    result = out.getvalue()
    out.close()
    return result

def printSpace(level, out):
    for i in range(level):
        out.write('   '),
        
def printObj(obj, level, out):
    import java.util.HashMap
    if isinstance(obj, java.util.HashMap) :
        out.write('\n') # newline
        for key in obj.keySet():
            printSpace(level, out)
            out.write(key)
            printObj(obj[key], level + 1, out)
    else:
        #printSpace(level)
        out.write( ': ')
        out.write(str(obj))
        out.write('\n')

def getDefaultMessageQueueScope():
    return OPERATION_SCOPE

def getCurrentMessageQueue(chartProperties, stepProperties):
    from ils.sfc.gateway.api import s88Get 
    return s88Get(chartProperties, stepProperties, MESSAGE_ID, getDefaultMessageQueueScope())

def substituteScopeReferences(scopeContext, stepProperties, sql):
    pass

def sendChartStatus(projectName, payload):
    import system.util
    system.util.sendMessage(projectName, UPDATE_CHART_STATUS_HANDLER, payload, "C")
    
def sendCurrentOperation(projectName, payload):
    import system.util
    system.util.sendMessage(projectName, UPDATE_CURRENT_OPERATION_HANDLER, payload, "C")
    
 