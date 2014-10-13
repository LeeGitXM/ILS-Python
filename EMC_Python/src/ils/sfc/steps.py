'''
Methods that are associated with particular SFC step types

Created on Sep 30, 2014

@author: rforbes
'''
from ils.sfc.util import * 
from system.ils.sfc import *
from ils.queue.message import insert
from ils.queue.message import clear
from system.sfc import cancelChart
from system.sfc import pauseChart
from time import sleep

def queueInsert(chartProperties, stepProperties):
    '''
    action for java QueueMessageStep
    queues the step's message
    '''
    print('line 1')
    currentMsgQueue = s88Get(None, chartProperties, MESSAGE_QUEUE, OPERATION) 
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
    s88Set(stepName, chartProperties, MESSAGE_QUEUE, queue, recipeLocation)

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
    s88Set(stepName, chartProperties, key, value, recipeLocation)

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
      
def postDelayNotification():
    pass

def deleteDelayNotification():
    pass
  