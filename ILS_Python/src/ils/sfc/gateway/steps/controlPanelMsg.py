'''
Created on Dec 16, 2015

@author: rforbes
'''

import system
from ils.sfc.common.constants import DEACTIVATED, ACTIVATED, PAUSED, CANCELLED, MESSAGE, ACK_REQUIRED, POST_TO_QUEUE, PRIORITY
from ils.sfc.common.constants import WAITING_FOR_REPLY, MESSAGE_ID
from ils.queue.message import insert
from ils.sfc.recipeData.api import substituteScopeReferences
from ils.sfc.gateway.api import getDatabaseName, addControlPanelMessage, getCurrentMessageQueue, getChartLogger, handleUnexpectedGatewayError, getStepProperty, logStepDeactivated

def activate(scopeContext, stepProperties, state):
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
            else:
                workDone = True
        else:
            logger.trace("Checking if the message has been acknowledged")
            msgId = stepScope[MESSAGE_ID]

            SQL = "select count(*) from SfcControlPanelMessage where id = '%s'" % msgId
            rows = system.db.runScalarQuery(SQL, database)

            if rows == 0:
                workDone = True

    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in controlPanelMsg.py', logger)
        workDone = True
    finally:
        return workDone