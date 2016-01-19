'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties, deactivate):   
    from ils.sfc.gateway.util import createWindowRecord, getControlPanelId, sendOpenWindow, getStepId, \
    handleUnexpectedGatewayError, getStepProperty
    from ils.sfc.common.util import isEmpty
    from ils.sfc.gateway.api import getChartLogger, getDatabaseName
    from system.ils.sfc.common.Constants import SECURITY, BUTTON_LABEL, POSITION, SCALE, WINDOW_TITLE, WINDOW
    
    try:
        chartScope = scopeContext.getChartScope()
        chartLogger = getChartLogger(chartScope)
        stepId = getStepId(stepProperties) 

        # window common properties:
        database = getDatabaseName(chartScope)
        controlPanelId = getControlPanelId(chartScope)
        buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL) 
        if isEmpty(buttonLabel):
            buttonLabel = 'Win'
        position = getStepProperty(stepProperties, POSITION) 
        scale = getStepProperty(stepProperties, SCALE) 
        title = getStepProperty(stepProperties, WINDOW_TITLE) 
        # specific properties:
        windowType = getStepProperty(stepProperties, WINDOW) 
        security = getStepProperty(stepProperties, SECURITY)
        windowId = createWindowRecord(controlPanelId, windowType, buttonLabel, position, scale, title, database)
        # ? No window-specific table data. Could enhance to take table name and dictionary to
        # write into a window-specific table
        sendOpenWindow(chartScope, windowId, stepId, database)
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in showWindow.py', chartLogger)
    # No window cleanup--window is closed in CloseWindow step
    finally:
        return True