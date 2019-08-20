'''
Created on Dec 16, 2015

@author: rforbes

Action for java YesNoStep
Get a yes/no response from the user; block until a
response is received, put response in chart properties
'''

import system
from ils.sfc.common.util import isEmpty
from ils.sfc.gateway.steps.commonInput import cleanup
from ils.sfc.gateway.api import getDatabaseName, getChartLogger, sendMessageToClient, handleUnexpectedGatewayError, getStepProperty, getControlPanelId, registerWindowWithControlPanel, logStepDeactivated, getTopChartRunId
from ils.sfc.recipeData.api import s88Set, s88Get, s88GetStep, substituteScopeReferences
from ils.sfc.common.constants import BUTTON_LABEL, WAITING_FOR_REPLY, IS_SFC_WINDOW, \
    WINDOW_ID, POSITION, SCALE, WINDOW_TITLE, PROMPT, WINDOW_PATH, DEACTIVATED, CANCELLED, RECIPE_LOCATION, KEY

def activate(scopeContext, stepProperties, state):
    buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL)
    if isEmpty(buttonLabel):
        buttonLabel = 'Y/N'

    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    logger = getChartLogger(chartScope)

#    logger.tracef("YES/NO chart scope %s", str(chartScope))
#    logger.tracef("YES/NO step scope %s", str(stepScope))
#    logger.tracef("YES/NO step properties %s", str(stepProperties))
    windowPath = "SFC/YesNo"
    messageHandler = "sfcOpenWindow"
    responseKey = getStepProperty(stepProperties, KEY)
    responseRecipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION)
    
    if state in [DEACTIVATED, CANCELLED]:
        logger.tracef("The Yes/No state is %s!", state)
        logStepDeactivated(chartScope, stepProperties)
        cleanup(chartScope, stepProperties, stepScope)
        return False
            
    try:        
        # Check for previous state:
        workDone = False
        waitingForReply = stepScope.get(WAITING_FOR_REPLY, False);
        
        if not waitingForReply:
            # first call; do initialization and cache info in step scope for subsequent calls:
            logger.tracef("Initializing a Yes/No step, the response key is: %s", responseKey)
            
            # Clear the response recipe data so we know when the client has updated it
            s88Set(chartScope, stepScope, responseKey, "NULL", responseRecipeLocation)
            logger.tracef("---DONE INITIALIZING THE RESPONSE RECIPE DATA---")

            stepScope[WAITING_FOR_REPLY] = True
            
            controlPanelId = getControlPanelId(chartScope)
            database = getDatabaseName(chartScope)
            chartRunId = getTopChartRunId(chartScope)
            
            position = getStepProperty(stepProperties, POSITION) 
            scale = getStepProperty(stepProperties, SCALE) 
            title = getStepProperty(stepProperties, WINDOW_TITLE) 
            prompt = getStepProperty(stepProperties, PROMPT)
            logger.trace("BLAH")
            prompt = substituteScopeReferences(chartScope, stepScope, prompt)
            if prompt.find("<HTML") < 0:
                prompt = "<HTML>" + prompt 
            
            targetStepId, stepName, responseKey = s88GetStep(chartScope, stepScope, responseRecipeLocation, responseKey, database)
            logger.tracef("...the step for the response is: %s - %d", stepName, targetStepId)
            
            windowId = registerWindowWithControlPanel(chartRunId, controlPanelId, windowPath, buttonLabel, position, scale, title, database)
            stepScope[WINDOW_ID] = windowId
            
            sql = "insert into SfcInput (windowId, prompt, targetStepId, keyAndAttribute) values (?, ?, ?, ?)"
            system.db.runPrepUpdate(sql, [windowId, prompt, targetStepId, responseKey], database)
            
            payload = {WINDOW_ID: windowId, WINDOW_PATH: windowPath, IS_SFC_WINDOW: True}
            sendMessageToClient(chartScope, messageHandler, payload)
        
        else: 
            # waiting for reply
            response = s88Get(chartScope, stepScope, responseKey, responseRecipeLocation)
            logger.tracef("...the current response to a Yes/No step is: %s", str(response))
            
            if response <> None and response <> "None" and response <> "NULL": 
                logger.tracef("Setting the workDone flag")
                workDone = True

    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in commonInput.py', logger)
        workDone = True
    finally:
        if workDone:
            logger.trace("All of the work is done, cleaning up...")
            cleanup(chartScope, stepProperties, stepScope)
        return workDone
