'''
Created on Dec 16, 2015

@author: rforbes

Action for java YesNoStep
Get a yes/no response from the user; block until a
response is received, put response in chart properties
'''

import system
from ils.sfc.common.util import isEmpty
from ils.sfc.gateway.steps.commonInput import cleanup, initializeResponse
from ils.sfc.gateway.api import getDatabaseName, getChartLogger, sendMessageToClient, handleUnexpectedGatewayError, getStepProperty, getControlPanelId, registerWindowWithControlPanel, logStepDeactivated, getTopChartRunId
from ils.sfc.recipeData.api import s88Set, s88Get, s88GetStep, substituteScopeReferences
from ils.sfc.common.constants import BUTTON_LABEL, WAITING_FOR_REPLY, IS_SFC_WINDOW, \
    WINDOW_ID, POSITION, SCALE, WINDOW_TITLE, PROMPT, WINDOW_PATH, DEACTIVATED, CANCELLED, RECIPE_LOCATION, KEY, \
    ID, INSTANCE_ID, CHART_ID, WORK_DONE, CLIENT_DONE, CHART_SCOPE, STEP_SCOPE

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
    responseLocation = getStepProperty(stepProperties, RECIPE_LOCATION)
    
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
            logger.tracef("Initializing a Yes/No step, the response key is: %s", responseKey)
            
            chartId = chartScope.get(INSTANCE_ID, -1)
            stepId = getStepProperty(stepProperties, ID)
            logger.tracef("Chart id: %s", chartId)
            logger.tracef("Step id: %s", stepId)

            stepScope[WAITING_FOR_REPLY] = True
            stepScope[CLIENT_DONE] = False
            
            controlPanelId = getControlPanelId(chartScope)
            database = getDatabaseName(chartScope)
            logger.tracef("...using database: %s", database)
            chartRunId = getTopChartRunId(chartScope)
            
            position = getStepProperty(stepProperties, POSITION) 
            scale = getStepProperty(stepProperties, SCALE) 
            title = getStepProperty(stepProperties, WINDOW_TITLE) 
            prompt = getStepProperty(stepProperties, PROMPT)
            logger.trace("BLAH")
            prompt = substituteScopeReferences(chartScope, stepScope, prompt)
            if prompt.find("<HTML") < 0:
                prompt = "<HTML>" + prompt 
            
            windowId = registerWindowWithControlPanel(chartRunId, controlPanelId, windowPath, buttonLabel, position, scale, title, database)
            stepScope[WINDOW_ID] = windowId
            
            ''' Clear the response recipe data so we know when the client has updated it '''
            initializeResponse(scopeContext, stepProperties, windowId)
            
            if responseLocation in [CHART_SCOPE, STEP_SCOPE]:
                responseKeyAndAttribute = responseKey
                targetStepId = -1
            else:
                targetStepId, stepName, responseKeyAndAttribute = s88GetStep(chartScope, stepScope, responseLocation, responseKey, database)
                logger.tracef("...the step for the response is: %s - %d", stepName, targetStepId)
            
            SQL = "insert into SfcInput (windowId, prompt, targetStepId, keyAndAttribute, responseLocation, chartId, stepId) values (?, ?, ?, ?, ?, ?, ?)"
            logger.tracef(SQL)
            args =  [windowId, prompt, targetStepId, responseKeyAndAttribute, responseLocation, str(chartId), str(stepId)]
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
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in commonInput.py', logger)
        workDone = True
    finally:
        if workDone:
            cleanup(chartScope, stepProperties, stepScope)
        return workDone
