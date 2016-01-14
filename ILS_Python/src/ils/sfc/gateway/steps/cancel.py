'''
Created on Dec 16, 2015

@author: rforbes
'''

def activate(scopeContext, step):
    ''' Abort the chart execution'''
    from ils.sfc.gateway.api import cancelChart, addControlPanelMessage, getChartLogger
    from ils.sfc.gateway.util import handleUnexpectedGatewayError
    try:
        chartScope = scopeContext.getChartScope()
        chartLogger = getChartLogger(chartScope)
        cancelChart(chartScope)
        addControlPanelMessage(chartScope, "Chart canceled", False)
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in cancel.py', chartLogger)

