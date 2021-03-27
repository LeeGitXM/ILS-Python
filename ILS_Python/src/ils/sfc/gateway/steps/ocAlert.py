'''
Created on Mar 18, 2021

@author: phass
'''
import system
from ils.common.ocAlert import sendAlert
from ils.sfc.common.util import isEmpty
from ils.sfc.gateway.steps.commonInput import cleanup, initializeResponse
from ils.sfc.gateway.api import getStepProperty, getControlPanelId, registerWindowWithControlPanel, getProject, \
        logStepDeactivated, getTopChartRunId, getDatabaseName, getChartLogger, sendMessageToClient, handleUnexpectedGatewayError
from ils.sfc.recipeData.api import s88Set, s88Get, s88GetStep, substituteScopeReferences
from ils.sfc.common.constants import ACK_REQUIRED, BUTTON_LABEL, WAITING_FOR_REPLY, IS_SFC_WINDOW, \
    WINDOW_ID, PROJECT, WINDOW_PATH, DEACTIVATED, CANCELLED, RECIPE_LOCATION, KEY, \
    ID, STEP_ID, INSTANCE_ID, CHART_ID, WORK_DONE, CLIENT_DONE, CHART_SCOPE, STEP_SCOPE, TOP_MESSAGE, MAIN_MESSAGE, BOTTOM_MESSAGE, \
    OC_ALERT_WINDOW, POST

def activate(scopeContext, stepProperties, state):
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    logger = getChartLogger(chartScope)
    logger.tracef("In %s.activate()", __name__)

    if state in [DEACTIVATED, CANCELLED]:
        logStepDeactivated(chartScope, stepProperties)
        cleanup(chartScope, stepProperties, stepScope)
        return False
            
    try:        
        # Check for previous state:
        workDone = False
        waitingForReply = stepScope.get(WAITING_FOR_REPLY, False);
        
        if not waitingForReply:
            # first call; do initialization and cache info in step scope for subsequent calls:
            logger.trace("Initializing a getInput step")

            chartId = chartScope.get(INSTANCE_ID, -1)
            stepId = getStepProperty(stepProperties, ID)
            controlPanelId = getControlPanelId(chartScope)
            database = getDatabaseName(chartScope)
            chartRunId = getTopChartRunId(chartScope)
            project = getProject(chartScope)
            
            logger.infof("Chart id: %s", chartId)
            logger.infof("Step id: %s", stepId)
            logger.infof("Project: %s", project)
            
            stepScope[WAITING_FOR_REPLY] = True
            stepScope[CLIENT_DONE] = False
            
            topMessage = getStepProperty(stepProperties, TOP_MESSAGE) 
            mainMessage = getStepProperty(stepProperties, MAIN_MESSAGE) 
            bottomMessage = getStepProperty(stepProperties, BOTTOM_MESSAGE) 
            windowPath = getStepProperty(stepProperties, OC_ALERT_WINDOW) 
            post = getStepProperty(stepProperties, POST)
            buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL)
            if isEmpty(buttonLabel):
                buttonLabel = 'OC Alert'
            ackRequired = getStepProperty(stepProperties, ACK_REQUIRED)
            
            if ackRequired:
                sendAlert(project, post, topMessage, bottomMessage, mainMessage, buttonLabel, callback="ils.common.ocAlert.sfcHandshake", 
                    callbackPayloadDictionary={"chartId": chartId, "stepId": stepId}, timeoutEnabled=False, timeoutSeconds=0, db=database, isolationMode=False,
                    windowName=windowPath)
                logger.trace("Setting ACK flag")
                stepScope[WAITING_FOR_REPLY] = True
            else:
                sendAlert(project, post, topMessage, bottomMessage, mainMessage, buttonLabel,  
                    timeoutEnabled=False, timeoutSeconds=0, db=database, isolationMode=False, windowName=windowPath)
                workDone = True
        
        else: 
            ''' waiting for reply '''
            clientDone = stepScope.get(CLIENT_DONE, False);
            logger.tracef("...checking clientDone: %s", str(clientDone))
            if clientDone:
                workDone =True

    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in commonInput.py', logger)
        workDone = True
    finally:
        if workDone:
            logger.trace("All of the work is done, cleaning up...")
            cleanup(chartScope, stepProperties, stepScope)
        return workDone