'''
Created on Dec 17, 2015

@author: rforbes
'''

import system, time
from ils.sfc.common.util import isEmpty
from ils.sfc.gateway.steps.commonInput import cleanup
from ils.sfc.gateway.api import getStepProperty, getControlPanelId, registerWindowWithControlPanel, \
        logStepDeactivated, getTopChartRunId, getDatabaseName, getChartLogger, sendMessageToClient, handleUnexpectedGatewayError
from ils.sfc.recipeData.api import s88Set, s88Get, s88GetTargetStepUUID
from ils.sfc.common.constants import BUTTON_LABEL, WAITING_FOR_REPLY, IS_SFC_WINDOW, \
    WINDOW_ID, POSITION, SCALE, WINDOW_TITLE, PROMPT, WINDOW_PATH, DEACTIVATED, RECIPE_LOCATION, KEY

def activate(scopeContext, stepProperties, state):
    buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL)
    if isEmpty(buttonLabel):
        buttonLabel = 'Input'
    
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    logger = getChartLogger(chartScope)
    windowPath = "SFC/Input"
    messageHandler = "sfcOpenWindow"
    responseKey = getStepProperty(stepProperties, KEY)
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
            logger.trace("Initializing a getInput step")
            
            # Clear the response recipe data so we know when the client has updated it
            s88Set(chartScope, stepScope, responseKey, "NULL", responseRecipeLocation)
            
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

            targetStepUUID = s88GetTargetStepUUID(chartScope, stepScope, responseRecipeLocation)

            sql = "insert into SfcInput (windowId, prompt, targetStepUUID, keyAndAttribute) values ('%s', '%s', '%s', '%s')" % (windowId, prompt, targetStepUUID, responseKey)
            numInserted = system.db.runUpdateQuery(sql, database)
            if numInserted == 0:
                handleUnexpectedGatewayError(chartScope, stepProperties, 'Failed to insert row into SfcInput', logger)

            payload = {WINDOW_ID: windowId, WINDOW_PATH: windowPath, IS_SFC_WINDOW: True}
            time.sleep(0.1)
            sendMessageToClient(chartScope, messageHandler, payload)
        
        else: # waiting for reply
            response = s88Get(chartScope, stepScope, responseKey, responseRecipeLocation)
            logger.tracef("...the current response to a Get Input step is: %s", str(response))
            
            if response <> None and response <> "NULL":
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