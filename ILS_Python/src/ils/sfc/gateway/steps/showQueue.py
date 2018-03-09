'''
Created on Dec 16, 2015

@author: rforbes
'''

from ils.sfc.gateway.api import getControlPanelId, getControlPanelName, getOriginator, getStepProperty, getChartLogger, sendMessageToClient, getCurrentMessageQueue, handleUnexpectedGatewayError
from ils.sfc.common.constants import ORIGINATOR, CONTROL_PANEL_ID, CONTROL_PANEL_NAME, HANDLER, POSITION, SCALE
import system

logger=system.util.getLogger("com.ils.sfc.gateway.steps.showQueue")

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

        position = getStepProperty(stepProperties, POSITION) 
        scale = getStepProperty(stepProperties, SCALE) 

        handler = "sfcShowQueue"
        payload = {HANDLER: handler, 'queueKey': currentMsgQueue, CONTROL_PANEL_ID: controlPanelId, CONTROL_PANEL_NAME: controlPanelName, ORIGINATOR: originator, POSITION: position, SCALE: scale}
        logger.infof("Handling a ************************************************* showQueue message with payload: <%s>", str(payload))
        sendMessageToClient(chartScope, handler, payload)
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in showQueue.py', chartLogger)
    finally:
        return True