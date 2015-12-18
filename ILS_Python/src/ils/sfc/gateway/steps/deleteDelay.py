'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):
    from ils.sfc.gateway.util import getTopChartRunId
    from ils.sfc.gateway.api import sendMessageToClient
    from ils.sfc.common.constants import CHART_RUN_ID
    chartScope = scopeContext.getChartScope()
    payload = dict()
    payload[CHART_RUN_ID] = getTopChartRunId(chartScope)
    sendMessageToClient(chartScope, 'sfcDeleteDelayNotifications', payload)