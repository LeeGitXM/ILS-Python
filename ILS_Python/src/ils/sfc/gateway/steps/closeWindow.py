'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, step):   
    from ils.sfc.gateway.util import transferStepPropertiesToMessage, sendMessageToClient, handleUnexpectedGatewayError
    from ils.sfc.gateway.api import getProject, getChartLogger
    try:
        chartScope = scopeContext.getChartScope()
        chartLogger = getChartLogger(chartScope)
        stepProperties = step.getProperties();
        payload = dict()
        transferStepPropertiesToMessage(stepProperties, payload)
        project = getProject(chartScope)
        sendMessageToClient(project, 'sfcCloseWindow', payload)
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in closeWindow.py', chartLogger)
