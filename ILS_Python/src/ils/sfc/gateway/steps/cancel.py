'''
Created on Dec 16, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):
    ''' Abort the chart execution'''
    from ils.sfc.gateway.api import cancelChart, addControlPanelMessage
    chartScope = scopeContext.getChartScope()
    cancelChart(chartScope)
    addControlPanelMessage(chartScope, "Chart canceled", False)
