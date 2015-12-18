'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):
    from ils.sfc.gateway.api import sendMessageToClient
    from ils.sfc.gateway.util import transferStepPropertiesToMessage
    chartScope = scopeContext.getChartScope()
    payload = dict()
    transferStepPropertiesToMessage(stepProperties, payload)
    sendMessageToClient(chartScope, 'sfcEnableDisable', payload)