'''
Created on Dec 17, 2015

@author: rforbes
'''

import system

def activate(scopeContext, stepProperties, state):
    from ils.sfc.gateway.util import getControlPanelId, getControlPanelName, registerWindowWithControlPanel, getStepProperty, \
        handleUnexpectedGatewayError, getStepId, getTopChartRunId, getOriginator
    from ils.sfc.gateway.api import getDatabaseName, getChartLogger, sendMessageToClient, getProject
    from ils.sfc.common.util import isEmpty
    from ils.sfc.common.constants import DATABASE, BUTTON_LABEL, POSITION, SCALE, WINDOW_ID, WINDOW_TITLE, MESSAGE, \
        PROMPT, ORIGINATOR, WINDOW_PATH, CONTROL_PANEL_ID, CONTROL_PANEL_NAME

    try:
        chartScope = scopeContext.getChartScope()
        stepScope = scopeContext.getStepScope()
        logger = getChartLogger(chartScope)
        windowPath = "SFC/BusyNotification"
        messageHandler = "sfcOpenWindow"

        # window common properties:
        database = getDatabaseName(chartScope)
        project=getProject(chartScope)
        controlPanelId = getControlPanelId(chartScope)
        controlPanelName = getControlPanelName(chartScope)
        originator = getOriginator(chartScope)
        chartRunId = getTopChartRunId(chartScope)
        
        buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL) 
        if isEmpty(buttonLabel):
            buttonLabel = 'Busy'
        
        position = getStepProperty(stepProperties, POSITION) 
        scale = getStepProperty(stepProperties, SCALE) 
        title = getStepProperty(stepProperties, WINDOW_TITLE) 
        # step-specific properties:
        message = getStepProperty(stepProperties, MESSAGE)
        stepId = getStepId(stepProperties) 

        windowId = registerWindowWithControlPanel(chartRunId, controlPanelId, windowPath, buttonLabel, position, scale, title, database)
        system.db.runUpdateQuery("insert into SfcBusyNotification (windowId, message) values ('%s', '%s')" % (windowId, message), database)
            
#        sendOpenWindow(chartScope, windowId, stepId, database)
        payload = {WINDOW_ID: windowId, DATABASE: database}
        payload = {WINDOW_ID: windowId, DATABASE: database, CONTROL_PANEL_ID: controlPanelId,\
                       CONTROL_PANEL_NAME: controlPanelName, ORIGINATOR: originator, WINDOW_PATH: windowPath}
        sendMessageToClient(project, messageHandler, payload)
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in postDelay.py', logger)
    finally:
        return True
    
    # no window cleanup/close; windows stay open until DeleteDelayNotification step executes