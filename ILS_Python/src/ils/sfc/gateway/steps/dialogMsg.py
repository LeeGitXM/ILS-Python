'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):
    from ils.sfc.gateway.util import transferStepPropertiesToMessage
    from ils.sfc.gateway.api import sendMessageToClient
    chartScope = scopeContext.getChartScope()
    payload = dict()
    transferStepPropertiesToMessage(stepProperties,payload)
    sendMessageToClient(chartScope, 'sfcDialogMessage', payload)

