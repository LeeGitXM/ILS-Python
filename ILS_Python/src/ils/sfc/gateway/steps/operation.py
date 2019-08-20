'''
Created on Dec 16, 2015

@author: rforbes
'''

from ils.sfc.gateway.api import getDatabaseName, getChartLogger, handleUnexpectedGatewayError, getChartPath, getStepProperty, getTopChartRunId
from ils.sfc.common.constants import NAME, MESSAGE_QUEUE
from ils.common.util import formatDateTime
from ils.sfc.gateway.steps.commonEncapsulation import monitorCalledChart
import system

def activate(scopeContext, stepProperties, state):

    try:
        chartScope = scopeContext.getChartScope()
        chartPath = getChartPath(chartScope)
        stepName = getStepProperty(stepProperties, NAME)
        messageQueue = getStepProperty(stepProperties, MESSAGE_QUEUE)
        calledChartPath = getStepProperty(stepProperties, "chart-path")
        logger = getChartLogger(chartScope)
        db = getDatabaseName(chartScope)
        chartRunId = getTopChartRunId(chartScope)
        rows = system.db.runUpdateQuery("update SfcControlPanel set operation = '%s', MsgQueue = '%s' where chartRunId = '%s'" % (stepName, messageQueue, chartRunId), database=db)
        if rows <> 1:
            logger.errorf("Error updating the SfcControlPanel info for operation <%s> and queue <%s> using chartRunId: %s", stepName, messageQueue, chartRunId)
            
        SQL = "Insert into SfcRunLog (ChartPath, StepName, StepType, StartTime) values ('%s', '%s', 'Operation', '%s')" % (chartPath, stepName, formatDateTime(system.date.now(), format='MM/dd/yy HH:mm:ss'))
        runId = system.db.runUpdateQuery(SQL, database=db, getKey=True)
        monitorCalledChart(runId, calledChartPath, db)
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in operation.py', logger)
    finally:
        return True
    