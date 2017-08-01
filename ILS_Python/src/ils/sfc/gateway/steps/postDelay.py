'''
Created on Dec 17, 2015

@author: rforbes
'''

import system
from ils.sfc.gateway.api import getControlPanelId, registerWindowWithControlPanel, getStepProperty, getTopChartRunId, \
    getDatabaseName, getChartLogger, handleUnexpectedGatewayError, sendMessageToClient
from ils.sfc.common.util import isEmpty
from ils.sfc.common.constants import BUTTON_LABEL, POSITION, SCALE, WINDOW_ID, WINDOW_TITLE, MESSAGE, \
    WINDOW_PATH, TARGET_STEP_UUID, KEY, IS_SFC_WINDOW, NAME

def activate(scopeContext, stepProperties, state):

    try:
        chartScope = scopeContext.getChartScope()
        stepScope = scopeContext.getStepScope()
        stepName=stepScope.get(NAME, "Unknown")
        logger = getChartLogger(chartScope)
        logger.tracef("In %s.activate() initializing the step %s...", __name__, stepName)
        windowPath = "SFC/BusyNotification"
        messageHandler = "sfcOpenWindow"

        # window common properties:
        database = getDatabaseName(chartScope)
        controlPanelId = getControlPanelId(chartScope)
        chartRunId = getTopChartRunId(chartScope)
        
        buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL) 
        if isEmpty(buttonLabel):
            buttonLabel = 'Busy'
        
        position = getStepProperty(stepProperties, POSITION) 
        scale = getStepProperty(stepProperties, SCALE) 
        title = getStepProperty(stepProperties, WINDOW_TITLE) 
        # step-specific properties:
        message = getStepProperty(stepProperties, MESSAGE)

        windowId = registerWindowWithControlPanel(chartRunId, controlPanelId, windowPath, buttonLabel, position, scale, title, database)
        system.db.runUpdateQuery("insert into SfcBusyNotification (windowId, message) values ('%s', '%s')" % (windowId, message), database)

        payload = {WINDOW_ID: windowId, WINDOW_PATH: windowPath, TARGET_STEP_UUID: "", KEY: "", IS_SFC_WINDOW: True}
        sendMessageToClient(chartScope, messageHandler, payload)
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in postDelay.py', logger)
    finally:
        return True
    
    
    # no window cleanup/close; windows stay open until DeleteDelayNotification step executes