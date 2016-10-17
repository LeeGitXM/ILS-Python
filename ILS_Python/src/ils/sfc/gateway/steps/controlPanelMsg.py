'''
Created on Dec 16, 2015

@author: rforbes
'''
import system

def activate(scopeContext, stepProperties, state):
    import time
    from ils.sfc.gateway.util import getStepProperty, handleUnexpectedGatewayError, getTimeoutTime, logStepDeactivated
    from system.ils.sfc.common.Constants import DEACTIVATED, ACTIVATED, PAUSED, CANCELLED
    from system.ils.sfc.common.Constants import MESSAGE, ACK_REQUIRED, POST_TO_QUEUE, PRIORITY
    from ils.sfc.common.constants import WAITING_FOR_REPLY, TIMEOUT_TIME, MESSAGE_ID, TIMED_OUT
    from ils.queue.message import insert
    from ils.sfc.gateway.recipe import substituteScopeReferences
    from ils.sfc.gateway.api import getDatabaseName, addControlPanelMessage, getCurrentMessageQueue, getChartLogger 

    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    logger = getChartLogger(chartScope)

    if state == DEACTIVATED:
        # no cleanup is needed
        logStepDeactivated(chartScope, stepProperties)
        return False
    
    try:
        database = getDatabaseName(chartScope)
        
        workDone = False
        waitingForReply = stepScope.get(WAITING_FOR_REPLY, False);
        
        if not waitingForReply:
            message = getStepProperty(stepProperties, MESSAGE)
            logger.trace("The untranslated message is <%s>..." % (message))
            message = substituteScopeReferences(chartScope, stepScope, message)
            logger.trace("...the translated message is <%s>" % (message))
            ackRequired = getStepProperty(stepProperties, ACK_REQUIRED)
            priority = getStepProperty(stepProperties, PRIORITY)
            msgId = addControlPanelMessage(chartScope, message, priority, ackRequired)
            stepScope[MESSAGE_ID] = msgId
            postToQueue = getStepProperty(stepProperties, POST_TO_QUEUE)
            if postToQueue:
                logger.trace("Adding control panel message to the queue")
                currentMsgQueue = getCurrentMessageQueue(chartScope)   
                insert(currentMsgQueue, priority, message, database)
            if ackRequired:
                logger.trace("Setting ACK flag")
                stepScope[WAITING_FOR_REPLY] = True
                timeoutTime = getTimeoutTime(chartScope, stepProperties)
                stepScope[TIMEOUT_TIME] = timeoutTime
            else:
                workDone = True
        else:
            logger.trace("Checking if the message has been acknowledged")
            timeoutTime = stepScope[TIMEOUT_TIME]
            msgId = stepScope[MESSAGE_ID]

            SQL = "select count(*) from SfcControlPanelMessage where id = '%s'" % msgId
            rows = system.db.runScalarQuery(SQL, database)

            if rows == 0:
                stepScope[TIMED_OUT] = False
                workDone = True
            elif timeoutTime != None and time.time() > timeoutTime:
                stepScope[TIMED_OUT] = True
                workDone = True
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in controlPanelMsg.py', logger)
        workDone = True
    finally:
        return workDone