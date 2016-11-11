'''
Created on Dec 17, 2015

@author: rforbes

The job of this step is to open a window on the appropriate client.  This works by sending a message with the appropriate payload
to the client and let the client do most of the work.
'''

def activate(scopeContext, stepProperties, state):   
    from ils.sfc.gateway.util import registerWindowWithControlPanel, getControlPanelId, getControlPanelName, sendOpenWindow, getStepId, \
    handleUnexpectedGatewayError, getStepProperty, getOriginator
    from ils.sfc.common.constants import ORIGINATOR, WINDOW, WINDOW_ID, WINDOW_PATH, CONTROL_PANEL_ID, CONTROL_PANEL_NAME, SCALE, POSITION, SECURITY, BUTTON_LABEL
    from ils.sfc.gateway.util import sendMessageToClient
    from ils.sfc.gateway.api import getChartLogger, getDatabaseName, getProject

    windowPath = getStepProperty(stepProperties, WINDOW)
    messageHandler = "sfcOpenWindow"

    try:
        chartScope = scopeContext.getChartScope()
        chartLogger = getChartLogger(chartScope)
                
        scale = getStepProperty(stepProperties, SCALE)
        position = getStepProperty(stepProperties, POSITION)
        buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL)
        controlPanelId = getControlPanelId(chartScope)
        
        database = getDatabaseName(chartScope)
        title = ""
        # Register the window with the control panel
        from ils.sfc.gateway.util import getTopChartRunId
        chartRunId = getTopChartRunId(chartScope)
        windowId = registerWindowWithControlPanel(chartRunId, controlPanelId, windowPath, buttonLabel, position, scale, title, database)

        payload = {WINDOW_ID: windowId, WINDOW_PATH: windowPath}
        sendMessageToClient(chartScope, messageHandler, payload)
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in showWindow.py', chartLogger)
    # No window cleanup--window is closed in CloseWindow step
    finally:
        return True