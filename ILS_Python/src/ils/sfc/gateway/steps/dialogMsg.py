'''
Created on Dec 17, 2015

@author: rforbes
'''

import system
from ils.sfc.recipeData.api import s88Set, s88Get, s88SetWithUnits, s88GetWithUnits
from ils.sfc.gateway.api import sendMessageToClient, getControlPanelId, registerWindowWithControlPanel, getStepProperty, \
    logStepDeactivated, getTopChartRunId, deleteAndSendClose, getDatabaseName, getChartLogger, handleUnexpectedGatewayError, getProject
from ils.sfc.recipeData.api import substituteScopeReferences
from ils.sfc.common.util import isEmpty
from ils.sfc.common.constants import WAITING_FOR_REPLY, WINDOW_ID, WINDOW_PATH, MESSAGE, IS_SFC_WINDOW, \
    KEY, TARGET_STEP_UUID, DEACTIVATED, POSITION, SCALE, WINDOW_TITLE, STATIC, RECIPE_LOCATION, STRATEGY, ACK_REQUIRED, BUTTON_LABEL

def activate(scopeContext, stepProperties, state):
    chartScope = scopeContext.getChartScope()
    database = getDatabaseName(chartScope)
    stepScope = scopeContext.getStepScope()
    logger = getChartLogger(chartScope)
    windowPath = "SFC/DialogMessage"
    messageHandler = "sfcOpenWindow"

    if state == DEACTIVATED:
        logStepDeactivated(chartScope, stepProperties)
        cleanup(chartScope, stepProperties, stepScope)
        return False
 
    try:
        workDone = False
        waitingForReply = stepScope.get(WAITING_FOR_REPLY, False);
        ackRequired =  getStepProperty(stepProperties, ACK_REQUIRED)
        
        if not waitingForReply:
            logger.trace("In %s.activate() initializing the step... (Ack required: %s)" % (__name__, str(ackRequired)))
            if ackRequired:
                stepScope[WAITING_FOR_REPLY] = True
            else:
                workDone = True
            
            # common window properties:
            controlPanelId = getControlPanelId(chartScope)
            chartRunId = getTopChartRunId(chartScope)
            
            buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL) 
            if isEmpty(buttonLabel):
                buttonLabel = 'Msg'
            position = getStepProperty(stepProperties, POSITION) 
            scale = getStepProperty(stepProperties, SCALE) 
            title = getStepProperty(stepProperties, WINDOW_TITLE) 

            strategy = getStepProperty(stepProperties, STRATEGY)
            if strategy == STATIC:
                message = getStepProperty(stepProperties, MESSAGE)
            else: # RECIPE
                recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION)
                key = getStepProperty(stepProperties, KEY)
                message = s88Get(chartScope, stepScope, key, recipeLocation)
                
            message = substituteScopeReferences(chartScope, stepScope, message)
            
            # create db window records:
            windowId = registerWindowWithControlPanel(chartRunId, controlPanelId, windowPath, buttonLabel, position, scale, title, database)
            stepScope[WINDOW_ID] = windowId
            numInserted = system.db.runUpdateQuery("insert into SfcDialogMessage (windowId, message, ackRequired) values ('%s', '%s', %d)" % (windowId, message, ackRequired), database)
            if numInserted == 0:
                handleUnexpectedGatewayError(chartScope, stepProperties, 'Failed to insert row into SfcDialogMessage', logger)
            
            # The client side does not use recipe data, but I need to send it to keep the framework happy.
            payload = {WINDOW_ID: windowId, WINDOW_PATH: windowPath, TARGET_STEP_UUID: "", KEY: "", IS_SFC_WINDOW: True}
            sendMessageToClient(chartScope, messageHandler, payload)
            
            logger.trace("...done initializing!")
        
        else:
            # If we ever get into this branch then acknowledgement is required.
            logger.trace("In %s.activate(), waiting for a response..." % (__name__))
            windowId = stepScope[WINDOW_ID]
            SQL = "select acknowledged from SfcDialogMessage where windowId = '%s'" % (windowId)
            pds = system.db.runQuery(SQL, database)
            if len(pds) == 0:
                logger.info("...no rows found for this window, assuming that the window has been acknowledged!")
                workDone = True
            else:
                record = pds[0]
                acknowledged = record["acknowledged"]
                if acknowledged:
                    logger.info("The message dialog has been acknowledged!")
                    workDone = True
                
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in dialogMsg.py', logger)
        workDone = True
    finally:
        # only close the window if we have been waiting for an acknowledgement;
        # otherwise let the chart continue and we will asynchronously get a closeWindow
        # message when the user presses the OK button on the dialog
        if workDone and ackRequired:
            cleanup(chartScope, stepProperties, stepScope)
        return workDone
   
def cleanup(chartScope, stepProperties, stepScope):
    try:
        database = getDatabaseName(chartScope)
        project = getProject(chartScope)
        windowId = stepScope.get(WINDOW_ID, '???')
        system.db.runUpdateQuery("delete from SfcDialogMessage where windowId = '%s'" % (windowId), database)   
        deleteAndSendClose(project, windowId, database)
    except:
        chartLogger = getChartLogger(chartScope)
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in cleanup in commonInput.py', chartLogger)

