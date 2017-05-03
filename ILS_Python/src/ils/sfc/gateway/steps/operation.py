'''
Created on Dec 16, 2015

@author: rforbes
'''
from ils.sfc.gateway.util import getStepProperty, getTopChartRunId, handleUnexpectedGatewayError
from ils.sfc.gateway.api import getDatabaseName, getChartLogger
from ils.sfc.common.constants import NAME
import system
    
def activate(scopeContext, stepProperties, state):

    try:
        chartScope = scopeContext.getChartScope()
        stepName = getStepProperty(stepProperties, NAME)
        chartLogger = getChartLogger(chartScope)
        database = getDatabaseName(chartScope)
        chartRunId = getTopChartRunId(chartScope)
        system.db.runUpdateQuery("update SfcControlPanel set operation = '%s' where chartRunId = '%s'" % (stepName, chartRunId), database)
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in operation.py', chartLogger)
    finally:
        return True