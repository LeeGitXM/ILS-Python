'''
Created on Dec 16, 2015

@author: rforbes

Action for java YesNoStep
Get a yes/no response from the user; block until a
response is received, put response in chart properties
'''

import system
from ils.sfc.common.util import isEmpty
from ils.sfc.gateway.steps.commonInput import cleanup, checkForTimeout
from ils.sfc.gateway.util import getStepProperty, getTimeoutTime, getControlPanelId, registerWindowWithControlPanel, \
        logStepDeactivated, getTopChartRunId, handleUnexpectedGatewayError
from ils.sfc.gateway.api import getDatabaseName, getChartLogger, sendMessageToClient
from ils.sfc.recipeData.api import s88Set, s88Get, s88GetTargetStepUUID
from ils.sfc.common.constants import BUTTON_LABEL, TIMED_OUT, WAITING_FOR_REPLY, TIMEOUT_TIME, IS_SFC_WINDOW, \
    WINDOW_ID, POSITION, SCALE, WINDOW_TITLE, PROMPT, WINDOW_PATH, DEACTIVATED, RECIPE_LOCATION, KEY, TARGET_STEP_UUID

def activate(scopeContext, stepProperties, state):
    buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL)
    if isEmpty(buttonLabel):
        buttonLabel = 'Y/N'

    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    logger = getChartLogger(chartScope)
    windowPath = "SFC/YesNo"
    messageHandler = "sfcOpenWindow"
    responseKey = getStepProperty(stepProperties, KEY)
    responseRecipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION)
    
    if state == DEACTIVATED:
        logStepDeactivated(chartScope, stepProperties)
        cleanup(chartScope, stepScope)
        return False
            
    try:        
        # Check for previous state:
        workDone = False
        waitingForReply = stepScope.get(WAITING_FOR_REPLY, False);
        
        if not waitingForReply:
            # first call; do initialization and cache info in step scope for subsequent calls:
            # calculate the absolute timeout time in epoch secs:
            logger.trace("Initializing a Yes/No step")
            
            # Clear the response recipe data so we know when the client has updated it
            s88Set(chartScope, stepScope, responseKey, "NULL", responseRecipeLocation)

            stepScope[WAITING_FOR_REPLY] = True
            timeoutTime = getTimeoutTime(chartScope, stepProperties)
            stepScope[TIMEOUT_TIME] = timeoutTime
            
            controlPanelId = getControlPanelId(chartScope)
            database = getDatabaseName(chartScope)
            chartRunId = getTopChartRunId(chartScope)
            
            position = getStepProperty(stepProperties, POSITION) 
            scale = getStepProperty(stepProperties, SCALE) 
            title = getStepProperty(stepProperties, WINDOW_TITLE) 
            prompt = getStepProperty(stepProperties, PROMPT)
            
            windowId = registerWindowWithControlPanel(chartRunId, controlPanelId, windowPath, buttonLabel, position, scale, title, database)
            stepScope[WINDOW_ID] = windowId

            sql = "insert into SfcInput (windowId, prompt) values ('%s', '%s')" % (windowId, prompt)
            numInserted = system.db.runUpdateQuery(sql, database)
            if numInserted == 0:
                handleUnexpectedGatewayError(chartScope, stepProperties, 'Failed to insert row into SfcInput', logger)

            targetStepUUID = s88GetTargetStepUUID(chartScope, stepScope, responseRecipeLocation)
            payload = {WINDOW_ID: windowId, WINDOW_PATH: windowPath, TARGET_STEP_UUID: targetStepUUID, KEY: responseKey, IS_SFC_WINDOW: True}
            sendMessageToClient(chartScope, messageHandler, payload)
        
        else: 
            # waiting for reply
            response = s88Get(chartScope, stepScope, responseKey, responseRecipeLocation)
            logger.tracef("...the current response to a Yes/No step is: %s", str(response))
            
            if response <> None and response <> "None" and response <> "NULL": 
                logger.tracef("Setting the workDone flag")
                workDone = True
            else:
                timeout = checkForTimeout(stepScope)
                if timeout:
                    print "The YES_NO step has timed out!"
                    logger.tracef("Setting the Timeout flag")
                    stepScope[TIMED_OUT] = True

    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in commonInput.py', logger)
        workDone = True
    finally:
        if workDone:
            logger.trace("All of the work is done, cleaning up...")
            cleanup(chartScope, stepScope)
        return workDone
