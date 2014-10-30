'''
Lower-level utilities supporting sfcs

Created on Sep 30, 2014

@author: rforbes
'''
import system.util
from system.ils.sfc import * # this maps Java classes
from ils.sfc.api import *
#from com.ils.sfc.common import IlsSfcNames 
#from com.ils.sfc.util import IlsResponseManager
from ils.sfc.constants import RESPONSE_HANDLER
from ils.common.units import Unit
import logging

# Chart states:
Aborted = 0
Aborting = 1
Canceled = 2
Canceling = 3
Initial = 4
Paused = 5
Pausing = 6
Resuming = 7
Running = 8
Starting = 9
Stopped = 10
Stopping = 11
    
# Chart scope keys
MESSAGE_QUEUE = 'messageQueue'
PARENT_SCOPE = 'chart.parent'
CHART_STATE = 'chart.state'
PROJECT = 'project'
DATABASE = 'database'
RESPONSE = 'response'
LOCATION = 'location'
INSTANCE_ID = 'instanceId'

# client message handlers
SHOW_QUEUE_HANDLER = 'sfcShowQueue'
YES_NO_HANDLER = 'sfcYesNo'
DELETE_DELAY_NOTIFICATIONS_HANDLER = 'sfcDeleteDelayNotifications'
POST_DELAY_NOTIFICATION_HANDLER = 'sfcPostDelayNotification'
CONTROL_PANEL_MSG_HANDLER = 'sfcControlPanelMessage'
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

counter = 0

def getLogger():
    return logging.getLogger('ilssfc')


def printCounter():
    global counter
    print counter
    counter = counter + 1
    
def getWithPath(properties, key):
    '''
    Get a value using a potentially compound key
    '''

def getLocalScope(chartProperties, stepProperties):
    '''
    Get the local scope dictionary, creating it if necessary. 
    As this is dependent on a key convention, ALL accesses to 
    local scope should go through this method in case the 
    convention changes...
    '''
    stepName = getStepProperty(stepProperties, NAME)
    localScope = chartProperties[BY_NAME].get(stepName, None)
    if localScope == None:
        localScope = dict()
        chartProperties[BY_NAME][stepName] = localScope
    return localScope

def getPropertiesByLocation(chartProperties, stepProperties, location, create=False):
    '''
    Get the property dictionary of the element at the given location.
    Return None if not found.
    '''
    if location == SUPERIOR:
        return chartProperties[PARENT_SCOPE]       
    elif location == PROCEDURE or location == PHASE or location == OPERATION or location == GLOBAL:
        return getPropertiesByLevel(chartProperties, location)
    elif location == LOCAL:
        return getLocalScope(chartProperties, stepProperties)
    elif location == NAMED:
        return chartProperties[BY_NAME]
    elif location == PREVIOUS:
        return chartProperties[BY_NAME].get(PREVIOUS, None)
    else:
        reportUnexpectedError("unknown property location type %s", location)
        
def getPropertiesByLevel(chartProperties, location):
    ''' Use of PROCEDURE, PHASE, and OPERATION depends on the charts at
        those levels setting the LOCATION property 
    '''
    thisLocation = chartProperties.get(LOCATION, None)
    if location == thisLocation:
        return chartProperties
    else:
        parentProperties = chartProperties[PARENT_SCOPE]
        if parentProperties != None:
            return getPropertiesByLevel(parentProperties, location)
        else:
            return None
        
def createUniqueId():
    '''
    create a unique id
    '''
    import uuid
    return str(uuid.uuid4())
    
def sendMessage(project, handler, payload):
    # TODO: check returned list of recipients
    # TODO: restrict to a particular client session
    messageId = createUniqueId()
    payload[MESSAGE_ID] = messageId
    print 'sending message to clients', project, handler
    system.util.sendMessage(project, handler, payload, "C")
    return messageId
    
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
    while response == None:
        time.sleep(10);
        # chartState = chartScope[CHART_STATE]
        # if chartState == Canceling or chartState == Pausing or chartState == Aborting:
            # TODO: log that we're bailing
        # return None
        response = getResponse(requestId)
    return response

def sendResponse(requestPayload, responsePayload):
    '''
    This method is called from CLIENT scope to 
    send a reply to the Gateway
    '''
    messageId = requestPayload[MESSAGE_ID]
    responsePayload[MESSAGE_ID] = messageId    
    project = system.util.getProjectName()
    system.util.sendMessage(project, RESPONSE_HANDLER, responsePayload, "G")
    
def sendControlPanelMessage(chartProperties, stepProperties):
    payload = dict()
    transferStepPropertiesToMessage(stepProperties,payload)
    project = chartProperties[PROJECT];
    sendMessage(project, CONTROL_PANEL_MSG_HANDLER, payload)

def substituteScopeReferences(chartProperties, stepProperties, sql):
    ''' Substitute for scope variable references, e.g. 'local:selected-emp.val'
    '''
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
    print a dictionary into a nice, readable indented form
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
    if hasattr(obj, 'keys'):
        out.write('\n') # newline
        for key in obj:
            printSpace(level, out)
            out.write(key)
            printObj(obj[key], level + 1, out)
    else:
        #printSpace(level)
        out.write( ': ')
        out.write(str(obj))
        out.write('\n')

def readFile(filepath):
    '''
    Read the contents of a file into a string
    '''
    import StringIO
    out = StringIO.StringIO()
    fp = open(filepath, 'r')
    line = "dummy"
    while line != "":
        line = fp.readline()
        out.write(line)
    fp.close()
    result = out.getvalue()
    out.close()
    return result   

def reportUnexpectedError(msg):
    '''
    Report an unexpected error so that it is visible to the operator--
    e.g. put in a message queue
    '''
    getLogger.error(msg)
    #TODO: message the client, or queue a message that the client will see