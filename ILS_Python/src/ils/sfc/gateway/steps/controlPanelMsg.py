'''
Created on Dec 16, 2015

@author: rforbes
'''

def activate(scopeContext, step):
    import time
    from ils.sfc.gateway.util import getStepProperty, getDelaySeconds, handleUnexpectedGatewayError
    from system.ils.sfc.common.Constants import MESSAGE, ACK_REQUIRED, POST_TO_QUEUE, PRIORITY, TIMEOUT, TIMEOUT_UNIT
    from ils.queue.message import insert
    from ils.sfc.gateway.recipe import substituteScopeReferences
    from ils.sfc.common.cpmessage import getAckTime, timeOutControlPanelMessageAck
    from ils.sfc.gateway.api import getDatabaseName, addControlPanelMessage, getCurrentMessageQueue, getChartLogger
    try:
        chartScope = scopeContext.getChartScope()
        stepScope = scopeContext.getStepScope()
        stepProperties = step.getProperties();
        chartLogger = getChartLogger(chartScope)
        message = getStepProperty(stepProperties, MESSAGE)
        message = substituteScopeReferences(chartScope, stepScope, message)
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
            # sendUpdateControlPanelMsg(chartScope)
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in controlPanelMsg.py', chartLogger)
