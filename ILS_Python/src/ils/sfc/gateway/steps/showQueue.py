'''
Created on Dec 16, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):
    '''
    action for java ShowQueueStep
    send a message to the client to show the current message queue
    '''
    from ils.sfc.gateway.util import sendMessageToClient, handleUnexpectedGatewayError
    from system.ils.sfc.common.Constants import MESSAGE_QUEUE
    from ils.sfc.gateway.api import getCurrentMessageQueue, getProject, getChartLogger
    
    try:
        chartScope = scopeContext.getChartScope()
        chartLogger = getChartLogger(chartScope)
        currentMsgQueue = getCurrentMessageQueue(chartScope)
        payload = dict()
        payload[MESSAGE_QUEUE] = currentMsgQueue 
        project = getProject(chartScope)
        sendMessageToClient(project, 'sfcShowQueue', payload)
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in cancel.py', chartLogger)