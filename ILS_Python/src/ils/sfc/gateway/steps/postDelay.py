'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):
    from ils.sfc.gateway.util import getControlPanelId, createWindowRecord, getStepProperty, \
        handleUnexpectedGatewayError, getStepId, sendOpenWindow
    from ils.sfc.gateway.api import getDatabaseName, getChartLogger
    from ils.sfc.common.util import isEmpty
    from system.ils.sfc.common.Constants import BUTTON_LABEL, POSITION, SCALE, WINDOW_TITLE, MESSAGE
    import system.db
    
    try:
        chartScope = scopeContext.getChartScope()
        chartLogger = getChartLogger(chartScope)
        
        # window common properties:
        database = getDatabaseName(chartScope)
        controlPanelId = getControlPanelId(chartScope)
        buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL) 
        if isEmpty(buttonLabel):
            buttonLabel = 'Busy'
        position = getStepProperty(stepProperties, POSITION) 
        scale = getStepProperty(stepProperties, SCALE) 
        title = getStepProperty(stepProperties, WINDOW_TITLE) 
        # step-specific properties:
        message = getStepProperty(stepProperties, MESSAGE)
        stepId = getStepId(stepProperties) 
    
        # create db window records:
        windowId = createWindowRecord(controlPanelId, 'SFC/BusyNotification', buttonLabel, position, scale, title, database)
        numInserted = system.db.runUpdateQuery("insert into SfcBusyNotification (windowId, message) values ('%s', '%s')" % (windowId, message), database)
        if numInserted == 0:
            handleUnexpectedGatewayError(chartScope, 'Failed to insert row into SfcInput', chartLogger)
            
        sendOpenWindow(chartScope, windowId, stepId, database)
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in postDelay.py', chartLogger)
    # no window cleanup/close; windows stay open until DeleteDelayNotification step executes