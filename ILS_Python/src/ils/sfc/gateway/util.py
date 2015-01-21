'''
Lower-level utilities supporting sfcs

Created on Sep 30, 2014

@author: rforbes
'''
from system.ils.sfc import getResponse
from ils.sfc.common.constants import *
from ils.sfc.common.util import getChartRunId
from ils.sfc.common.util import getDatabase

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

def getStepProperty(stepProperties, pname):
    # Why isn't there a dictionary so we don't have to loop ?!
    for prop in stepProperties.getProperties():
        if prop.getName() == pname:
            return stepProperties.getOrDefault(prop)
    return None

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
    
def substituteScopeReferences(chartProperties, stepProperties, sql):
    ''' Substitute for scope variable references, e.g. 'local:selected-emp.val'
    '''
    from ils.sfc.gateway.api import s88Get
    # really wish Python had a do-while loop...
    while True:
        ref = findBracketedScopeReference(sql)
        if ref != None:
            location, key = parseBracketedScopeReference(ref)
            value = s88Get(chartProperties, stepProperties, key, location)
            sql = sql.replace(ref, str(value))
        else:
            break
    return sql

def addControlPanelMessage(chartProperties, message, ackRequired):
    from ils.sfc.common.sessions import addControlPanelMessage 
    chartRunId = getChartRunId(chartProperties)
    db = getDatabase(chartProperties)
    msgId = addControlPanelMessage(message, ackRequired, chartRunId, db)
    sendUpdateControlPanelMsg(chartProperties)
    return msgId

def findBracketedScopeReference(string):
    '''
     Find the first bracketed reference in the string, e.g. {local:selected-emp.val}
     or return None if not found
     '''
    lbIndex = string.find('{')
    rbIndex = string.find('}')
    colonIndex = string.find(':')
    if lbIndex != -1 and rbIndex != -1 and colonIndex != -1 and colonIndex > lbIndex and rbIndex > colonIndex:
        return string[lbIndex : rbIndex+1]
    else:
        return None

# Get the chart's own working copy of all the recipe data, creating it 
# if it doesn't exist
def getWorkingRecipeData(chartProperties):
    from ils.sfc.common.util import getTopLevelProperties 
    from system.ils.sfc import getWorkingRecipeData
    topChartProperties = getTopLevelProperties(chartProperties)
    if not (RECIPE_DATA in topChartProperties):
        data = getWorkingRecipeData()
        topChartProperties[RECIPE_DATA] = data
    data = topChartProperties[RECIPE_DATA]
    return data
    
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

def parseBracketedScopeReference(bracketedRef):
    '''
    Break a bracked reference into location and key--e.g. {local:selected-emp.val} gets
    broken into 'local' and 'selected-emp.val'
    '''   
    colonIndex = bracketedRef.index(':')
    location = bracketedRef[1 : colonIndex].strip()
    key = bracketedRef[colonIndex + 1 : len(bracketedRef) - 1].strip()
    return location, key

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
    
def getChartState(uuid):
    from system.ils.sfc import getChartState
    return getChartState(uuid)

def getDefaultMessageQueueScope():
    return OPERATION_SCOPE

def getCurrentMessageQueue(chartProperties, stepProperties):
    from ils.sfc.gateway.api import s88Get 
    return s88Get(chartProperties, stepProperties, MESSAGE_ID, getDefaultMessageQueueScope())

#def sendChartStatus(projectName, payload):
#    from ils.sfc.common.util import sendMessageToClient
#    sendMessageToClient(chartProperties, UPDATE_CHART_STATUS_HANDLER, payload)
    
def getRecipeScope(stepProperties):
    return getStepProperty(stepProperties,RECIPE_LOCATION)
 