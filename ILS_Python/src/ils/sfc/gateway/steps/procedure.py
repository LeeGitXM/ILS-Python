'''
Created on Sept 28, 2016
'''

from ils.sfc.gateway.api import getDatabaseName, getChartLogger, handleUnexpectedGatewayError, getStepProperty, getTopChartRunId
from ils.sfc.common.constants import MESSAGE_QUEUE
import system

def activate(scopeContext, stepProperties, state):

    try:
        chartScope = scopeContext.getChartScope()
        queueName = getStepProperty(stepProperties, MESSAGE_QUEUE)
        logger = getChartLogger(chartScope)
        logger.trace("In %s.activate()" % (__name__))
        chartRunId = getTopChartRunId(chartScope)
        logger.infof("The chart run id is: %s", str(chartRunId))
        database = getDatabaseName(chartScope)
        system.db.runUpdateQuery("update SfcControlPanel set msgQueue = '%s' where chartRunId = '%s'" % (queueName, chartRunId), database)
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in procedure.py', logger)
    finally:
        return True