'''
Methods that are associated with particular SFC step types, matching
one-to-one with step calls in the Java class JythonCall

Created on Sep 30, 2014

@author: rforbes`
'''

s88CreateOverride = True # force create of recipe keys

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

def invokeStep(chartProperties, stepProperties, methodName):
    '''
    A single point to invoke all step methods, in order to do exception handling
    '''
    import sys
    func = globals()[methodName]
    try:
        func(chartProperties, stepProperties)
    except Exception, e:
        msg = "Unexpected error: " + type(e).__name__ + " " + str(e)
        print msg
        handleUnexpectedError(chartProperties, msg)
         
def queueInsert(chartProperties, stepProperties):
    '''
    action for java QueueMessageStep
    queues the step's message
    '''
    currentMsgQueue = getCurrentMessageQueue(chartProperties, stepProperties)
    message = getStepProperty(stepProperties, MESSAGE)  
    priority = getStepProperty(stepProperties, PRIORITY)  
    database = chartProperties[DATABASE]
    insert(currentMsgQueue, priority, message, database) 
    
def setQueue(chartProperties, stepProperties):
    '''
    action for java SetQueueStep
    sets the chart's current message queue
    '''
    queue = getStepProperty(stepProperties, QUEUE)
    recipeLocation = getDefaultMessageQueueScope()
    s88Set(chartProperties, stepProperties, MESSAGE_QUEUE, queue, recipeLocation, True or s88CreateOverride)

def showQueue(chartProperties, stepProperties):
    '''
    action for java ShowQueueStep
    send a message to the client to show the current message queue
    '''
    currentMsgQueue = getCurrentMessageQueue(chartProperties, stepProperties)
    payload = dict()
    payload[QUEUE] = currentMsgQueue 
    project = chartProperties[PROJECT];
    sendMessage(project, SHOW_QUEUE_HANDLER, payload)

def clearQueue(chartProperties, stepProperties):
    '''
    action for java ClearQueueStep
    delete all messages from the current message queue
    '''
    currentMsgQueue = getCurrentMessageQueue(chartProperties, stepProperties)
    database = chartProperties[DATABASE]
    clear(currentMsgQueue, database)

def yesNo(chartProperties, stepProperties):
    '''
    Action for java YesNoStep
    Get a yes/no response from the user; block until a
    response is received, put response in chart properties
    '''
    prompt = getStepProperty(stepProperties, PROMPT) 
    recipeLocation = getRecipeScope(stepProperties) 
    key = getStepProperty(stepProperties, KEY) 
    payload = dict()
    payload[PROMPT] = prompt 
    project = chartProperties[PROJECT];
    messageId = sendMessage(project, YES_NO_HANDLER, payload)
    response = waitOnResponse(messageId, chartProperties)
    value = response[RESPONSE]
    s88Set(chartProperties, stepProperties, key, value, recipeLocation, False or s88CreateOverride)

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
    from ils.queue.message import insert
    message = getStepProperty(stepProperties, MESSAGE)
    database = chartProperties[DATABASE]
    ackRequired = getStepProperty(stepProperties, ACK_REQUIRED)
    msgId = addControlPanelMessage(chartProperties, message, ackRequired)
    postToQueue = getStepProperty(stepProperties, POST_TO_QUEUE)
    if postToQueue:
        currentMsgQueue = getCurrentMessageQueue(chartProperties, stepProperties)
        priority = getStepProperty(stepProperties, PRIORITY)
        insert(currentMsgQueue, priority, message, database)
    if ackRequired:
        database = chartProperties[DATABASE]
        timeout = message = getStepProperty(stepProperties, TIMEOUT)
        timeoutUnit = getStepProperty(stepProperties, TIMEOUT_UNIT)
        timeoutSeconds = Unit.convert(timeoutUnit, SECOND, timeout, database)
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
    from ils.sfc.common.util import createUniqueId
    database = chartProperties[DATABASE]
    timeDelayStrategy = getStepProperty(stepProperties, STRATEGY) 
    callback = getStepProperty(stepProperties, CALLBACK) 
    postNotification = getStepProperty(stepProperties, POST_NOTIFICATION) 
    key = getStepProperty(stepProperties, KEY) 
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
    # TODO: we need a better solution for unit initialization:
    delayUnit = getStepProperty(stepProperties, DELAY_UNIT)
    if timeDelayStrategy == STATIC:
        delay = getStepProperty(stepProperties, DELAY) 
    elif timeDelayStrategy == RECIPE:
        delay = s88Get(chartProperties, stepProperties, key, recipeLocation)
    elif timeDelayStrategy == CALLBACK:
        pass # TODO: implement script callback--value can be dynamic
        handleUnexpectedError(chartProperties, "Callback strategy not implemented: ")
    else:
        handleUnexpectedError(chartProperties, "unknown delay strategy: " + timeDelayStrategy)
    delaySeconds = Unit.convert(delayUnit, SECOND, delay, database)
    if postNotification:
        payload = dict()
        payload[CHART_RUN_ID] = getChartRunId(chartProperties)
        payload[MESSAGE] = str(delay) + ' ' + delayUnit + " remaining."
        payload[ACK_REQUIRED] = False
        payload[WINDOW_ID] = createUniqueId()
        project = chartProperties[PROJECT];
        sendMessage(project, POST_DELAY_NOTIFICATION_HANDLER, payload)
    sleep(delaySeconds)
    if postNotification:
        sendMessage(project, DELETE_DELAY_NOTIFICATION_HANDLER, payload)
      
def postDelayNotification(chartProperties, stepProperties):
    from ils.sfc.common.util import createUniqueId
    project = chartProperties[PROJECT];
    message = getStepProperty(stepProperties, MESSAGE) 
    payload = dict()
    payload[MESSAGE] = message
    print 'step props ', stepProperties
    payload[CHART_RUN_ID] = getChartRunId(chartProperties)
    payload[WINDOW_ID] = createUniqueId()
    sendMessage(project, POST_DELAY_NOTIFICATION_HANDLER, payload)

def deleteDelayNotifications(chartProperties, stepProperties):
    project = chartProperties[PROJECT];
    payload = dict()
    payload[CHART_RUN_ID] = getChartRunId(chartProperties)
    sendMessage(project, DELETE_DELAY_NOTIFICATIONS_HANDLER, payload)

def enableDisable(chartProperties, stepProperties):
    project = chartProperties[PROJECT];
    payload = dict()
    transferStepPropertiesToMessage(stepProperties, payload)
    payload[INSTANCE_ID] = chartProperties[INSTANCE_ID]
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
    s88Set(chartProperties, stepProperties, key, value, recipeLocation, True or s88CreateOverride)

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
    
    s88Set(chartProperties, stepProperties, key, floatValue, recipeLocation, True or s88CreateOverride)

def dialogMessage(chartProperties, stepProperties):
    from ils.sfc.common.util import getChartRunId
    payload = dict()
    transferStepPropertiesToMessage(stepProperties,payload)
    project = chartProperties[PROJECT];
    sendMessage(project, DIALOG_MSG_HANDLER, payload)

def collectData(chartProperties, stepProperties):
    tagPath = getStepProperty(stepProperties, TAG_PATH)
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
    key = getStepProperty(stepProperties, KEY) 
    value = system.tag.read(tagPath)
    s88Set(chartProperties, stepProperties, key, value, recipeLocation, True or s88CreateOverride)
    
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
    s88Set(chartProperties, stepProperties, key, value, recipeLocation, True or s88CreateOverride)

def rawQuery(chartProperties, stepProperties):
    database = getStepProperty(stepProperties, DATABASE) 
    sql = getStepProperty(stepProperties, SQL) 
    result = system.db.runQuery(sql, database) # returns a PyDataSet
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
    key = getStepProperty(stepProperties, KEY) 
    s88Set(chartProperties, stepProperties, key, result, recipeLocation, False or s88CreateOverride)

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
    from system.ils.sfc import getRecipeData
    from ils.sfc.common.constants import ID
    resultsMode = getStepProperty(stepProperties, RESULTS_MODE)
    fetchMode = getStepProperty(stepProperties, FETCH_MODE) 
    createFlag = fetchMode == UPDATE_OR_CREATE
    recipeLocation = getRecipeScope(stepProperties) 
    keyMode = getStepProperty(stepProperties, KEY_MODE) 
    key = getStepProperty(stepProperties, KEY) 
    stepId = getStepId(stepProperties)
    recipeData = getRecipeData(recipeLocation, stepId, None, createFlag)
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
    from system.ils.sfc import getRecipeData
    # extract property values
    project = chartProperties[PROJECT];
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
    key = getStepProperty(stepProperties, KEY) 
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
    stepId = getStepId(stepProperties)
    recipeData = getRecipeData(recipeLocation, stepId, key)
    if chartProperties == None:
        getLogger.error("data for location " + recipeLocation + " not found")
    
    # write the file
    filepath = directory + '/' + fileName + timestamp + extension
    fp = open(filepath, 'w')
    writeObj(recipeData, 0, fp)
    fp.close()
    
    # send message to client for view/print
    if printFile or viewFile:
        payload = dict()
        #payloadData = dict()
        #for key in data:
        #    payloadData[key] = data[key]
        payload[DATA] = prettyPrintDict(recipeData)
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
    payload[INSTANCE_ID] = getChartRunId(chartProperties)
    project = chartProperties[PROJECT];
    sendMessage(project, CLOSE_WINDOW_HANDLER, payload)

def showWindow(chartProperties, stepProperties):   
    from ils.sfc.common.util import getChartRunId
    payload = dict()
    payload[INSTANCE_ID] = getChartRunId(chartProperties)
    transferStepPropertiesToMessage(stepProperties, payload)
    project = chartProperties[PROJECT];
    security = payload[SECURITY]
    #TODO: implement security

    sendMessage(project, SHOW_WINDOW_HANDLER, payload) 

