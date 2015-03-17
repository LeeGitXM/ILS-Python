'''
Methods that are associated with particular SFC step types, matching
one-to-one with step calls in the Java class JythonCall

Created on Sep 30, 2014

@author: rforbes`
'''

#from com.ils.sfc.common import IlsSfcNames
from ils.sfc.gateway.api import s88Set, s88Get
from ils.common.units import Unit
from ils.sfc.gateway.util import * 
from ils.sfc.common.constants import *

from ils.sfc.common.util import getDatabaseName
from ils.sfc.common.util import sendMessageToClient
from ils.sfc.common.util import getLogger

from ils.queue.message import insert
from ils.queue.message import clear
from time import sleep
import system.tag

def invokeStep(scopeContext, stepProperties, methodName):
    '''
    A single point to invoke all step methods, in order to do exception handling
    '''
    func = globals()[methodName]
    try:
        func(scopeContext, stepProperties)
    except Exception, e:
        msg = "Unexpected error: " + type(e).__name__ + " " + str(e)
        print msg
        handleUnexpectedGatewayError(scopeContext, msg)
         
def queueInsert(scopeContext, stepProperties):
    '''
    action for java QueueMessageStep
    queues the step's message
    '''
    chartScope = scopeContext.getChartScope()
    currentMsgQueue = getCurrentMessageQueue(scopeContext, stepProperties)
    message = getStepProperty(stepProperties, MESSAGE)  
    priority = getStepProperty(stepProperties, PRIORITY)  
    database = getDatabaseName(chartScope)
    insert(currentMsgQueue, priority, message, database) 
    
def setQueue(scopeContext, stepProperties):
    '''
    action for java SetQueueStep
    sets the chart's current message queue
    '''
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    queue = getStepProperty(stepProperties, QUEUE)
    recipeLocation = getDefaultMessageQueueScope()
    s88Set(chartScope, stepScope, MESSAGE_QUEUE, recipeLocation, queue)

def showQueue(scopeContext, stepProperties):
    '''
    action for java ShowQueueStep
    send a message to the client to show the current message queue
    '''
    currentMsgQueue = getCurrentMessageQueue(scopeContext, stepProperties)
    payload = dict()
    payload[QUEUE] = currentMsgQueue 
    sendMessageToClient(scopeContext, SHOW_QUEUE_HANDLER, payload)

def clearQueue(scopeContext, stepProperties):
    '''
    action for java ClearQueueStep
    delete all messages from the current message queue
    '''
    chartScope = scopeContext.getChartScope()
    currentMsgQueue = getCurrentMessageQueue(scopeContext, stepProperties)
    database = getDatabaseName(chartScope)
    clear(currentMsgQueue, database)

def yesNo(scopeContext, stepProperties):
    '''
    Action for java YesNoStep
    Get a yes/no response from the user; block until a
    response is received, put response in chart properties
    '''
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    prompt = getStepProperty(stepProperties, PROMPT)
    recipeLocation = getRecipeScope(stepProperties) 
    key = getStepProperty(stepProperties, KEY) 
    payload = dict()
    payload[PROMPT] = prompt 
    messageId = sendMessageToClient(chartScope, YES_NO_HANDLER, payload)
    response = waitOnResponse(messageId, chartScope)
    value = response[RESPONSE]
    s88Set(chartScope, stepScope, key, recipeLocation, value)

def cancel(scopeContext, stepProperties):
    ''' Abort the chart execution'''
    from ils.sfc.gateway.api import cancelChart
    chartScope = scopeContext.getChartScope()
    cancelChart(chartScope)
    addControlPanelMessage(chartScope, "Chart canceled", False)
    
def pause(scopeContext, stepProperties):
    ''' Pause the chart execution'''
    from ils.sfc.gateway.api import pauseChart
    chartScope = scopeContext.getChartScope()
    pauseChart(chartScope)
    addControlPanelMessage(chartScope, "Chart paused", False)
    
def controlPanelMessage(scopeContext, stepProperties):
    import time
    from ils.sfc.common.sessions import getAckTime
    from ils.sfc.common.sessions import timeOutControlPanelMessageAck
    chartScope = scopeContext.getChartScope()
    message = getStepProperty(stepProperties, MESSAGE)
    database = getDatabaseName(chartScope)
    ackRequired = getStepProperty(stepProperties, ACK_REQUIRED)
    msgId = addControlPanelMessage(chartScope, message, ackRequired)
    postToQueue = getStepProperty(stepProperties, POST_TO_QUEUE)
    if postToQueue:
        currentMsgQueue = getCurrentMessageQueue(chartScope, stepProperties)
        priority = getStepProperty(stepProperties, PRIORITY)
        insert(currentMsgQueue, priority, message, database)
    if ackRequired:
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
        sendUpdateControlPanelMsg(chartScope)
            
def timedDelay(scopeContext, stepProperties):
    from ils.sfc.common.util import createUniqueId, getTimeFactor, callMethod
    from ils.sfc.gateway.util import getStepName
    import time
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    timeDelayStrategy = getStepProperty(stepProperties, STRATEGY) 
    if timeDelayStrategy == STATIC:
        delay = getStepProperty(stepProperties, DELAY) 
    elif timeDelayStrategy == RECIPE:
        recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
        key = getStepProperty(stepProperties, KEY) 
        delay = s88Get(chartScope, stepScope, key, recipeLocation)
    elif timeDelayStrategy == CALLBACK:
        callback = getStepProperty(stepProperties, CALLBACK) 
        delay = callMethod(callback)
    else:
        handleUnexpectedGatewayError(chartScope, "unknown delay strategy: " + str(timeDelayStrategy))

    delayUnit = getStepProperty(stepProperties, DELAY_UNIT)
    if delayUnit == DELAY_UNIT_SECOND:
        delaySeconds = delay
    elif delayUnit == DELAY_UNIT_MINUTE:
        delaySeconds = delay * 60
    elif delayUnit == DELAY_UNIT_HOUR:
        delaySeconds = delay * 3600
    else:
        handleUnexpectedGatewayError(chartScope, "Unknown delay unit: " + delayUnit)

    timeFactor = getTimeFactor(chartScope)
    delaySeconds = delaySeconds * timeFactor
    startTimeEpochSecs = time.time()
    endTimeEpochSecs = startTimeEpochSecs + delaySeconds
    postNotification = getStepProperty(stepProperties, POST_NOTIFICATION) 
    if postNotification:
        payload = dict()
        payload[CHART_NAME] = chartScope.chartPath
        payload[STEP_NAME] = getStepName(stepProperties)
        payload[CHART_RUN_ID] = getChartRunId(chartScope)
        payload[MESSAGE] = str(delay) + ' ' + delayUnit + " remaining."
        payload[ACK_REQUIRED] = False
        payload[WINDOW_ID] = createUniqueId()
        payload[END_TIME] = endTimeEpochSecs
        sendMessageToClient(chartScope, POST_DELAY_NOTIFICATION_HANDLER, payload)
    
    #TODO: put some logic in to check for cancellation/pausing
    #may need to do more in Java
    sleep(delaySeconds)
    
    if postNotification:
        sendMessageToClient(chartScope, DELETE_DELAY_NOTIFICATION_HANDLER, payload)
      
def postDelayNotification(scopeContext, stepProperties):
    from ils.sfc.common.util import createUniqueId
    chartScope = scopeContext.getChartScope()
    message = getStepProperty(stepProperties, MESSAGE) 
    payload = dict()
    payload[MESSAGE] = message
    print 'step props ', stepProperties
    payload[CHART_RUN_ID] = getChartRunId(chartScope)
    payload[WINDOW_ID] = createUniqueId()
    sendMessageToClient(chartScope, POST_DELAY_NOTIFICATION_HANDLER, payload)

def deleteDelayNotifications(scopeContext, stepProperties):
    chartScope = scopeContext.getChartScope()
    payload = dict()
    payload[CHART_RUN_ID] = getChartRunId(chartScope)
    sendMessageToClient(chartScope, DELETE_DELAY_NOTIFICATIONS_HANDLER, payload)

def enableDisable(scopeContext, stepProperties):
    chartScope = scopeContext.getChartScope()
    payload = dict()
    transferStepPropertiesToMessage(stepProperties, payload)
    payload[INSTANCE_ID] = chartScope[INSTANCE_ID]
    sendMessageToClient(chartScope, ENABLE_DISABLE_HANDLER, payload)

def selectInput(scopeContext, stepProperties):
    # extract properties
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    prompt = getStepProperty(stepProperties, PROMPT) 
    choicesRecipeLocation = getStepProperty(stepProperties, CHOICES_RECIPE_LOCATION) 
    choicesKey = getStepProperty(stepProperties, CHOICES_KEY) 
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
    key = getStepProperty(stepProperties, KEY) 

    choices = s88Get(chartScope, stepScope, choicesKey, choicesRecipeLocation)
    
    # send message
    payload = dict()
    payload[PROMPT] = prompt
    payload[CHOICES] = choices
    
    messageId = sendMessageToClient(chartScope, SELECT_INPUT_HANDLER, payload) 
    
    response = waitOnResponse(messageId, chartScope)
    value = response[RESPONSE]
    s88Set(chartScope, stepScope, key, recipeLocation, value)

def getLimitedInput(scopeContext, stepProperties):
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
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
        messageId = sendMessageToClient(chartScope, LIMITED_INPUT_HANDLER, payload)   
        responseMsg = waitOnResponse(messageId, chartScope)
        responseValue = responseMsg[RESPONSE]
        try:
            floatValue = float(responseValue)
            responseIsValid = floatValue >= minimumValue and floatValue <= maximumValue
        except ValueError:
            payload[PROMPT] = 'Input is not valid. ' + prompt  
    
    s88Set(chartScope, stepScope, key, recipeLocation, floatValue)

def dialogMessage(scopeContext, stepProperties):
    chartScope = scopeContext.getChartScope()
    payload = dict()
    transferStepPropertiesToMessage(stepProperties,payload)
    sendMessageToClient(chartScope, DIALOG_MSG_HANDLER, payload)

def collectData(scopeContext, stepProperties):
    from ils.sfc.common.util import substituteProvider
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    tagPath = getStepProperty(stepProperties, TAG_PATH)
    tagPath = substituteProvider(chartScope, tagPath)
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
    key = getStepProperty(stepProperties, KEY) 
    value = system.tag.read(tagPath)
    s88Set(chartScope, stepScope, key, recipeLocation, value)
    
def getInput(scopeContext, stepProperties):
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    prompt = getStepProperty(stepProperties, PROMPT) 
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
    key = getStepProperty(stepProperties, KEY) 
   
    payload = dict()
    payload[PROMPT] = prompt
    
    messageId = sendMessageToClient(chartScope, INPUT_HANDLER, payload)
    response = waitOnResponse(messageId, chartScope)
    value = response[RESPONSE]
    s88Set(chartScope, stepScope, key, recipeLocation, value)

def rawQuery(scopeContext, stepProperties):
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    database = getDatabaseName(chartScope)
    sql = getStepProperty(stepProperties, SQL) 
    result = system.db.runQuery(sql, database) # returns a PyDataSet
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
    key = getStepProperty(stepProperties, KEY) 
    s88Set(chartScope, stepScope, key, recipeLocation, result)

def simpleQuery(scopeContext, stepProperties):
    chartScope = scopeContext.getChartScope()
    database = getDatabaseName(chartScope)
    sql = getStepProperty(stepProperties, SQL)
    processedSql = substituteScopeReferences(chartScope, stepProperties, sql)
    dbRows = system.db.runQuery(processedSql, database).getUnderlyingDataset() 
    if dbRows.rowCount == 0:
        getLogger.error('No rows returned for query %s', processedSql)
        return
    simpleQueryProcessRows(chartScope, stepProperties, dbRows)

def simpleQueryProcessRows(scopeContext, stepProperties, dbRows):
    # TODO: use results mode
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    resultsMode = getStepProperty(stepProperties, RESULTS_MODE)
    fetchMode = getStepProperty(stepProperties, FETCH_MODE) 
    createFlag = fetchMode == UPDATE_OR_CREATE
    recipeLocation = getRecipeScope(stepProperties) 
    keyMode = getStepProperty(stepProperties, KEY_MODE) 
    key = getStepProperty(stepProperties, KEY) 
    recipeData = s88Get(chartScope, stepScope, key, recipeLocation)
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
     
def saveData(scopeContext, stepProperties):
    import time
    # extract property values
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
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
        directory = chartScope.get(directory, None)
        if directory == None:
            getLogger().error("directory key " + directory + " not found")
            
    # create timestamp if requested
    if doTimestamp: 
        timestamp = "-" + time.strftime("%Y%m%d%H%M")
    else:
        timestamp = ""
    
    # get the data at the given location
    recipeData = s88Get(chartScope, stepScope, key, recipeLocation)
    if chartScope == None:
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
        sendMessageToClient(chartScope, SAVE_DATA_HANDLER, payload)
        
def printFile(scopeContext, stepProperties):  
    from ils.sfc.common.util import readFile
    # extract property values
    chartScope = scopeContext.getChartScope()
    computer = getStepProperty(stepProperties, COMPUTER) 
    payload = dict()
    if computer == SERVER:
        fileName = getStepProperty(stepProperties, FILENAME) 
        payload[MESSAGE] = readFile(fileName)
    transferStepPropertiesToMessage(stepProperties, payload)
    sendMessageToClient(chartScope, PRINT_FILE_HANDLER, payload)

def printWindow(scopeContext, stepProperties):   
    from ils.sfc.common.util import getProject
    chartScope = scopeContext.getChartScope()
    project = getProject(chartScope)
    payload = dict()
    transferStepPropertiesToMessage(stepProperties, payload)
    sendMessageToClient(project, PRINT_WINDOW_HANDLER, payload)
    
def closeWindow(scopeContext, stepProperties):   
    chartScope = scopeContext.getChartScope()
    payload = dict()
    transferStepPropertiesToMessage(stepProperties, payload)
    payload[INSTANCE_ID] = getChartRunId(chartScope)
    sendMessageToClient(chartScope, CLOSE_WINDOW_HANDLER, payload)

def showWindow(scopeContext, stepProperties):   
    chartScope = scopeContext.getChartScope()
    payload = dict()
    payload[INSTANCE_ID] = getChartRunId(chartScope)
    transferStepPropertiesToMessage(stepProperties, payload)
    security = payload[SECURITY]
    #TODO: implement security

    sendMessageToClient(chartScope, SHOW_WINDOW_HANDLER, payload) 

def reviewData(scopeContext, stepProperties):    
    from system.ils.sfc import getReviewDataConfig
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    stepId = getStepId(stepProperties)
    payload = dict()
    transferStepPropertiesToMessage(stepProperties, payload)
    showAdvice = hasStepProperty(stepProperties, REVIEW_DATA_WITH_ADVICE) 
    payload[CONFIG] = getReviewDataConfig(stepId, showAdvice)
    messageId = sendMessageToClient(chartScope, REVIEW_DATA_HANDLER, payload) 
    
    responseMsg = waitOnResponse(messageId, chartScope)
    responseValue = responseMsg[RESPONSE]
    recipeKey = getStepProperty(stepProperties, BUTTON_KEY)
    recipeLocation = getStepProperty(stepProperties, BUTTON_KEY_LOCATION)
    s88Set(chartScope, stepScope, recipeKey, recipeLocation, responseValue)


