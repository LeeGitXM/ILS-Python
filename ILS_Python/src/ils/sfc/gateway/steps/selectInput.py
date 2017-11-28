'''
Created on Dec 17, 2015

@author: rforbes
'''

import system
from ils.sfc.gateway.api import getStepProperty, getControlPanelId, registerWindowWithControlPanel, logStepDeactivated, getTopChartRunId, \
    getChartLogger, getDatabaseName, sendMessageToClient, handleUnexpectedGatewayError
from ils.sfc.common.constants import CHOICES_RECIPE_LOCATION, CHOICES_KEY, IS_SFC_WINDOW, BUTTON_LABEL, WAITING_FOR_REPLY,\
    DEACTIVATED, RECIPE_LOCATION, KEY, TARGET_STEP_UUID, WINDOW_ID, POSITION, SCALE, WINDOW_TITLE, PROMPT, WINDOW_PATH, \
    RESPONSE_KEY_AND_ATTRIBUTE
from ils.sfc.common.util import isEmpty
from ils.sfc.recipeData.api import s88Set, s88Get, s88GetStep
from ils.sfc.gateway.steps.commonInput import cleanup

def activate(scopeContext, stepProperties, state):
    buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL)
    if isEmpty(buttonLabel):
        buttonLabel = 'Select'

    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    logger = getChartLogger(chartScope)
    windowPath = "SFC/SelectInput"
    messageHandler = "sfcOpenWindow"
    responseKeyAndAttribute = getStepProperty(stepProperties, RESPONSE_KEY_AND_ATTRIBUTE)
    responseRecipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION)

    if state == DEACTIVATED:
        logStepDeactivated(chartScope, stepProperties)
        cleanup(chartScope, stepProperties, stepScope)
        return False
            
    try:      
        # Check for previous state:
        workDone = False
        waitingForReply = stepScope.get(WAITING_FOR_REPLY, False);
        
        if not waitingForReply:
            # first call; do initialization and cache info in step scope for subsequent calls:
            logger.trace("Initializing a Select Input step")
        
            # Clear the response recipe data so we know when the client has updated it
            s88Set(chartScope, stepScope, responseKeyAndAttribute, "NULL", responseRecipeLocation)
            
            # Get the choices from recipe data:
            choicesRecipeLocation = getStepProperty(stepProperties, CHOICES_RECIPE_LOCATION) 
            choicesKey = getStepProperty(stepProperties, CHOICES_KEY) 
            
            print "choicesRecipeLocation: ", choicesRecipeLocation
            print "choicesKey: ", choicesKey
            
            stepScope[WAITING_FOR_REPLY] = True
            
            controlPanelId = getControlPanelId(chartScope)
            database = getDatabaseName(chartScope)
            chartRunId = getTopChartRunId(chartScope)
            
            position = getStepProperty(stepProperties, POSITION) 
            scale = getStepProperty(stepProperties, SCALE) 
            title = getStepProperty(stepProperties, WINDOW_TITLE) 
            prompt = getStepProperty(stepProperties, PROMPT)
            
            windowId = registerWindowWithControlPanel(chartRunId, controlPanelId, windowPath, buttonLabel, position, scale, title, database)
            stepScope[WINDOW_ID] = windowId
            
            choicesStepUUID, stepName = s88GetStep(chartScope, stepScope, choicesRecipeLocation)
            
            targetStepUUID, stepName = s88GetStep(chartScope, stepScope, responseRecipeLocation)
            
            sql = "insert into SfcSelectInput (windowId, prompt, choicesStepUUID, choicesKey, targetStepUUID, keyAndAttribute) "\
                "values ('%s', '%s', '%s', '%s', '%s', '%s')" \
                % (windowId, prompt, choicesStepUUID, choicesKey, targetStepUUID, responseKeyAndAttribute)
            system.db.runUpdateQuery(sql, database)
            
            payload = {WINDOW_ID: windowId, WINDOW_PATH: windowPath, IS_SFC_WINDOW: True}
            sendMessageToClient(chartScope, messageHandler, payload)
            
        else:
            response = s88Get(chartScope, stepScope, responseKeyAndAttribute, responseRecipeLocation)
            logger.tracef("...the current response to a selectInput step is: %s", str(response))
            
            if response <> None and response <> "None" and response <> "NULL": 
                logger.tracef("Setting the workDone flag")
                workDone = True
                
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in %s' % (__name__), logger)
        workDone = True
    finally:
        if workDone:
            cleanup(chartScope, stepProperties, stepScope)
        return workDone
