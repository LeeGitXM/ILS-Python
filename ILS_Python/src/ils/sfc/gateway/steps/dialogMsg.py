'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties, state):
    from ils.sfc.gateway.util import getControlPanelId, createWindowRecord, getStepProperty, getTimeoutTime, \
        handleUnexpectedGatewayError, getStepId, sendOpenWindow, logStepDeactivated
    from ils.sfc.gateway.api import getDatabaseName, getChartLogger, s88Get, s88Set
    from ils.sfc.common.util import isEmpty
    from system.ils.sfc.common.Constants import DEACTIVATED, ACTIVATED, PAUSED, CANCELLED
    from system.ils.sfc.common.Constants import BUTTON_LABEL, POSITION, SCALE, WINDOW_TITLE, MESSAGE, \
    ACK_REQUIRED, STRATEGY, STATIC, RECIPE_LOCATION, KEY
    from ils.sfc.common.constants import WAITING_FOR_REPLY, TIMEOUT_TIME, WINDOW_ID, TIMED_OUT
    from ils.sfc.gateway.util import checkForResponse
    import system.db

    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    chartLogger = getChartLogger(chartScope)

    if state == DEACTIVATED:
        logStepDeactivated(chartScope, stepProperties)
        cleanup(chartScope, stepScope)
        return False
 
    try:
        workDone = False
        waitingForReply = stepScope.get(WAITING_FOR_REPLY, False);
        ackRequired =  getStepProperty(stepProperties, ACK_REQUIRED)
        
        if not waitingForReply:
            if ackRequired:
                stepScope[WAITING_FOR_REPLY] = True
            else:
                workDone = True
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

            strategy = getStepProperty(stepProperties, STRATEGY)
            if strategy == STATIC:
                message = getStepProperty(stepProperties, MESSAGE)
            else: # RECIPE
                recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION)
                key = getStepProperty(stepProperties, KEY)
                message = s88Get(chartScope, stepScope, key, recipeLocation)  
            # calculate the absolute timeout time in epoch secs:
            timeoutTime = getTimeoutTime(chartScope, stepProperties)
            stepScope[TIMEOUT_TIME] = timeoutTime
            # create db window records:
            windowId = createWindowRecord(controlPanelId, 'SFC/DialogMessage', buttonLabel, position, scale, title, database)
            stepScope[WINDOW_ID] = windowId
            numInserted = system.db.runUpdateQuery("insert into SfcDialogMsg (windowId, message, ackRequired) values ('%s', '%s', %d)" % (windowId, message, ackRequired), database)
            if numInserted == 0:
                handleUnexpectedGatewayError(chartScope, 'Failed to insert row into SfcDialogMessage', chartLogger)
                
            sendOpenWindow(chartScope, windowId, stepId, database)
        else:
            response = checkForResponse(chartScope, stepScope, stepProperties)    
            if response != None: 
                workDone = True
                if response != TIMED_OUT:
                    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
                    key = getStepProperty(stepProperties, KEY) 
                    s88Set(chartScope, stepScope, key, response, recipeLocation)
                
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in dialogMsg.py', chartLogger)
        workDone = True
    finally:
        # only close the window if we have been waiting for an acknowledgement;
        # otherwise let the chart continue and we will asynchronously get a closeWindow
        # message when the user presses the OK button on the dialog
        if workDone and ackRequired:
            cleanup(chartScope, stepScope)
        return workDone
   
def cleanup(chartScope, stepScope):
    import system.db
    from ils.sfc.gateway.util import deleteAndSendClose, handleUnexpectedGatewayError
    from ils.sfc.gateway.api import getDatabaseName, getProject, getChartLogger
    from ils.sfc.common.constants import WINDOW_ID
    try:
        database = getDatabaseName(chartScope)
        project = getProject(chartScope)
        windowId = stepScope.get(WINDOW_ID, '???')
        system.db.runUpdateQuery("delete from SfcDialogMsg where windowId = '%s'" % (windowId), database)   
        deleteAndSendClose(project, windowId, database)
    except:
        chartLogger = getChartLogger(chartScope)
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in cleanup in commonInput.py', chartLogger)

