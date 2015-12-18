'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):
    from ils.sfc.gateway.util import getTopChartRunId, getStepProperty
    from ils.sfc.gateway.api import sendMessageToClient
    from system.ils.sfc.common.Constants import MESSAGE
    from ils.sfc.common.constants import CHART_RUN_ID, WINDOW_ID
    from ils.sfc.common.util import createUniqueId
    chartScope = scopeContext.getChartScope()
    message = getStepProperty(stepProperties, MESSAGE) 
    payload = dict()
    payload[MESSAGE] = message
    payload[CHART_RUN_ID] = getTopChartRunId(chartScope)
    payload[WINDOW_ID] = createUniqueId()
    sendMessageToClient(chartScope, 'sfcPostDelayNotification', payload)
