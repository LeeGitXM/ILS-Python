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
    currentMsgQueue = s88Get(None, chartProperties, MESSAGE_ID, OPERATION)
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
    stepName = getStepProperty(stepProperties, NAME) 
    s88Set(stepName, chartProperties, MESSAGE_QUEUE, queue, recipeLocation, True)

def showQueue(chartProperties, stepProperties):
    '''
    action for java ShowQueueStep
    send a message to the client to show the current message queue
    '''
    currentMsgQueue = s88Get(None, chartProperties, MESSAGE_QUEUE, OPERATION) 
    payload = dict()
    payload[QUEUE] = currentMsgQueue 
    project = chartProperties[PROJECT];
    sendMessage(project, SHOW_QUEUE_HANDLER, payload)

def clearQueue(chartProperties, stepProperties):
    '''
    action for java ClearQueueStep
    delete all messages from the current message queue
    '''
    currentMsgQueue = s88Get(None, chartProperties, MESSAGE_QUEUE, OPERATION) 
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
    stepName = getStepProperty(stepProperties, NAME) 
    s88Set(stepName, chartProperties, key, value, recipeLocation, False)

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
    postNotification = getStepProperty(stepProperties, POST_NOTIFICATION) 
    delay = getStepProperty(stepProperties, DELAY) 
    delayUnit = getStepProperty(stepProperties, DELAY_UNIT)
    delaySeconds = Unit.convert(delayUnit, SECOND, delay)
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
    stepName = getStepProperty(stepProperties, NAME) 

    choices = s88Get(stepName, chartProperties, choicesKey, choicesRecipeLocation)
    
    # send message
    payload = dict()
    payload[PROMPT] = prompt
    payload[CHOICES] = choices
    
    messageId = sendMessage(project, SELECT_INPUT_HANDLER, payload) 
    
    response = waitOnResponse(messageId, chartProperties)
    value = response[RESPONSE]
    s88Set(stepName, chartProperties, key, value, recipeLocation, False)

def getLimitedInput(chartProperties, stepProperties):
    project = chartProperties[PROJECT];
    prompt = getStepProperty(stepProperties, PROMPT) 
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
    key = getStepProperty(stepProperties, KEY) 
    stepName = getStepProperty(stepProperties, NAME) 
    minimumValue = getStepProperty(stepProperties, MINIMUM_VALUE)
    maximumValue = getStepProperty(stepProperties, MAXIMUM_VALUE) 
    
    payload = dict()
    payload[PROMPT] = prompt
    payload[MINIMUM_VALUE] = minimumValue
    payload[MAXIMUM_VALUE] = maximumValue
    
    messageId = sendMessage(project, LIMITED_INPUT_HANDLER, payload) 
    
    response = waitOnResponse(messageId, chartProperties)
    value = response[RESPONSE]
    s88Set(stepName, chartProperties, key, value, recipeLocation, False)

def dialogMessage(chartProperties, stepProperties):
    payload = dict()
    transferStepPropertiesToMessage(stepProperties,payload)
    project = chartProperties[PROJECT];
    sendMessage(project, DIALOG_MSG_HANDLER, payload)


def collectData(chartProperties, stepProperties):
    tagPath = getStepProperty(stepProperties, TAG_PATH)
    stepName = getStepProperty(stepProperties, NAME) 
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
    key = getStepProperty(stepProperties, KEY) 
    value = system.tag.read(tagPath)
    s88Set(stepName, chartProperties, key, value, recipeLocation, False)
    
def getInput(chartProperties, stepProperties):
    project = chartProperties[PROJECT];
    prompt = getStepProperty(stepProperties, PROMPT) 
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
    key = getStepProperty(stepProperties, KEY) 
    stepName = getStepProperty(stepProperties, NAME) 
   
    payload = dict()
    payload[PROMPT] = prompt
    
    messageId = sendMessage(project, INPUT_HANDLER, payload)
    
    response = waitOnResponse(messageId, chartProperties)
    value = response[RESPONSE]
    s88Set(stepName, chartProperties, key, value, recipeLocation, False)

def rawQuery(chartProperties, stepProperties):
    database = getStepProperty(stepProperties, DATABASE) 
    sql = getStepProperty(stepProperties, SQL) 
    result = system.db.runQuery(sql, database) # returns a PyDataSet
    stepName = getStepProperty(stepProperties, NAME) 
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
    key = getStepProperty(stepProperties, KEY) 
    s88Set(stepName, chartProperties, key, result, recipeLocation, False)

def simpleQuery(chartProperties, stepProperties):
    database = getStepProperty(stepProperties, DATABASE) 
    sql = getStepProperty(stepProperties, SQL) 
    processedSql = substituteScopeReferences(chartProperties, stepProperties, sql)
    resultsMode = getStepProperty(stepProperties, RESULTS_MODE) 
    fetchMode = getStepProperty(stepProperties, FETCH_MODE) 
    stepName = getStepProperty(stepProperties, NAME) 
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
    keyMode = getStepProperty(stepProperties, KEY_MODE) 
    key = getStepProperty(stepProperties, KEY) 
    dbRows = system.db.runQuery(processedSql, database) 
    if keyMode == STATIC: # fetchMode must be SINGLE
        recipeData = s88Get(stepName, chartProperties, key, recipeLocation)
        rowData = dbRows[0]
        copyData(rowData, recipeData)
    elif keyMode == DYNAMIC:
        key = s88Get(stepName, chartProperties, key, recipeLocation)
        recipeDataByKey = dict() # ??? extract and index
        if fetchMode == MULTIPLE:# returns a PyDataSet
            for row in dbRows:
                if row.get(key, None) == key:
                    recipeData = recipeDataByKey.get(key, None)
                    if recipeData != None:
                        for colKey in row.keys():
                            recipeData[colKey] = row[colKey]

def copyData(fromDict, toDict):
    for key in fromDict.keys:
        toDict[key] = fromDict[key]
    