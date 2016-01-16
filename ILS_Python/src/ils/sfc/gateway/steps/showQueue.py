'''
Created on Dec 16, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):
    '''
    action for java ShowQueueStep
    send a message to the client to show the current message queue
    '''
    from ils.sfc.gateway.util import handleUnexpectedGatewayError
    from ils.sfc.gateway.api import getChartLogger, sendMessageToClient, getProject
    
    try:
        chartScope = scopeContext.getChartScope()
        chartLogger = getChartLogger(chartScope)
        payload = dict()
        project = getProject(chartScope)
        sendMessageToClient(project, 'sfcShowQueue', payload)
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in showQueue.py', chartLogger)
    finally:
        return True