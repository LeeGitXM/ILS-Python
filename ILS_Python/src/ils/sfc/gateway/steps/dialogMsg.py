'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, step):
    from ils.sfc.gateway.util import getControlPanelId, createWindowRecord, getStepProperty, getTimeoutTime, \
        handleUnexpectedGatewayError, getStepId, sendOpenWindow, deleteAndSendClose, waitOnResponse
    from ils.sfc.gateway.api import getDatabaseName, getChartLogger, s88Get, getProject
    from ils.sfc.common.util import isEmpty
    from system.ils.sfc.common.Constants import BUTTON_LABEL, POSITION, SCALE, WINDOW_TITLE, MESSAGE, \
    ACK_REQUIRED, STRATEGY, STATIC, RECIPE_LOCATION, KEY
    import system.db
    
    try:
        chartScope = scopeContext.getChartScope()
        stepScope = scopeContext.getStepScope()
        stepProperties = step.getProperties();
        chartLogger = getChartLogger(chartScope)
        
        # window common properties:
        database = getDatabaseName(chartScope)
        controlPanelId = getControlPanelId(chartScope)
        buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL) 
        if isEmpty(buttonLabel):
            buttonLabel = 'Msg'
        position = getStepProperty(stepProperties, POSITION) 
        scale = getStepProperty(stepProperties, SCALE) 
        title = getStepProperty(stepProperties, WINDOW_TITLE) 
        # step-specific properties:
        stepId = getStepId(stepProperties) 
        ackRequired =  getStepProperty(stepProperties, ACK_REQUIRED)
        strategy = getStepProperty(stepProperties, STRATEGY)
        if strategy == STATIC:
            message = getStepProperty(stepProperties, MESSAGE)
        else: # RECIPE
            recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION)
            key = getStepProperty(stepProperties, KEY)
            message = s88Get(chartScope, stepScope, key, recipeLocation)  
        # calculate the absolute timeout time in epoch secs:
        timeoutTime = getTimeoutTime(chartScope, stepProperties)
        # create db window records:
        windowId = createWindowRecord(controlPanelId, 'SFC/DialogMessage', buttonLabel, position, scale, title, database)
        numInserted = system.db.runUpdateQuery("insert into SfcDialogMsg (windowId, message, ackRequired) values ('%s', '%s', %d)" % (windowId, message, ackRequired), database)
        if numInserted == 0:
            handleUnexpectedGatewayError(chartScope, 'Failed to insert row into SfcDialogMessage', chartLogger)
            
        sendOpenWindow(chartScope, windowId, stepId, database)
    
        if ackRequired:
            response = waitOnResponse(windowId, chartScope, timeoutTime)
        # Todo: timeout action??
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in dialogMsg.py', chartLogger)
    finally:
        system.db.runUpdateQuery("delete from SfcDialogMsg where windowId = '%s'" % (windowId), database)   
        project = getProject(chartScope)
        deleteAndSendClose(project, windowId, database)
