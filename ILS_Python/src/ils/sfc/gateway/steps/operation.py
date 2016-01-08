'''
Created on Dec 16, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):
    from ils.sfc.gateway.util import getStepProperty, getTopChartRunId, handleUnexpectedGatewayError
    from ils.sfc.gateway.api import getDatabaseName, getChartLogger
    from system.ils.sfc.common.Constants import NAME
    import system.db
    try:
        chartScope = scopeContext.getChartScope()
        stepName = getStepProperty(stepProperties, NAME)
        chartLogger = getChartLogger(chartScope)
        database = getDatabaseName(chartScope)
        chartRunId = getTopChartRunId(chartScope)
        system.db.runUpdateQuery("update SfcControlPanel set operation = '%s' where chartRunId = '%s'" % (stepName, chartRunId), database)
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in operation.py', chartLogger)
