'''
Created on Dec 16, 2015

@author: rforbes
'''

def activate(scopeContext, step):
    ''' Pause the chart execution'''
    from ils.sfc.gateway.api import pauseChart, addControlPanelMessage, getChartLogger
    from ils.sfc.gateway.util import handleUnexpectedGatewayError
    try:
        chartScope = scopeContext.getChartScope()
        chartLogger = getChartLogger(chartScope)
        stepProperties = step.getProperties();
        pauseChart(chartScope)
        addControlPanelMessage(chartScope, "Chart paused", False)
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in pause.py', chartLogger)
