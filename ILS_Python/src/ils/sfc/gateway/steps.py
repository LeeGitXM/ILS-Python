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
    from ils.sfc.gateway.api import getCurrentMessageQueue
    chartScope = scopeContext.getChartScope()
    currentMsgQueue = getCurrentMessageQueue(chartScope)
    message = getStepProperty(stepProperties, MESSAGE)  
    priority = getStepProperty(stepProperties, PRIORITY)  
    database = getDatabaseName(chartScope)
    insert(currentMsgQueue, priority, message, database) 
    
def setQueue(scopeContext, stepProperties):
    '''
    action for java SetQueueStep
    sets the chart's current message queue
    '''
    from ils.sfc.gateway.api import setCurrentMessageQueue
    chartScope = scopeContext.getChartScope()
    queue = getStepProperty(stepProperties, MESSAGE_QUEUE)
    setCurrentMessageQueue(chartScope, queue)

def showQueue(scopeContext, stepProperties):
    '''
    action for java ShowQueueStep
    send a message to the client to show the current message queue
    '''
    from ils.sfc.gateway.api import getCurrentMessageQueue
    chartScope = scopeContext.getChartScope()
    currentMsgQueue = getCurrentMessageQueue(chartScope)
    payload = dict()
    payload[MESSAGE_QUEUE] = currentMsgQueue 
    sendMessageToClient(chartScope, SHOW_QUEUE_HANDLER, payload)

def clearQueue(scopeContext, stepProperties):
    '''
    action for java ClearQueueStep
    delete all messages from the current message queue
    '''
    from ils.sfc.gateway.api import getCurrentMessageQueue
    chartScope = scopeContext.getChartScope()
    currentMsgQueue = getCurrentMessageQueue(chartScope)
    database = getDatabaseName(chartScope)
    clear(currentMsgQueue, database)

def saveQueue(scopeContext, stepProperties):
    from ils.sfc.gateway.api import getCurrentMessageQueue
    from ils.queue.message import save
    chartScope = scopeContext.getChartScope()
    currentMsgQueue = getCurrentMessageQueue(chartScope)
    database = getDatabaseName(chartScope)
    print 'database name', database
    filepath = createFilepath(chartScope, stepProperties)
    save(currentMsgQueue, True, filepath, database)

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
    s88Set(chartScope, stepScope, key, value, recipeLocation)

def cancel(scopeContext, stepProperties):
    ''' Abort the chart execution'''
    from ils.sfc.gateway.api import cancelChart, addControlPanelMessage
    chartScope = scopeContext.getChartScope()
    cancelChart(chartScope)
    addControlPanelMessage(chartScope, "Chart canceled", False)
    
def pause(scopeContext, stepProperties):
    ''' Pause the chart execution'''
    from ils.sfc.gateway.api import pauseChart, addControlPanelMessage
    chartScope = scopeContext.getChartScope()
    pauseChart(chartScope)
    addControlPanelMessage(chartScope, "Chart paused", False)
    
def controlPanelMessage(scopeContext, stepProperties):
    import time
    from ils.sfc.common.sessions import getAckTime
    from ils.sfc.common.sessions import timeOutControlPanelMessageAck
    from ils.sfc.gateway.api import addControlPanelMessage, getCurrentMessageQueue
    chartScope = scopeContext.getChartScope()
    message = getStepProperty(stepProperties, MESSAGE)
    database = getDatabaseName(chartScope)
    ackRequired = getStepProperty(stepProperties, ACK_REQUIRED)
    msgId = addControlPanelMessage(chartScope, message, ackRequired)
    postToQueue = getStepProperty(stepProperties, POST_TO_QUEUE)
    if postToQueue:
        currentMsgQueue = getCurrentMessageQueue(chartScope)
        priority = getStepProperty(stepProperties, PRIORITY)
        insert(currentMsgQueue, priority, message, database)
    if ackRequired:
        timeout = getStepProperty(stepProperties, TIMEOUT)
        timeoutUnit = getStepProperty(stepProperties, TIMEOUT_UNIT)
        timeoutSeconds = getDelaySeconds(timeout, timeoutUnit)
        sleepSeconds = 5
        elapsedSeconds = 0
        startTime = time.time()
        ackTime = None
        # Loop, checking if we see an ack time in the database
        while ackTime == None and (timeoutSeconds > 0 and elapsedSeconds < timeoutSeconds):
            time.sleep(sleepSeconds);
            ackTime = getAckTime(msgId, database)
            elapsedSeconds = time.time() - startTime
        if ackTime == None:
            timeOutControlPanelMessageAck(msgId, database)
        sendUpdateControlPanelMsg(chartScope)
            
def timedDelay(scopeContext, stepProperties):
    from ils.sfc.common.util import createUniqueId, getTimeFactor, callMethod
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
        delay = 0
        
    delayUnit = getStepProperty(stepProperties, DELAY_UNIT)
    delaySeconds = getDelaySeconds(delay, delayUnit)
    timeFactor = getTimeFactor(chartScope)
    delaySeconds = delaySeconds * timeFactor
    startTimeEpochSecs = time.time()
    endTimeEpochSecs = startTimeEpochSecs + delaySeconds
    postNotification = getStepProperty(stepProperties, POST_NOTIFICATION) 
    if postNotification:
        payload = dict()
        payload[CHART_NAME] = chartScope.chartPath
        payload[STEP_NAME] = getStepName(stepProperties)
        payload[CHART_RUN_ID] = getTopChartRunId(chartScope)
        payload[MESSAGE] = str(delay) + ' ' + delayUnit + " remaining."
        payload[ACK_REQUIRED] = False
        payload[WINDOW_ID] = createUniqueId()
        payload[END_TIME] = endTimeEpochSecs
        sendMessageToClient(chartScope, POST_DELAY_NOTIFICATION_HANDLER, payload)
    
    #TODO: checking the real clock time is probably more accurate
    sleepIncrement = 5
    while delaySeconds > 0:
        from ils.sfc.common.constants import _STATUS
        status = stepScope[_STATUS]
        sleep(sleepIncrement)
        delaySeconds = delaySeconds - sleepIncrement
    
    if postNotification:
        sendMessageToClient(chartScope, DELETE_DELAY_NOTIFICATION_HANDLER, payload)
      
def postDelayNotification(scopeContext, stepProperties):
    from ils.sfc.common.util import createUniqueId
    chartScope = scopeContext.getChartScope()
    message = getStepProperty(stepProperties, MESSAGE) 
    payload = dict()
    payload[MESSAGE] = message
    payload[CHART_RUN_ID] = getTopChartRunId(chartScope)
    payload[WINDOW_ID] = createUniqueId()
    sendMessageToClient(chartScope, POST_DELAY_NOTIFICATION_HANDLER, payload)

def deleteDelayNotifications(scopeContext, stepProperties):
    chartScope = scopeContext.getChartScope()
    payload = dict()
    payload[CHART_RUN_ID] = getTopChartRunId(chartScope)
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
    s88Set(chartScope, stepScope, key, value, recipeLocation)

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
    
    s88Set(chartScope, stepScope, key, floatValue, recipeLocation )

def dialogMessage(scopeContext, stepProperties):
    chartScope = scopeContext.getChartScope()
    payload = dict()
    transferStepPropertiesToMessage(stepProperties,payload)
    sendMessageToClient(chartScope, DIALOG_MSG_HANDLER, payload)

def collectData(scopeContext, stepProperties):
    from ils.sfc.common.util import substituteProvider, getTopLevelProperties
    # from ils.sfc.gateway.util import getChartLogger
    from system.util import jsonDecode

    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    logger = getChartLogger(chartScope, stepScope)
    configJson = getStepProperty(stepProperties, CONFIG)
    config = jsonDecode(configJson)
    # config.errorHandling
    for row in config['rows']:
        tagPath = substituteProvider(chartScope, row['tagPath'])
        valueType = row['valueType']
        if valueType == 'current':
            try:
                tagReadResult = system.tag.read(tagPath)
                tagValue = tagReadResult.value
                readOk = tagReadResult.quality.isGood()
            except:
                readOk = False
        else:
            tagPaths = [tagPath]
            if valueType == 'stdDeviation':
                pass
                # tagValues = system.tag.queryTagHistory(tagPaths, intervalHours=row['pastWindow'], ignoreBadQuality=True)
                # how to get std dev??
            else:
                if valueType == 'average':
                    mode = 'Average'
                elif valueType == 'minimum':
                    mode = 'Minimum'
                elif valueType == 'maximum':
                    mode = 'Maximum'
                else:
                    logger.error("Unknown value type" + valueType)
                    mode = 'Average'
                try:
                    tagValues = system.tag.queryTagHistory(tagPaths, returnSize=1, intervalHours=row['pastWindow'], aggregationMode=mode, ignoreBadQuality=True)
                    # ?? how do we tell if there was an error??
                    if tagValues.rowCount == 1:
                        tagValue = tagValues.getValueAt(0,1)
                        readOk = True
                    else:
                        readOk = False
                except:
                    readOk = False
        print 'readOk', readOk
        if readOk:
            s88Set(chartScope, stepScope, row['recipeKey'], tagValue, row['location'])
        else:
            # ?? should we write a None value to recipe data for abort/timeout cases ??
            errorHandling = config['errorHandling']
            if errorHandling == 'abort':
                topRunId = getTopChartRunId(chartScope)
                system.sfc.cancelChart(topRunId)
            elif errorHandling == 'timeout':
                topScope = getTopLevelProperties(chartScope)
                topScope['timeout'] = True
            elif errorHandling == 'defaultValue':
                s88Set(chartScope, stepScope, row['recipeKey'], row['defaultValue'], row['location'] )
                
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
    s88Set(chartScope, stepScope, key, value, recipeLocation )

def rawQuery(scopeContext, stepProperties):
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    database = getDatabaseName(chartScope)
    sql = getStepProperty(stepProperties, SQL) 
    result = system.db.runQuery(sql, database) # returns a PyDataSet
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
    key = getStepProperty(stepProperties, KEY) 
    s88Set(chartScope, stepScope, key, result, recipeLocation)

def simpleQuery(scopeContext, stepProperties):
    from ils.sfc.gateway.recipe import substituteScopeReferences
    chartScope = scopeContext.getChartScope()
    database = getDatabaseName(chartScope)
    sql = getStepProperty(stepProperties, SQL)
    processedSql = substituteScopeReferences(chartScope, stepProperties, sql)
    dbRows = system.db.runQuery(processedSql, database).getUnderlyingDataset() 
    if dbRows.rowCount == 0:
        getLogger.error('No rows returned for query %s', processedSql)
        return
    simpleQueryProcessRows(scopeContext, stepProperties, dbRows)

def simpleQueryProcessRows(scopeContext, stepProperties, dbRows):
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    resultsMode = getStepProperty(stepProperties, RESULTS_MODE) # UPDATE or CREATE
    fetchMode = getStepProperty(stepProperties, FETCH_MODE) # SINGLE or MULTIPLE
    recipeLocation = getRecipeScope(stepProperties) 
    keyMode = getStepProperty(stepProperties, KEY_MODE) # STATIC or DYNAMIC
    key = getStepProperty(stepProperties, KEY) 
    create = (resultsMode == UPDATE_OR_CREATE)
    if keyMode == STATIC: # TODO: fetchMode must be SINGLE
        for rowNum in range(dbRows.rowCount):
            transferSimpleQueryData(chartScope, stepScope, key, recipeLocation, dbRows, rowNum, create)
    elif keyMode == DYNAMIC:
        for rowNum in range(dbRows.rowCount):
            dynamicKey = dbRows.getValueAt(rowNum,key)
            transferSimpleQueryData(chartScope, stepScope, dynamicKey, recipeLocation, dbRows, rowNum, create)

def transferSimpleQueryData(chartScope, stepScope, key, recipeLocation, dbRows, rowNum, create ):
    from system.ils.sfc import s88GetScope, s88ScopeChanged
    from system.util import jsonEncode
    if create:
        recipeScope = s88GetScope(chartScope, stepScope, recipeLocation)
        # create a structure like a deserialized Structure recipe data object
        structData = dict()
        recipeScope[key] = structData
        structData['class'] = 'Structure'
        structData['key'] = key
        valueData = dict()
        copyRowToDict(dbRows, rowNum, valueData, create)
        jsonValue = jsonEncode(valueData)
        print 'key', key, 'jsonValue', jsonValue
        structData['value'] = jsonValue
        s88ScopeChanged(chartScope, recipeScope)     
    else:
        recipeData = s88Get(chartScope, stepScope, key, recipeLocation)
        copyRowToDict(dbRows, rowNum, recipeData, create)
      
    
def saveData(scopeContext, stepProperties):
    from system.ils.sfc import getRecipeDataText
    # extract property values
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
    printFile = getStepProperty(stepProperties, PRINT_FILE) 
    viewFile = getStepProperty(stepProperties, VIEW_FILE) 
        
    # get the data at the given location
    recipeData = getRecipeDataText(chartScope, stepScope, recipeLocation)
    if chartScope == None:
        getLogger.error("data for location " + recipeLocation + " not found")
    
    # write the file
    filepath = createFilepath(chartScope, stepProperties)
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
    chartScope = scopeContext.getChartScope()
    payload = dict()
    transferStepPropertiesToMessage(stepProperties, payload)
    sendMessageToClient(chartScope, PRINT_WINDOW_HANDLER, payload)
    
def closeWindow(scopeContext, stepProperties):   
    chartScope = scopeContext.getChartScope()
    payload = dict()
    transferStepPropertiesToMessage(stepProperties, payload)
    payload[INSTANCE_ID] = getTopChartRunId(chartScope)
    sendMessageToClient(chartScope, 'sfcCloseWindow', payload)

def showWindow(scopeContext, stepProperties):   
    chartScope = scopeContext.getChartScope()
    payload = dict()
    payload[INSTANCE_ID] = getTopChartRunId(chartScope)
    transferStepPropertiesToMessage(stepProperties, payload)
    security = payload[SECURITY]
    #TODO: implement security
    sendMessageToClient(chartScope, 'sfcOpenWindow', payload) 

def reviewData(scopeContext, stepProperties):    
    from system.ils.sfc import getReviewData
    from ils.sfc.common.constants import AUTO_MODE, SEMI_AUTOMATIC
    chartScope = scopeContext.getChartScope() 
    stepScope = scopeContext.getStepScope()
    showAdvice = hasStepProperty(stepProperties, PRIMARY_REVIEW_DATA_WITH_ADVICE)
    if showAdvice:
        primaryConfig = getStepProperty(stepProperties, PRIMARY_REVIEW_DATA_WITH_ADVICE) 
        secondaryConfig = getStepProperty(stepProperties, SECONDARY_REVIEW_DATA_WITH_ADVICE) 
    else:
        primaryConfig = getStepProperty(stepProperties, PRIMARY_REVIEW_DATA)        
        secondaryConfig = getStepProperty(stepProperties, SECONDARY_REVIEW_DATA)        
    payload = dict()
    transferStepPropertiesToMessage(stepProperties, payload)
    payload[PRIMARY_CONFIG] = getReviewData(chartScope, stepScope, primaryConfig, showAdvice)
    payload[SECONDARY_CONFIG] = getReviewData(chartScope, stepScope, secondaryConfig, showAdvice)
    payload[INSTANCE_ID] = getTopChartRunId(chartScope)
    messageId = sendMessageToClient(chartScope, REVIEW_DATA_HANDLER, payload) 
    
    responseMsg = waitOnResponse(messageId, chartScope)
    responseValue = responseMsg[RESPONSE]
    recipeKey = getStepProperty(stepProperties, BUTTON_KEY)
    recipeLocation = getStepProperty(stepProperties, BUTTON_KEY_LOCATION)
    s88Set(chartScope, stepScope, recipeKey, responseValue, recipeLocation )

def confirmControllers(scopeContext, stepProperties): 
    pass   

def writeOutput(scopeContext, stepProperties): 
    pass   

def monitorPV(scopeContext, stepProperties): 
    pass   

def monitorDownload(scopeContext, stepProperties): 
    pass   



