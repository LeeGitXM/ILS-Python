'''
Methods that are associated with particular SFC step types, matching
one-to-one with step calls in the Java class JythonCall

Created on Sep 30, 2014

@author: rforbes
'''
#from com.ils.sfc.common import IlsSfcNames
from ils.sfc.gateway.util import * 
from ils.sfc.common.constants import *
from ils.sfc.common.util import sendMessage
from ils.sfc.common.util import getLogger

from ils.queue.message import insert
from ils.queue.message import clear
from system.sfc import cancelChart
from system.sfc import pauseChart
from time import sleep
import system.tag

def queueInsert(chartProperties, stepProperties):
    '''
    action for java QueueMessageStep
    queues the step's message
    '''
    print('line 1')
    currentMsgQueue = s88Get(chartProperties, stepProperties, MESSAGE_ID, OPERATION)
    message = getStepProperty(stepProperties, MESSAGE)  
    status = getStepProperty(stepProperties, STATUS)  
    database = chartProperties[DATABASE]
    insert(currentMsgQueue, status, message, database) 
    
def setQueue(chartProperties, stepProperties):
    '''
    action for java SetQueueStep
    sets the chart's current message queue
    '''
    queue = getStepProperty(stepProperties, QUEUE)
    # TODO: what to use for scope here ?:
    recipeLocation = OPERATION
    s88Set(chartProperties, stepProperties, MESSAGE_QUEUE, queue, recipeLocation, True)

def showQueue(chartProperties, stepProperties):
    '''
    action for java ShowQueueStep
    send a message to the client to show the current message queue
    '''
    currentMsgQueue = s88Get(chartProperties, stepProperties, MESSAGE_QUEUE, OPERATION) 
    payload = dict()
    payload[QUEUE] = currentMsgQueue 
    project = chartProperties[PROJECT];
    sendMessage(project, SHOW_QUEUE_HANDLER, payload)

def clearQueue(chartProperties, stepProperties):
    '''
    action for java ClearQueueStep
    delete all messages from the current message queue
    '''
    currentMsgQueue = s88Get(chartProperties, stepProperties, MESSAGE_QUEUE, OPERATION) 
    database = chartProperties[DATABASE]
    clear(currentMsgQueue, database)

def yesNo(chartProperties, stepProperties):
    '''
    Action for java YesNoStep
    Get a yes/no response from the user; block until a
    response is received, put response in chart properties
    '''
    prompt = getStepProperty(stepProperties, PROMPT) 
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
    key = getStepProperty(stepProperties, KEY) 
    payload = dict()
    payload[PROMPT] = prompt 
    project = chartProperties[PROJECT];
    messageId = sendMessage(project, YES_NO_HANDLER, payload)
    response = waitOnResponse(messageId, chartProperties)
    value = response[RESPONSE]
    s88Set(chartProperties, stepProperties, key, value, recipeLocation, False)

def cancel(chartProperties, stepProperties):
    ''' Abort the chart execution'''
    from ils.sfc.gateway.api import cancelChart
    cancelChart(chartProperties)
    addControlPanelMessage(chartProperties, "Chart canceled", False)
    
def pause(chartProperties, stepProperties):
    ''' Pause the chart execution'''
    from ils.sfc.gateway.api import pauseChart
    pauseChart(chartProperties)
    addControlPanelMessage(chartProperties, "Chart paused", False)
    
def controlPanelMessage(chartProperties, stepProperties):
    import time
    from ils.sfc.common.sessions import getAckTime
    from ils.sfc.common.sessions import timeOutControlPanelMessageAck
    from ils.common.units import Unit
    message = getStepProperty(stepProperties, MESSAGE)
    ackRequired = getStepProperty(stepProperties, ACK_REQUIRED)
    msgId = addControlPanelMessage(chartProperties, message, ackRequired)
    if ackRequired:
        database = chartProperties[DATABASE]
        timeout = message = getStepProperty(stepProperties, TIMEOUT)
        timeoutUnit = getStepProperty(stepProperties, TIMEOUT_UNIT)
        timeoutSeconds = Unit.convert(timeoutUnit, SECOND, timeout)
        sleepSeconds = 15
        elapsedSeconds = 0
        startTime = time.time()
        ackTime = None
        while ackTime == None and (timeoutSeconds > 0 and elapsedSeconds < timeoutSeconds):
            time.sleep(sleepSeconds);
            ackTime = getAckTime(msgId, database)
            elapsedSeconds = time.time() - startTime
        if ackTime == None:
            timeOutControlPanelMessageAck(msgId, database)
        sendUpdateControlPanelMsg(chartProperties)
            
def timedDelay(chartProperties, stepProperties):
    timeDelayStrategy = getStepProperty(stepProperties, TIME_DELAY_STRATEGY) 
    callback = getStepProperty(stepProperties, CALLBACK) 
    postNotification = getStepProperty(stepProperties, POST_NOTIFICATION) 
    key = getStepProperty(stepProperties, KEY) 
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
    delayUnit = getStepProperty(stepProperties, DELAY_UNIT)
    if timeDelayStrategy == STATIC:
        delay = getStepProperty(stepProperties, DELAY) 
    elif timeDelayStrategy == RECIPE:
        delay = s88Get(chartProperties, stepProperties, key, recipeLocation)
    elif timeDelayStrategy == CALLBACK:
        pass # TODO: implement script callback--value can be dynamic
    delaySeconds = Unit.convert(delayUnit, SECOND, delay)
    if postNotification:
        payload = dict()
        payload[MESSAGE] = str(delay) + ' ' + delayUnit + " remaining."
        project = chartProperties[PROJECT];
        sendMessage(project, POST_DELAY_NOTIFICATION_HANDLER, payload)
    sleep(delaySeconds)
      
def postDelayNotification(chartProperties, stepProperties):
    project = chartProperties[PROJECT];
    message = getStepProperty(stepProperties, MESSAGE) 
    payload = dict()
    payload[MESSAGE] = message
    sendMessage(project, POST_DELAY_NOTIFICATION_HANDLER, payload)

def deleteDelayNotifications(chartProperties, stepProperties):
    project = chartProperties[PROJECT];
    payload = dict()
    sendMessage(project, DELETE_DELAY_NOTIFICATIONS_HANDLER, payload)

def enableDisable(chartProperties, stepProperties):
    project = chartProperties[PROJECT];
    payload = dict()
    transferStepPropertiesToMessage(stepProperties, payload)
    sendMessage(project, ENABLE_DISABLE_HANDLER, payload)

def selectInput(chartProperties, stepProperties):
    # extract properties
    project = chartProperties[PROJECT];
    prompt = getStepProperty(stepProperties, PROMPT) 
    choicesRecipeLocation = getStepProperty(stepProperties, CHOICES_RECIPE_LOCATION) 
    choicesKey = getStepProperty(stepProperties, CHOICES_KEY) 
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
    key = getStepProperty(stepProperties, KEY) 

    choices = s88Get(chartProperties, stepProperties, choicesKey, choicesRecipeLocation)
    
    # send message
    payload = dict()
    payload[PROMPT] = prompt
    payload[CHOICES] = choices
    
    messageId = sendMessage(project, SELECT_INPUT_HANDLER, payload) 
    
    response = waitOnResponse(messageId, chartProperties)
    value = response[RESPONSE]
    s88Set(chartProperties, stepProperties, key, value, recipeLocation, True)

def getLimitedInput(chartProperties, stepProperties):
    project = chartProperties[PROJECT];
    prompt = getStepProperty(stepProperties, PROMPT) 
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
    key = getStepProperty(stepProperties, KEY) 
    minimumValue = getStepProperty(stepProperties, MINIMUM_VALUE)
    maximumValue = getStepProperty(stepProperties, MAXIMUM_VALUE) 
    
    payload = dict()
    payload[PROMPT] = prompt
    payload[MINIMUM_VALUE] = minimumValue
    payload[MAXIMUM_VALUE] = maximumValue
    responseIsValid = False
    while not responseIsValid:
        messageId = sendMessage(project, LIMITED_INPUT_HANDLER, payload)   
        responseMsg = waitOnResponse(messageId, chartProperties)
        responseValue = responseMsg[RESPONSE]
        try:
            floatValue = float(responseValue)
            responseIsValid = floatValue >= minimumValue and floatValue <= maximumValue
        except ValueError:
            payload[PROMPT] = 'Input is not valid. ' + prompt  
    
    s88Set(chartProperties, stepProperties, key, floatValue, recipeLocation, True)

def dialogMessage(chartProperties, stepProperties):
    payload = dict()
    transferStepPropertiesToMessage(stepProperties,payload)
    project = chartProperties[PROJECT];
    sendMessage(project, DIALOG_MSG_HANDLER, payload)


def collectData(chartProperties, stepProperties):
    tagPath = getStepProperty(stepProperties, TAG_PATH)
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
    key = getStepProperty(stepProperties, KEY) 
    value = system.tag.read(tagPath)
    s88Set(chartProperties, stepProperties, key, value, recipeLocation, True)
    
def getInput(chartProperties, stepProperties):
    project = chartProperties[PROJECT];
    prompt = getStepProperty(stepProperties, PROMPT) 
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
    key = getStepProperty(stepProperties, KEY) 
   
    payload = dict()
    payload[PROMPT] = prompt
    
    messageId = sendMessage(project, INPUT_HANDLER, payload)
    
    response = waitOnResponse(messageId, chartProperties)
    value = response[RESPONSE]
    s88Set(chartProperties, stepProperties, key, value, recipeLocation, True)

def rawQuery(chartProperties, stepProperties):
    database = getStepProperty(stepProperties, DATABASE) 
    sql = getStepProperty(stepProperties, SQL) 
    result = system.db.runQuery(sql, database) # returns a PyDataSet
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
    key = getStepProperty(stepProperties, KEY) 
    s88Set(chartProperties, stepProperties, key, result, recipeLocation, False)

def simpleQuery(chartProperties, stepProperties):
    database = getStepProperty(stepProperties, DATABASE) 
    sql = getStepProperty(stepProperties, SQL) 
    processedSql = substituteScopeReferences(chartProperties, stepProperties, sql)
    dbRows = system.db.runQuery(processedSql, database).getUnderlyingDataset() 
    if dbRows.rowCount == 0:
        getLogger.error('No rows returned for query %s', processedSql)
        return
    simpleQueryProcessRows(chartProperties, stepProperties, dbRows)

def simpleQueryProcessRows(chartProperties, stepProperties, dbRows):
    resultsMode = getStepProperty(stepProperties, RESULTS_MODE)
    fetchMode = getStepProperty(stepProperties, FETCH_MODE) 
    createFlag = fetchMode == UPDATE_OR_CREATE
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
    keyMode = getStepProperty(stepProperties, KEY_MODE) 
    key = getStepProperty(stepProperties, KEY) 
    recipeData = getPropertiesByLocation(chartProperties, stepProperties, recipeLocation, createFlag)
    if keyMode == STATIC: # fetchMode must be SINGLE
        if dbRows.rowCount > 1:
            getLogger().warn('More than one row returned for single query')
        # TODO: what about creation?
        newObj = dict()
        recipeData[key] = newObj
        copyData(dbRows, 0, newObj)
    elif keyMode == DYNAMIC:
        for rowNum in range(dbRows.rowCount):
            newObj = dict()
            copyData(dbRows, rowNum, newObj)
            dkey = newObj[key]
            recipeData[dkey] = newObj
     
def saveData(chartProperties, stepProperties):
    import time
    
    # extract property values
    project = chartProperties[PROJECT];
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
    directory = getStepProperty(stepProperties, DIRECTORY) 
    fileName = getStepProperty(stepProperties, FILENAME) 
    extension = getStepProperty(stepProperties, EXTENSION) 
    doTimestamp = getStepProperty(stepProperties, TIMESTAMP) 
    printFile = getStepProperty(stepProperties, PRINT_FILE) 
    viewFile = getStepProperty(stepProperties, VIEW_FILE) 
    
    # lookup the directory if it is a variab,e
    if directory.startswith('['):
        directory = chartProperties.get(directory, None)
        if directory == None:
            getLogger().error("directory key " + directory + " not found")
            
    # create timestamp if requested
    if doTimestamp: 
        timestamp = "-" + time.strftime("%Y%m%d%H%M")
    else:
        timestamp = ""
    
    # get the data at the given location
    data = getPropertiesByLocation(chartProperties, stepProperties, recipeLocation, False)
    if chartProperties == None:
        getLogger.error("data for location " + recipeLocation + " not found")
    
    # write the file
    filepath = directory + '/' + fileName + timestamp + extension
    fp = open(filepath, 'w')
    writeObj(data, 0, fp)
    fp.close()
    
    # send message to client for view/print
    if printFile or viewFile:
        payload = dict()
        #payloadData = dict()
        #for key in data:
        #    payloadData[key] = data[key]
        payload[DATA] = prettyPrintDict(data)
        payload[FILEPATH] = filepath
        payload[PRINT_FILE] = printFile
        payload[VIEW_FILE] = viewFile
        sendMessage(project, SAVE_DATA_HANDLER, payload)
        
def printFile(chartProperties, stepProperties):  
    from ils.sfc.common.util import readFile
    # extract property values
    computer = getStepProperty(stepProperties, COMPUTER) 
    payload = dict()
    if computer == SERVER:
        fileName = getStepProperty(stepProperties, FILENAME) 
        payload[MESSAGE] = readFile(fileName)
    transferStepPropertiesToMessage(stepProperties, payload)
    project = chartProperties[PROJECT];
    sendMessage(project, PRINT_FILE_HANDLER, payload)

def printWindow(chartProperties, stepProperties):   
    payload = dict()
    transferStepPropertiesToMessage(stepProperties, payload)
    project = chartProperties[PROJECT];
    sendMessage(project, PRINT_WINDOW_HANDLER, payload)
    
def closeWindow(chartProperties, stepProperties):   
    payload = dict()
    transferStepPropertiesToMessage(stepProperties, payload)
    project = chartProperties[PROJECT];
    sendMessage(project, CLOSE_WINDOW_HANDLER, payload)

def showWindow(chartProperties, stepProperties):   
    payload = dict()
    transferStepPropertiesToMessage(stepProperties, payload)
    project = chartProperties[PROJECT];
    sendMessage(project, SHOW_WINDOW_HANDLER, payload) 

