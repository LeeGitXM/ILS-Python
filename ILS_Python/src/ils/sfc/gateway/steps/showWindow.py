'''
Created on Dec 17, 2015

@author: rforbes

The job of this step is to open a window on the appropriate client.  This works by sending a message with the appropriate payload
to the client and let the client do most of the work.
'''

from ils.sfc.common.constants import WINDOW, WINDOW_ID, WINDOW_PATH, SCALE, POSITION, BUTTON_LABEL, IS_SFC_WINDOW, SECURITY
from ils.sfc.gateway.api import getChartLogger, getDatabaseName, sendMessageToClient, handleUnexpectedGatewayError, registerWindowWithControlPanel, getControlPanelId, getStepProperty, getTopChartRunId
    
def activate(scopeContext, stepProperties, state):
    windowPath = getStepProperty(stepProperties, WINDOW)
    messageHandler = "sfcOpenWindow"

    try:
        chartScope = scopeContext.getChartScope()
        chartLogger = getChartLogger(chartScope)
                
        scale = getStepProperty(stepProperties, SCALE)
        position = getStepProperty(stepProperties, POSITION)
        buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL)
        isSfcWindow = getStepProperty(stepProperties, IS_SFC_WINDOW)
        security = getStepProperty(stepProperties, SECURITY)
        controlPanelId = getControlPanelId(chartScope)
        
        chartLogger.tracef("In %s.activate(), opening window: %s, at %s at scale: %s" % (__name__, windowPath, position, str(scale)))
        
        database = getDatabaseName(chartScope)
        title = ""
        # Register the window with the control panel
        chartRunId = getTopChartRunId(chartScope)
        windowId = registerWindowWithControlPanel(chartRunId, controlPanelId, windowPath, buttonLabel, position, scale, title, database)

        payload = {WINDOW_ID: windowId, WINDOW_PATH: windowPath, IS_SFC_WINDOW: isSfcWindow, SECURITY: security}
        sendMessageToClient(chartScope, messageHandler, payload)
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in showWindow.py', chartLogger)
    # No window cleanup--window is closed in CloseWindow step
    finally:
        return True