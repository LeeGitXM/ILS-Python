'''
Created on Dec 16, 2015

@author: rforbes

 Pause the chart execution
'''
from ils.sfc.common.constants import DEACTIVATED, ACTIVATED, PAUSED, CANCELLED
from ils.sfc.gateway.api import pauseChart, addControlPanelMessage, getChartLogger, handleUnexpectedGatewayError

def activate(scopeContext, stepProperties, state):
    chartScope = scopeContext.getChartScope()
    chartLogger = getChartLogger(chartScope)
    try:
        if not (state == DEACTIVATED or state == PAUSED):
            chartLogger = getChartLogger(chartScope)
            pauseChart(chartScope)
            addControlPanelMessage(chartScope, "Chart paused", "Error", False)
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in pause.py', chartLogger)
    finally:
        return True