'''
Created on Dec 17, 2015

@author: rforbes
'''

import system
from ils.sfc.gateway.api import getStepProperty, getControlPanelId, registerWindowWithControlPanel, logStepDeactivated, getTopChartRunId, \
    getChartLogger, getDatabaseName, sendMessageToClient, handleUnexpectedGatewayError
from ils.sfc.common.constants import CHOICES_RECIPE_LOCATION, CHOICES_KEY, IS_SFC_WINDOW, BUTTON_LABEL, WAITING_FOR_REPLY,\
    DEACTIVATED, CANCELLED, RESPONSE_LOCATION, KEY, TARGET_STEP_UUID, WINDOW_ID, POSITION, SCALE, WINDOW_TITLE, PROMPT, WINDOW_PATH, \
    RESPONSE_KEY_AND_ATTRIBUTE, ID, STEP_ID, INSTANCE_ID, CHART_ID, WORK_DONE, CLIENT_DONE, CHART_SCOPE, STEP_SCOPE
from ils.sfc.common.util import isEmpty
from ils.sfc.recipeData.api import s88Set, s88Get, s88GetStep, substituteScopeReferences
from ils.sfc.gateway.steps.commonInput import cleanup, initializeResponse
from ils.sfc.recipeData.core import splitKey

def activate(scopeContext, stepProperties, state):
    buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL)
    if isEmpty(buttonLabel):
        buttonLabel = 'Select'

    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    logger = getChartLogger(chartScope)
    logger.tracef("In %s.activate()", __name__)
    windowPath = "SFC/SelectInput"
    messageHandler = "sfcOpenWindow"
    
    responseKey = getStepProperty(stepProperties, RESPONSE_KEY_AND_ATTRIBUTE)
    responseLocation = getStepProperty(stepProperties, RESPONSE_LOCATION)
    
    logger.tracef("Response Location: %s", responseLocation)
    logger.tracef("Response Key: %s", responseKey)

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
            logger.tracef("Initializing a Select Input step")
            
            # Get the choices from recipe data:
            choicesRecipeLocation = getStepProperty(stepProperties, CHOICES_RECIPE_LOCATION) 
            choicesKey = getStepProperty(stepProperties, CHOICES_KEY) 
            chartId = chartScope.get(INSTANCE_ID, -1)
            stepId = getStepProperty(stepProperties, ID)
            logger.tracef("Chart id: %s", chartId)
            logger.tracef("Step id: %s", stepId)
            
            stepScope[WAITING_FOR_REPLY] = True
            stepScope[CLIENT_DONE] = False
            
            controlPanelId = getControlPanelId(chartScope)
            database = getDatabaseName(chartScope)
            chartRunId = getTopChartRunId(chartScope)
            
            position = getStepProperty(stepProperties, POSITION) 
            scale = getStepProperty(stepProperties, SCALE) 
            title = getStepProperty(stepProperties, WINDOW_TITLE) 
            prompt = getStepProperty(stepProperties, PROMPT)
            prompt = substituteScopeReferences(chartScope, stepScope, prompt)
            if prompt.find("<HTML") < 0:
                prompt = "<HTML>" + prompt 
            
            windowId = registerWindowWithControlPanel(chartRunId, controlPanelId, windowPath, buttonLabel, position, scale, title, database)
            stepScope[WINDOW_ID] = windowId
            
            # Clear the response recipe data so we know when the client has updated it
            initializeResponse(scopeContext, stepProperties, windowId)
            choicesStepId, stepName, choicesKeyAndAttribute = s88GetStep(chartScope, stepScope, choicesRecipeLocation, choicesKey, database)
            
            if responseLocation in [CHART_SCOPE, STEP_SCOPE]:
                responseKeyAndAttribute = responseKey
                targetStepId = -1
            else:
                targetStepId, stepName, responseKeyAndAttribute = s88GetStep(chartScope, stepScope, responseLocation, responseKey, database)
                logger.tracef("TargetStepId: %s, stepName: %s", targetStepId, stepName)
            
            SQL = "insert into SfcSelectInput (windowId, prompt, choicesStepId, choicesKey, targetStepId, keyAndAttribute, responseLocation, chartId, stepId) values (?, ?, ?, ?, ?, ?, ?, ?, ?)"
            logger.tracef(SQL)
            args = [windowId, prompt, choicesStepId, choicesKeyAndAttribute, targetStepId, responseKeyAndAttribute, responseLocation, str(chartId), str(stepId)]
            logger.tracef(str(args))
            system.db.runPrepUpdate(SQL, args, database)
            
            payload = {WINDOW_ID: windowId, WINDOW_PATH: windowPath, IS_SFC_WINDOW: True}
            sendMessageToClient(chartScope, messageHandler, payload)
            
        else:
            clientDone = stepScope.get(CLIENT_DONE, False);
            logger.tracef("...checking clientDone: %s", str(clientDone))
            if clientDone:
                workDone =True
                
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in %s' % (__name__), logger)
        workDone = True
        
    finally:
        if workDone:
            cleanup(chartScope, stepProperties, stepScope)
        return workDone
