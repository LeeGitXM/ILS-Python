'''
Created on Sept 28, 2016
'''

from ils.sfc.gateway.api import getDatabaseName, getChartLogger, handleUnexpectedGatewayError, getStepProperty, getTopChartRunId, getChartPath
from ils.sfc.common.constants import MESSAGE_QUEUE, NAME
from ils.common.util import formatDateTime
from ils.sfc.gateway.steps.commonEncapsulation import monitorCalledChart
import system

def activate(scopeContext, stepProperties, state):

    try:
        chartScope = scopeContext.getChartScope()
        queueName = getStepProperty(stepProperties, MESSAGE_QUEUE)
        logger = getChartLogger(chartScope)
        chartPath = getChartPath(chartScope)
        calledChartPath = getStepProperty(stepProperties, "chart-path")
        stepName = getStepProperty(stepProperties, NAME)
        logger.tracef("In %s.activate()", __name__)
        logger.tracef("chart Scope: %s", str(chartScope))
        logger.tracef("Step Properties: %s", str(stepProperties))
        chartRunId = getTopChartRunId(chartScope)
        logger.infof("The chart run id is: %s", str(chartRunId))
        database = getDatabaseName(chartScope)
        logger.tracef("Database: %s", database)
        system.db.runUpdateQuery("update SfcControlPanel set msgQueue = '%s' where chartRunId = '%s'" % (queueName, chartRunId), database)
        
        SQL = "Insert into SfcRunLog (ChartPath, StepName, StepType, StartTime) values ('%s', '%s', 'Unit Procedure', '%s')" % (chartPath, stepName, formatDateTime(system.date.now(), format='MM/dd/yy HH:mm:ss'))
        runId = system.db.runUpdateQuery(SQL, database=database, getKey=True)
        monitorCalledChart(runId, calledChartPath, database)
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in procedure.py', logger)
    finally:
        return True