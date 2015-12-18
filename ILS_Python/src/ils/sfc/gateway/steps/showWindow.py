'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):   
    from ils.sfc.gateway.util import transferStepPropertiesToMessage, sendMessageToClient
    from system.ils.sfc.common.Constants import SECURITY
    chartScope = scopeContext.getChartScope()
    payload = dict()
    transferStepPropertiesToMessage(stepProperties, payload)
    security = payload[SECURITY]
    #TODO: implement security
    sendMessageToClient(chartScope, 'sfcShowWindow', payload) 
