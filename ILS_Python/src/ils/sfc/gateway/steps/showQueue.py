'''
Created on Dec 16, 2015

@author: rforbes
'''

from ils.sfc.gateway.api import getControlPanelId, getControlPanelName, getOriginator, getChartLogger, sendMessageToClient, getCurrentMessageQueue, handleUnexpectedGatewayError, getStepProperty
from ils.sfc.common.constants import ORIGINATOR, CONTROL_PANEL_ID, CONTROL_PANEL_NAME, HANDLER, QUEUEPOSITION, SCALE

def activate(scopeContext, stepProperties, state):
    '''
    action for java ShowQueueStep
    send a message to the client to show the current message queue
    '''

    try:
        chartScope = scopeContext.getChartScope()
        chartLogger = getChartLogger(chartScope)
        currentMsgQueue = getCurrentMessageQueue(chartScope)
        controlPanelId = getControlPanelId(chartScope)
        controlPanelName = getControlPanelName(chartScope)
        originator = getOriginator(chartScope)
        position = getStepProperty(stepProperties, QUEUEPOSITION) 
        scale = getStepProperty(stepProperties, SCALE) 

        handler = "sfcShowQueue"
        payload = {HANDLER: handler, 'queueKey': currentMsgQueue, CONTROL_PANEL_ID: controlPanelId, CONTROL_PANEL_NAME: controlPanelName, ORIGINATOR: originator, QUEUEPOSITION: position, SCALE: scale}
        sendMessageToClient(chartScope, handler, payload)
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in showQueue.py', chartLogger)
    finally:
        return True