'''
Methods that are associated with particular SFC step types

Created on Sep 30, 2014

@author: rforbes
'''
#from com.ils.sfc.common import IlsSfcNames
from ils.sfc.util import * 
from system.ils.sfc import * # this maps Java classes
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

def abort(chartProperties, stepProperties):
    ''' Abort the chart execution'''
    chartId = chartProperties[INSTANCE_ID]
    print chartId.getClass().getName()
    cancelChart(str(chartId))
    sendControlPanelMessage(chartProperties, stepProperties)
    
def pause(chartProperties, stepProperties):
    ''' Pause the chart execution'''
    chartId = chartProperties[INSTANCE_ID]
    pauseChart(str(chartId))
    sendControlPanelMessage(chartProperties, stepProperties)
    
def controlPanelMessage(chartProperties, stepProperties):
    sendControlPanelMessage(chartProperties, stepProperties)
    
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
    s88Set(chartProperties, stepProperties, key, value, recipeLocation, False)

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
    
    messageId = sendMessage(project, LIMITED_INPUT_HANDLER, payload) 
    
    response = waitOnResponse(messageId, chartProperties)
    value = response[RESPONSE]
    s88Set(chartProperties, stepProperties, key, value, recipeLocation, False)

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
    s88Set(chartProperties, stepProperties, key, value, recipeLocation, False)
    
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
     
def debugProperties(chartProperties, stepProperties):
    project = chartProperties[PROJECT];
    # printObj(chartProperties, 0)
    payload = dict()
    properties = dict()
    for key in chartProperties:
        properties[key] = chartProperties[key]
    payload['properties'] = properties
    sendMessage(project, 'sfcDebugProperties', payload)