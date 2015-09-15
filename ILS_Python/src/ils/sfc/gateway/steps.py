
'''
Methods that are associated with particular SFC step types, matching
one-to-one with step calls in the Java class JythonCall

Created on Sep 30, 2014

@author: rforbes
'''

#from com.ils.sfc.common import IlsSfcNames
from ils.sfc.gateway.api import s88Set, s88Get, s88SetWithUnits
from ils.common.units import Unit
from ils.sfc.gateway.util import * 
from ils.sfc.common.constants import *
from ils.sfc.common.constants import _STATUS

from ils.sfc.gateway.api import getDatabaseName, sendMessageToClient, getChartLogger

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
        handleUnexpectedGatewayError(scopeContext.getChartScope(), msg)
         
def queueInsert(scopeContext, stepProperties):
    '''
    action for java QueueMessageStep
    queues the step's message
    '''
    from ils.sfc.gateway.api import getCurrentMessageQueue
    from ils.sfc.gateway.recipe import substituteScopeReferences

    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    currentMsgQueue = getCurrentMessageQueue(chartScope)
    message = getStepProperty(stepProperties, MESSAGE)  
    message = substituteScopeReferences(chartScope, stepScope, message)
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
    filepath = createFilepath(chartScope, stepProperties, False)
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
    value = waitOnResponse(messageId, chartScope)
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
    from ils.sfc.common.util import createUniqueId, callMethod
    from ils.sfc.gateway.api import getTimeFactor
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
        
        # Handle Cancel/Pause
        status = stepScope[_STATUS]
        if status == CANCEL:
            return
        elif status == PAUSE:
            sleep(sleepIncrement)
            continue
        
        delaySeconds = delaySeconds - sleepIncrement
        sleep(sleepIncrement)
    
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
    value = waitOnResponse(messageId, chartScope)
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
        responseValue = waitOnResponse(messageId, chartScope)
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
    from system.ils.sfc.common.Constants import COLLECT_DATA_CONFIG 
    from ils.sfc.common.util import substituteProvider
    from ils.sfc.gateway.util import getTopLevelProperties
    # from ils.sfc.gateway.util import getChartLogger
    from system.util import jsonDecode
    from ils.sfc.gateway.util import standardDeviation

    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    logger = getChartLogger(chartScope)
    logger.info("Executing a collect data block")
    configJson = getStepProperty(stepProperties, COLLECT_DATA_CONFIG)
    config = jsonDecode(configJson)
    logger.trace("Block Configuration: %s" % (str(config)))

    # config.errorHandling
    for row in config['rows']:
        tagPath = substituteProvider(chartScope, row['tagPath'])
        valueType = row['valueType']
        logger.info("Collecting %s from %s" % (str(valueType), str(tagPath)))
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
                logger.trace("calling queryTagHistory() to fetch the dataset for calculating the standard deviation") 
                tagValues = system.tag.queryTagHistory(tagPaths, rangeHours=row['pastWindow'], ignoreBadQuality=True)
                logger.trace("Calculating the standard deviation...")
                tagValue = standardDeviation(tagValues, 1)
                logger.trace("The standard deviation is: %s" % (tagValue))
                readOk = True
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
                    logger.trace("calling queryTagHistory() - rangeMinutes: %s, aggregationMode: %s" % (str(row['pastWindow']), mode))
                    tagValues = system.tag.queryTagHistory(tagPaths, returnSize=1, rangeMinutes=row['pastWindow'], aggregationMode=mode, ignoreBadQuality=True)
                    # ?? how do we tell if there was an error??
                    if tagValues.rowCount == 1:
                        tagValue = tagValues.getValueAt(0,1)
                        print 'mode', mode, 'value', tagValue
                        logger.trace("Successfully returned: %s" )
                        readOk = True
                    else:
                        readOk = False
                except:
                    readOk = False
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
    value = waitOnResponse(messageId, chartScope)
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
    logger = getChartLogger(chartScope)
    database = getDatabaseName(chartScope)
    sql = getStepProperty(stepProperties, SQL)
    processedSql = substituteScopeReferences(chartScope, stepProperties, sql)
    dbRows = system.db.runQuery(processedSql, database).getUnderlyingDataset() 
    if dbRows.rowCount == 0:
        logger.error('No rows returned for query %s', processedSql)
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
        # print 'key', key, 'jsonValue', jsonValue
        structData['value'] = jsonValue
        s88ScopeChanged(chartScope, recipeScope)     
    else:
        recipeData = s88Get(chartScope, stepScope, key, recipeLocation)
        copyRowToDict(dbRows, rowNum, recipeData, create)
      
    
def saveData(scopeContext, stepProperties):
    from system.ils.sfc import getRecipeDataText
    # extract property values
    chartScope = scopeContext.getChartScope()
    logger = getChartLogger(chartScope)
    stepScope = scopeContext.getStepScope()
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
    printFile = getStepProperty(stepProperties, PRINT_FILE) 
    viewFile = getStepProperty(stepProperties, VIEW_FILE) 
        
    # get the data at the given location
    recipeData = getRecipeDataText(chartScope, stepScope, recipeLocation)
    if chartScope == None:
        logger.error("data for location " + recipeLocation + " not found")
    
    # write the file
    filepath = createFilepath(chartScope, stepProperties, True)
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
    sendMessageToClient(chartScope, 'sfcCloseWindow', payload)

def showWindow(scopeContext, stepProperties):   
    chartScope = scopeContext.getChartScope()
    payload = dict()
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
    messageId = sendMessageToClient(chartScope, REVIEW_DATA_HANDLER, payload) 
    
    responseValue = waitOnResponse(messageId, chartScope)
    recipeKey = getStepProperty(stepProperties, BUTTON_KEY)
    recipeLocation = getStepProperty(stepProperties, BUTTON_KEY_LOCATION)
    s88Set(chartScope, stepScope, recipeKey, responseValue, recipeLocation )

def confirmControllers(scopeContext, stepProperties): 
    pass   

def writeOutput(scopeContext, stepProperties): 
    from system.ils.sfc.common.Constants import WRITE_OUTPUT_CONFIG, WRITE_CONFIRMED, \
    DOWNLOAD_STATUS, STEP_TIMESTAMP, STEP_TIME, TIMING, DOWNLOAD, VERBOSE, VALUE_TYPE, \
    SETPOINT, SUCCESS, PENDING, TARGET_VALUE
    from ils.sfc.common.constants import SLEEP_INCREMENT
    import time
    from ils.sfc.common.util import getMinutesSince, formatTime
    from ils.sfc.gateway.api import getIsolationMode
    from ils.sfc.gateway.util import getChartLogger, checkForCancelOrPause
    from system.ils.sfc import getWriteOutputConfig
    from ils.sfc.gateway.downloads import handleTimer, writeOutput, waitForTimerStart
    from ils.sfc.gateway.recipe import RecipeData
    from ils.sfc.gateway.abstractSfcIO import AbstractSfcIO
    
    chartScope = scopeContext.getChartScope() 
    stepScope = scopeContext.getStepScope()
    logger = getChartLogger(chartScope)
    logger.info("Executing a Write Output block")
    verbose = getStepProperty(stepProperties, VERBOSE)
    configJson = getStepProperty(stepProperties, WRITE_OUTPUT_CONFIG)
    config = getWriteOutputConfig(configJson)
    logger.trace("Block Configuration: %s" % (str(config)))
    outputRecipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION)
    logger.trace("Using recipe location: %s" % (outputRecipeLocation))

    # filter out disabled rows:
    downloadRows = []
    for row in config.rows:
        row.outputRD = RecipeData(chartScope, stepScope, outputRecipeLocation, row.key)
        download = row.outputRD.get(DOWNLOAD)
        if download:
            downloadRows.append(row)
    
    # do the timer logic, if there are rows that need timing
    timerNeeded = False
    for row in downloadRows:
        row.timingMinutes = row.outputRD.get(TIMING)
        if row.timingMinutes > 0.:
            timerNeeded = True
    logger.trace("Timer is needed: %s" % (str(timerNeeded)))
    
    if timerNeeded:
        handleTimer(chartScope, stepScope, stepProperties)
        # wait until the timer starts
        timerStart = waitForTimerStart(chartScope, stepScope, stepProperties, logger)
        logger.trace("The timer start is: %s" % (str(timerStart)))
        
        if timerStart == None:
            logger.info("The chart has been canceled")
            return
            
    # separate rows into timed rows and those that are written after timed rows:
    immediateRows = []
    timedRows = []
    finalRows = []
             
    # initialize row data and separate into immediate/timed/final:
    logger.trace("Initializing data and classifying outputs...")
    for row in downloadRows:
        row.written = False
         
        # clear out the dynamic values in recipe data:
        row.outputRD.set(DOWNLOAD_STATUS, None)
        # print 'setting output download status to NONE'
        # STEP_TIMESTAMP and STEP_TIME will be set below
        row.outputRD.set(WRITE_CONFIRMED, None)
        
        # cache some frequently used values from recipe data:
        row.value = row.outputRD.get(VALUE)
        row.tagPath = row.outputRD.get(TAG_PATH)
            
        # classify the rows
        timingIsEventDriven = False
        if row.timingMinutes == 0.:
            immediateRows.append(row)
        elif row.timingMinutes >= 1000.:
            finalRows.append(row)
            timingIsEventDriven = True
        else:
            timedRows.append(row)
  
        # write the absolute step timing back to recipe data
        if timingIsEventDriven:
            row.outputRD.set(STEP_TIMESTAMP, '')
            # I don't want to propagate the magic 1000 value, so we use None
            # to signal an event-driven step
            row.outputRD.set(STEP_TIME, None)
        else:
            absTiming = timerStart + row.timingMinutes * 60.
            timestamp = formatTime(absTiming)
            row.outputRD.set(STEP_TIMESTAMP, timestamp)
            row.outputRD.set(STEP_TIME, absTiming)

        isolationMode = getIsolationMode(chartScope)
        row.io = AbstractSfcIO.getIO(row.tagPath, isolationMode) 
        
    logger.trace("Starting immediate writes")
    for row in immediateRows:
        writeOutput(chartScope, row, verbose, logger)
                     
    logger.trace("Starting timed writes")
    writesPending = True       
    while writesPending:
        writesPending = False 
        
        elapsedMinutes = getMinutesSince(timerStart)
        for row in timedRows:
            if not row.written:
                logger.trace("checking output step %s; %.2f elapsed %.2f" % (row.key, row.timingMinutes, elapsedMinutes))
                if elapsedMinutes >= row.timingMinutes:
                    writeOutput(chartScope, row, verbose, logger)
                else:
                    writesPending = True
         
        if writesPending:
            time.sleep(SLEEP_INCREMENT)
 
        if checkForCancelOrPause(stepScope, logger):
            return
       
    logger.trace("Starting final writes")
    for row in finalRows:
        absTiming = time.time()
        timestamp = formatTime(absTiming)
        row.outputRD.set(STEP_TIMESTAMP, timestamp)
        row.outputRD.set(STEP_TIME, absTiming)
        writeOutput(chartScope, row, verbose, logger)    

    logger.info("Write output block finished!")
    #Note: write confirmations are on a separate thread and will write the result
    # directly to recipe data
        
def monitorPV(scopeContext, stepProperties):
    '''see the G2 procedures S88-RECIPE-INPUT-DATA__S88-MONITOR-PV.txt and 
    S88-RECIPE-OUTPUT-DATA__S88-MONITOR-PV.txt'''
    from system.ils.sfc.common.Constants import PV_MONITOR_CONFIG, SETPOINT, MONITOR, \
    NUMBER_OF_TIMEOUTS, IMMEDIATE, ABS, PCT, LOW, HIGH, CLASS, DOWNLOAD_STATUS, STEP_TIME, \
    HIGH_LOW, TIMER_LOCATION, DATA_LOCATION, PV_MONITOR_STATUS, PV_MONITOR_ACTIVE, PV_VALUE, \
    SUCCESS, WARNING, MONITORING, NOT_PERSISTENT, NOT_CONSISTENT, ERROR, WAIT
    from ils.sfc.common.constants import SLEEP_INCREMENT
    import time
    from ils.sfc.common.util import getMinutesSince
    from ils.sfc.gateway.api import getIsolationMode
    from system.ils.sfc import getPVMonitorConfig
    from ils.sfc.gateway.downloads import handleTimer
    from ils.sfc.gateway.monitoring import getMonitoringMgr
    from ils.sfc.gateway.recipe import RecipeData
    from ils.sfc.gateway.abstractSfcIO import AbstractSfcIO
    
    # general initialization:
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    logger = getChartLogger(chartScope)
    stepScope[NUMBER_OF_TIMEOUTS] = 0
    handleTimer(chartScope, stepScope, stepProperties)
    dataLocation = getStepProperty(stepProperties, DATA_LOCATION)
    durationStrategy = getStepProperty(stepProperties, STRATEGY)
    if durationStrategy == STATIC:
        timeLimitMin = getStepProperty(stepProperties, VALUE) 
    else:
        durationLocation = getStepProperty(stepProperties, RECIPE_LOCATION)
        durationKey = getStepProperty(stepProperties, KEY)
        durationRD = RecipeData(chartScope, stepScope, durationLocation, durationKey)
        timeLimitMin = durationRD.get(VALUE)
        
    configJson =  getStepProperty(stepProperties, PV_MONITOR_CONFIG)
    config = getPVMonitorConfig(configJson)

    maxPersistence = 0
    # initialize each input:
    for configRow in config.rows:
        configRow.status = MONITORING
        configRow.ioRD = RecipeData(chartScope, stepScope, dataLocation, configRow.pvKey)
        configRow.ioRD.set(PV_MONITOR_STATUS, MONITORING)
        configRow.ioRD.set(PV_MONITOR_ACTIVE, True)
        configRow.ioRD.set(PV_VALUE, None)
        dataType = configRow.ioRD.get(CLASS)
        configRow.isOutput = (dataType == 'Output')
        configRow.isDownloaded = False
        configRow.persistenceOK = False
        configRow.inToleranceTime = 0
        configRow.outToleranceTime = 0
        if configRow.persistence > maxPersistence:
            maxPersistence = configRow.persistence
            
        # we assume the target value won't change, so we get it once:
        if configRow.targetType == SETPOINT:
            configRow.targetValue = s88Get(chartScope, stepScope, configRow.targetNameIdOrValue + '/value', dataLocation)
        elif configRow.targetType == VALUE:
            configRow.targetValue = configRow.targetNameIdOrValue
        elif configRow.targetType == TAG:
            qualVal = system.tag.read(configRow.targetNameIdOrValue)
            configRow.targetValue = qualVal.value
        elif configRow.targetType == RECIPE:
            configRow.targetValue = s88Get(chartScope, stepScope, configRow.targetNameIdOrValue, dataLocation)           
        
        if configRow.toleranceType == ABS:
            tolerance = configRow.tolerance
        elif configRow.toleranceType == PCT:
            tolerance = configRow.targetValue * .01 * configRow.tolerance               

        if configRow.limits == LOW:
            configRow.lowLimit = configRow.targetValue - tolerance
            configRow.highLimit = configRow.targetValue
        elif configRow.limits == HIGH:
            configRow.lowLimit = configRow.targetValue
            configRow.highLimit = configRow.targetValue + tolerance
        elif configRow.limits == HIGH_LOW:
            configRow.lowLimit = configRow.targetValue - tolerance
            configRow.highLimit = configRow.targetValue + tolerance
        
        tagPath = configRow.ioRD.get(TAG_PATH)
        configRow.io = AbstractSfcIO.getIO(tagPath, getIsolationMode(chartScope))
        
    # Monitor for the specified period, possibly extended by persistence time
    startTime = time.time()
    elapsedMinutes = 0    
    extendedDuration = timeLimitMin + maxPersistence # extra time allowed for persistence checks
    persistencePending = False
    while (elapsedMinutes < timeLimitMin) or (persistencePending and elapsedMinutes < extendedDuration):
        
        if checkForCancelOrPause(stepScope, logger):
            return

        persistencePending = False
        for configRow in config.rows:
            # print ''
            # print 'PV monitor', configRow.pvKey  
            
            if not configRow.enabled:
                continue;
            
            #TODO: how are we supposed to know about a download unless we have an Output??
            if configRow.isOutput and not configRow.isDownloaded:
                downloadStatus = configRow.ioRD.get(DOWNLOAD_STATUS)
                configRow.isDownloaded = (downloadStatus == SUCCESS)
                if configRow.isDownloaded:
                    configRow.downloadTime = configRow.ioRD.get(STEP_TIME)
            # print 'configRow.download', configRow.download,  'configRow.isDownloaded', configRow.isDownloaded   
            if configRow.download == WAIT and not configRow.isDownloaded:
                # print '   skipping; not downloaded'
                continue
             
            presentValue = configRow.io.getCurrentValue()
            # ? Not sure why we are writing this to Recipe Data--the monitoring
            # logic has full access to the controller, doesn't it?
            configRow.ioRD.set(PV_VALUE, presentValue)
           
            # if we're just reading for display purposes, we're done with this pvInput:
            if configRow.strategy != MONITOR:
                continue
            
            # ERROR is a terminal state
            # ?? should SUCCESS be terminal as well?
            if configRow.status == ERROR:
                continue
            
            # check persistence:
            inToleranceNow = presentValue >= configRow.lowLimit and presentValue <= configRow.highLimit
            if inToleranceNow:
                configRow.outToleranceTime = 0
                isConsistentlyOutOfTolerance = False
                if configRow.inToleranceTime != 0:
                    isPersistent = getMinutesSince(configRow.inToleranceTime) > configRow.persistence                    
                else:
                    isPersistent = False
                    configRow.inToleranceTime = time.time()   
            else:
                configRow.inToleranceTime = 0
                isPersistent = False
                if configRow.outToleranceTime != 0:
                    isConsistentlyOutOfTolerance = getMinutesSince(configRow.outToleranceTime) > configRow.consistency
                else:
                    isConsistentlyOutOfTolerance = False
                    configRow.outToleranceTime = time.time()  
                    
            # check dead time                 
            if configRow.download == IMMEDIATE:
                referenceTime = startTime
            else:
                referenceTime = configRow.downloadTime
            # print 'minutes since reference', getMinutesSince(referenceTime)
            deadTimeExceeded = getMinutesSince(referenceTime) > configRow.deadTime 
            # print '   pv', presentValue, 'target', configRow.targetValue, 'low limit',  configRow.lowLimit, 'high limit', configRow.highLimit   
            # print '   inToleranceTime', configRow.inToleranceTime, 'outToleranceTime', configRow.outToleranceTime, 'deadTime',configRow.deadTime  
            # SUCCESS, WARNING, MONITORING, NOT_PERSISTENT, NOT_CONSISTENT, OUT_OF_RANGE, ERROR, TIMEOUT
            if inToleranceNow:
                if isPersistent:
                    configRow.status = SUCCESS
                else:
                    configRow.status = NOT_PERSISTENT
                    persistencePending = True
            else: # out of tolerance
                if deadTimeExceeded:
                    # print '   setting error status'
                    configRow.status = ERROR
                elif isConsistentlyOutOfTolerance:
                    configRow.status = WARNING
                else:
                    configRow.status = NOT_CONSISTENT
                        
            configRow.ioRD.set(PV_MONITOR_STATUS, configRow.status)
            # print '   status ', configRow.status    
        time.sleep(SLEEP_INCREMENT)
        elapsedMinutes =  getMinutesSince(startTime)
        
    numTimeouts = 0
    for configRow in config.rows:
        if configRow.status == ERROR:
            ++numTimeouts
            configRow.status = TIMEOUT
            configRow.ioRD.set(PV_MONITOR_STATUS, configRow.status)
        configRow.ioRD.set(PV_MONITOR_ACTIVE, False)
    stepScope[NUMBER_OF_TIMEOUTS] = numTimeouts
      
def monitorDownload(scopeContext, stepProperties): 
    from system.ils.sfc.common.Constants import MONITOR_DOWNLOADS_CONFIG, DATA_ID
    from system.ils.sfc import getMonitorDownloadsConfig
    from ils.sfc.gateway.downloads import handleTimer
    from ils.sfc.gateway.monitoring import createMonitoringMgr
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    logger = getChartLogger(chartScope)
    timer, timerAttribute = handleTimer(chartScope, stepScope, stepProperties)
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION)
    configJson = getStepProperty(stepProperties, MONITOR_DOWNLOADS_CONFIG)
    monitorDownloadsConfig = getMonitorDownloadsConfig(configJson)
    mgr = createMonitoringMgr(chartScope, stepScope, recipeLocation, timer, timerAttribute, monitorDownloadsConfig, logger)
    payload = dict()
    payload[DATA_ID] = mgr.getTimerId()
    transferStepPropertiesToMessage(stepProperties, payload)
    sendMessageToClient(chartScope, 'sfcMonitorDownloads', payload)             

def manualDataEntry(scopeContext, stepProperties):    
    from system.ils.sfc.common.Constants import MANUAL_DATA_CONFIG, AUTO_MODE, AUTOMATIC
    from system.ils.sfc import getManualDataEntryConfig 
    from system.dataset import toDataSet
    from ils.sfc.common.util import isEmpty
    from ils.sfc.gateway.api import s88GetType, parseValue
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    #logger = getChartLogger(chartScope)
    autoMode = getStepProperty(stepProperties, AUTO_MODE)
    configJson = getStepProperty(stepProperties, MANUAL_DATA_CONFIG)
    config = getManualDataEntryConfig(configJson)
    if autoMode == AUTOMATIC:
        for row in config.rows:
            s88Set(chartScope, stepScope, row.key, row.defaultValue, row.destination)
    else:
        header = ['Description', 'Value', 'Units', 'Low Limit', 'High Limit', 'Key', 'Destination', 'Type']    
        rows = []
        # Note: apparently the IA toDataSet method tries to coerce all column values to
        # the same type and throws an error if that is not possible. Since we potentially
        # have a mixture of float and string values, we convert them all to strings:
        for row in config.rows:
            tagType = s88GetType(chartScope, stepScope, row.key, row.destination)
            rows.append([row.prompt, str(row.defaultValue), row.units, row.lowLimit, row.highLimit, row.key, row.destination, tagType])
        dataset = toDataSet(header, rows)
        payload = dict()
        transferStepPropertiesToMessage(stepProperties, payload)
        payload[DATA] = dataset
        messageId = sendMessageToClient(chartScope, 'sfcManualDataEntry', payload)             
        response = waitOnResponse(messageId, chartScope)
        returnDataset = response[DATA]
        # Note: all values are returned as strings; we depend on s88Set to make the conversion
        for row in range(returnDataset.rowCount):
            strValue = returnDataset.getValueAt(row, 1)
            units = returnDataset.getValueAt(row, 2)
            key = returnDataset.getValueAt(row, 5)
            destination = returnDataset.getValueAt(row, 6)
            valueType = returnDataset.getValueAt(row, 7)
            print 'key', key, 'valueType', valueType, 'units', units, 'isEmpty', isEmpty(units)
            value = parseValue(strValue, valueType)
            if isEmpty(units):
                s88Set(chartScope, stepScope, key, value, destination)
            else:
                print 'units', units, ''
                s88SetWithUnits(chartScope, stepScope, key, value, destination, units)
