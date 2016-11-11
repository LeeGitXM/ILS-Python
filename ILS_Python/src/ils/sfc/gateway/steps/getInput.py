'''
Created on Dec 17, 2015

@author: rforbes
'''

import system
from ils.sfc.common.util import isEmpty
from ils.sfc.gateway.steps.commonInput import cleanup, setResponse
from ils.sfc.gateway.util import getStepProperty, getTimeoutTime, getControlPanelId, registerWindowWithControlPanel, \
        checkForResponse, logStepDeactivated, getStepId, getTopChartRunId, handleUnexpectedGatewayError
from ils.sfc.gateway.api import getDatabaseName, getChartLogger, sendMessageToClient
from ils.sfc.common.constants import BUTTON_LABEL, TIMED_OUT, WAITING_FOR_REPLY, TIMEOUT_TIME, \
    WINDOW_ID, POSITION, SCALE, WINDOW_TITLE, PROMPT, WINDOW_PATH, DEACTIVATED

def activate(scopeContext, stepProperties, state):
    buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL)
    if isEmpty(buttonLabel):
        buttonLabel = 'Input'
    
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    logger = getChartLogger(chartScope)
    windowPath = "SFC/Input"
    messageHandler = "sfcOpenWindow"

    if state == DEACTIVATED:
        logStepDeactivated(chartScope, stepProperties)
        cleanup(chartScope, stepScope)
        return False
            
    try:        
        # Get info from scope common across invocations 
        stepId = getStepId(stepProperties) 

        # Check for previous state:
        workDone = False
        waitingForReply = stepScope.get(WAITING_FOR_REPLY, False);
        
        if not waitingForReply:
            # first call; do initialization and cache info in step scope for subsequent calls:
            # calculate the absolute timeout time in epoch secs:
            logger.trace("Initializing a getInput step")
            
            setResponse(chartScope, stepScope, stepProperties, None)
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
                handleUnexpectedGatewayError(chartScope, 'Failed to insert row into SfcInput', logger)

            payload = {WINDOW_ID: windowId, WINDOW_PATH: windowPath}
            sendMessageToClient(chartScope, messageHandler, payload)
        else: # waiting for reply
            logger.trace("Waiting for a response to a Yes/No step...")
            response = checkForResponse(chartScope, stepScope, stepProperties)
            if response != None: 
                workDone = True
                if response != TIMED_OUT:
                    setResponse(chartScope, stepScope, stepProperties, response)                
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in commonInput.py', logger)
        workDone = True
    finally:
        if workDone:
            cleanup(chartScope, stepScope)
        return workDone
