'''
Created on Dec 16, 2015

@author: rforbes
'''

from ils.sfc.gateway.api import getDatabaseName, getChartLogger, handleUnexpectedGatewayError, getStepProperty, getTopChartRunId
from ils.sfc.common.constants import NAME, MESSAGE_QUEUE
import system
    
def activate(scopeContext, stepProperties, state):

    try:
        chartScope = scopeContext.getChartScope()
        stepName = getStepProperty(stepProperties, NAME)
        messageQueue = getStepProperty(stepProperties, MESSAGE_QUEUE)
        logger = getChartLogger(chartScope)
        db = getDatabaseName(chartScope)
        chartRunId = getTopChartRunId(chartScope)
        rows = system.db.runUpdateQuery("update SfcControlPanel set operation = '%s', MsgQueue = '%s' where chartRunId = '%s'" % (stepName, messageQueue, chartRunId), database=db)
        if rows <> 1:
            logger.errorf("Error updating the SfcControlPanel info for operation <%s> and queue <%s> using chartRunId: %s", stepName, messageQueue, chartRunId)
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in operation.py', logger)
    finally:
        return True