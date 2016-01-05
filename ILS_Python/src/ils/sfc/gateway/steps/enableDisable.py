'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):
    from ils.sfc.gateway.api import sendMessageToClient, getProject
    from ils.sfc.gateway.util import transferStepPropertiesToMessage
    chartScope = scopeContext.getChartScope()
    payload = dict()
    transferStepPropertiesToMessage(stepProperties, payload)
    project = getProject(chartScope)
    sendMessageToClient(project, 'sfcEnableDisable', payload)