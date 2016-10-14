'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties, state):   
    from ils.sfc.gateway.util import createWindowRecord, getControlPanelId, sendOpenWindow, getStepId, \
    handleUnexpectedGatewayError, getStepProperty, getOriginator
    from ils.sfc.common.util import isEmpty
    from ils.sfc.common.constants import ORIGINATOR, WINDOW, CONTROL_PANEL_ID
    from ils.sfc.gateway.util import sendMessageToClient
    from ils.sfc.gateway.api import getChartLogger, getDatabaseName, getProject
    from system.ils.sfc.common.Constants import SECURITY, BUTTON_LABEL, POSITION, \
        SCALE, WINDOW_TITLE

    try:
        chartScope = scopeContext.getChartScope()
        chartLogger = getChartLogger(chartScope)
        stepId = getStepId(stepProperties) 

        windowType = getStepProperty(stepProperties, WINDOW) 
        controlPanelId = getControlPanelId(chartScope)
        originator = getOriginator(chartScope)
        
        print "Opening an ordinary window"
        project = getProject(chartScope)
        sendMessageToClient(project, 'sfcOpenOrdinaryWindow', \
                {WINDOW: windowType, CONTROL_PANEL_ID: controlPanelId, ORIGINATOR: originator})

    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in showWindow.py', chartLogger)
    # No window cleanup--window is closed in CloseWindow step
    finally:
        return True