'''
Created on Dec 16, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):
    ''' Pause the chart execution'''
    from ils.sfc.gateway.api import pauseChart, addControlPanelMessage
    chartScope = scopeContext.getChartScope()
    pauseChart(chartScope)
    addControlPanelMessage(chartScope, "Chart paused", False)
