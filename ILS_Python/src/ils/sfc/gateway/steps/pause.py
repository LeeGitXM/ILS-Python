'''
Created on Dec 16, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties, state):
    ''' Pause the chart execution'''
    from system.ils.sfc.common.Constants import DEACTIVATED, ACTIVATED, PAUSED, CANCELLED
    from ils.sfc.gateway.api import pauseChart, addControlPanelMessage, getChartLogger
    from ils.sfc.gateway.util import handleUnexpectedGatewayError
    chartScope = scopeContext.getChartScope()
    chartLogger = getChartLogger(chartScope)
    try:
        if not (state == DEACTIVATED or state == PAUSED):
            chartLogger = getChartLogger(chartScope)
            pauseChart(chartScope)
            addControlPanelMessage(chartScope, "Chart paused", False)
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in pause.py', chartLogger)
    finally:
        return True