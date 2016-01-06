'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):   
    from ils.sfc.gateway.util import transferStepPropertiesToMessage, sendMessageToClient
    from ils.sfc.gateway.api import getProject
    chartScope = scopeContext.getChartScope()
    payload = dict()
    transferStepPropertiesToMessage(stepProperties, payload)
    project = getProject(chartScope)
    sendMessageToClient(project, 'sfcPrintWindow', payload)
