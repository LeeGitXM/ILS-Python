'''
Created on Dec 17, 2015

@author: rforbes
'''

import system, time
from ils.sfc.common.util import isEmpty
from ils.sfc.gateway.steps.commonInput import cleanup, initializeResponse
from ils.sfc.gateway.api import getDatabaseName, getChartLogger, sendMessageToClient, handleUnexpectedGatewayError, getStepProperty, getControlPanelId, registerWindowWithControlPanel, logStepDeactivated, getTopChartRunId
from ils.sfc.recipeData.api import s88Set, s88Get, s88GetStep, substituteScopeReferences
from ils.sfc.common.constants import BUTTON_LABEL, WAITING_FOR_REPLY, IS_SFC_WINDOW, MINIMUM_VALUE, MAXIMUM_VALUE, \
        WINDOW_ID, POSITION, SCALE, WINDOW_TITLE, PROMPT, DEFAULT_VALUE, WINDOW_PATH, DEACTIVATED, RECIPE_LOCATION, KEY, TARGET_STEP_UUID, \
        ID, STEP_ID, INSTANCE_ID, CHART_ID, WORK_DONE, CLIENT_DONE, CHART_SCOPE, STEP_SCOPE

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
    responseLocation = getStepProperty(stepProperties, RECIPE_LOCATION)
    
    logger.tracef("Response Location: %s", responseLocation)
    logger.tracef("Response Key: %s", responseKey)

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
            logger.trace("Initializing a Get Input with Limits step")
            
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
            title = substituteScopeReferences(chartScope, stepScope, title)
            prompt = getStepProperty(stepProperties, PROMPT)
            prompt = substituteScopeReferences(chartScope, stepScope, prompt)
            defaultValue = getStepProperty(stepProperties, DEFAULT_VALUE)
            minValue = getStepProperty(stepProperties, MINIMUM_VALUE)
            maxValue = getStepProperty(stepProperties, MAXIMUM_VALUE) 
            
            windowId = registerWindowWithControlPanel(chartRunId, controlPanelId, windowPath, buttonLabel, position, scale, title, database)
            stepScope[WINDOW_ID] = windowId
            
            ''' Clear the response recipe data so we know when the client has updated it '''
            initializeResponse(scopeContext, stepProperties, windowId)
            
            if responseLocation in [CHART_SCOPE, STEP_SCOPE]:
                responseKeyAndAttribute = responseKey
                targetStepId = -1
            else:
                targetStepId, stepName, responseKeyAndAttribute = s88GetStep(chartScope, stepScope, responseLocation, responseKey, database)
                logger.tracef("TargetStepId: %s, stepName: %s", targetStepId, stepName)

            SQL = "insert into SfcInput (windowId, prompt, targetStepId, keyAndAttribute, lowLimit, highLimit, defaultValue, responseLocation, chartId, stepId) "\
                " values ('%s', '%s', '%s', '%s', %s, %s, '%s', '%s', '%s', '%s')" \
                % (windowId, prompt, targetStepId, responseKeyAndAttribute, str(minValue), str(maxValue), defaultValue, responseLocation, str(chartId), str(stepId))
            numInserted = system.db.runUpdateQuery(SQL, database)
            if numInserted == 0:
                handleUnexpectedGatewayError(chartScope, stepProperties, 'Failed to insert row into SfcInput', logger)

            payload = {WINDOW_ID: windowId, WINDOW_PATH: windowPath, IS_SFC_WINDOW: True}
            sendMessageToClient(chartScope, messageHandler, payload)
        
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