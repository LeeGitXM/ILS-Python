'''
Created on Dec 16, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties, state):
    '''
    action for java ShowQueueStep
    send a message to the client to show the current message queue
    '''
    from ils.sfc.gateway.util import handleUnexpectedGatewayError, getControlPanelId, getControlPanelName, getOriginator
    from ils.sfc.gateway.api import getChartLogger, sendMessageToClient, getProject, getCurrentMessageQueue, getDatabaseName, getPostForControlPanelName
    from ils.sfc.common.constants import ORIGINATOR, CONTROL_PANEL_ID, CONTROL_PANEL_NAME, HANDLER

    try:
        chartScope = scopeContext.getChartScope()
        chartLogger = getChartLogger(chartScope)
        currentMsgQueue = getCurrentMessageQueue(chartScope)
        controlPanelId = getControlPanelId(chartScope)
        controlPanelName = getControlPanelName(chartScope)
        originator = getOriginator(chartScope)

        handler = "sfcShowQueue"
        payload = {HANDLER: handler, 'queueKey': currentMsgQueue, CONTROL_PANEL_ID: controlPanelId, CONTROL_PANEL_NAME: controlPanelName, ORIGINATOR: originator}
        sendMessageToClient(chartScope, handler, payload)
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in showQueue.py', chartLogger)
    finally:
        return True