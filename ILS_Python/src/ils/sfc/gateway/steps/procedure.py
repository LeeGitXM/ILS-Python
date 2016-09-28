'''
Created on Sept 28, 2016
'''

def activate(scopeContext, stepProperties, state):
    from ils.sfc.gateway.util import getStepProperty, getTopChartRunId, handleUnexpectedGatewayError
    from ils.sfc.gateway.api import getDatabaseName, getChartLogger
    from system.ils.sfc.common.Constants import MESSAGE_QUEUE
    import system.db
    try:
        chartScope = scopeContext.getChartScope()
        queueName = getStepProperty(stepProperties, MESSAGE_QUEUE)
        chartLogger = getChartLogger(chartScope)
        database = getDatabaseName(chartScope)
        chartRunId = getTopChartRunId(chartScope)
        system.db.runUpdateQuery("update SfcControlPanel set msgQueue = '%s' where chartRunId = '%s'" % (queueName, chartRunId), database)
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in procedure.py', chartLogger)
    finally:
        return True