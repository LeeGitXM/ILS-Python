'''
Created on Dec 17, 2015

@author: rforbes
'''

import system
from ils.sfc.gateway.util import getStepProperty, handleUnexpectedGatewayError, getTimeoutTime, getControlPanelId, \
    registerWindowWithControlPanel, checkForResponse, logStepDeactivated, getStepId, getTopChartRunId, getControlPanelName, getOriginator
from ils.sfc.gateway.api import s88Get, getChartLogger, getDatabaseName, getProject, sendMessageToClient
from system.ils.sfc.common.Constants import CHOICES_RECIPE_LOCATION, CHOICES_KEY, BUTTON_LABEL
from ils.sfc.gateway.steps import commonInput
from ils.sfc.common.util import isEmpty

from ils.sfc.gateway.steps.commonInput import cleanup, setResponse

from ils.sfc.common.constants import DATABASE, BUTTON_LABEL, TIMED_OUT, WAITING_FOR_REPLY, TIMEOUT_TIME, \
    CONTROL_PANEL_ID, CONTROL_PANEL_NAME, WINDOW_ID, POSITION, SCALE, WINDOW_TITLE, PROMPT, ORIGINATOR, WINDOW_PATH, \
    DEACTIVATED, ACTIVATED, PAUSED, CANCELLED

def activate(scopeContext, stepProperties, state):
    buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL)
    if isEmpty(buttonLabel):
        buttonLabel = 'Select'

    chartScope = scopeContext.getChartScope()
    logger = getChartLogger(chartScope)
    stepScope = scopeContext.getStepScope()
    windowPath = "SFC/SelectInput"
    messageHandler = "sfcOpenWindow"
    
    
    # Get the choices from recipe data:
#    try:
  
#    except:
#        handleUnexpectedGatewayError(chartScope, 'Unexpected error in selectInput.py', logger)
#        return True
    
#    return commonInput.activate(scopeContext, stepProperties, state, buttonLabel, 'SFC/SelectInput', choices)



    if state == DEACTIVATED:
        logStepDeactivated(chartScope, stepProperties)
        cleanup(chartScope, stepScope)
        return False
            
    try:        
        # Get info from scope common across invocations 
        stepId = getStepId(stepProperties) 
        
        # Get the choices from recipe data:
        choicesRecipeLocation = getStepProperty(stepProperties, CHOICES_RECIPE_LOCATION) 
        choicesKey = getStepProperty(stepProperties, CHOICES_KEY) 
        choices = s88Get(chartScope, stepScope, choicesKey, choicesRecipeLocation)  
        
        print "choicesRecipeLocation: ", choicesRecipeLocation
        print "choicesKey: ", choicesKey
        print "choices: ", choices
        
        # Check for previous state:
        workDone = False
        waitingForReply = stepScope.get(WAITING_FOR_REPLY, False);
        
        if not waitingForReply:
            # first call; do initialization and cache info in step scope for subsequent calls:
            # calculate the absolute timeout time in epoch secs:
            logger.trace("Initializing a Yes/No step")
            
            setResponse(chartScope, stepScope, stepProperties, None)
            stepScope[WAITING_FOR_REPLY] = True
            timeoutTime = getTimeoutTime(chartScope, stepProperties)
            stepScope[TIMEOUT_TIME] = timeoutTime
            
            controlPanelId = getControlPanelId(chartScope)
            controlPanelName = getControlPanelName(chartScope)
            originator = getOriginator(chartScope)
            project = getProject(chartScope)
            database = getDatabaseName(chartScope)
            chartRunId = getTopChartRunId(chartScope)
            
            position = getStepProperty(stepProperties, POSITION) 
            scale = getStepProperty(stepProperties, SCALE) 
            title = getStepProperty(stepProperties, WINDOW_TITLE) 
            prompt = getStepProperty(stepProperties, PROMPT)
            
            windowId = registerWindowWithControlPanel(chartRunId, controlPanelId, windowPath, buttonLabel, position, scale, title, database)
            stepScope[WINDOW_ID] = windowId
            
            sql = "insert into SfcInput (windowId, prompt) values ('%s', '%s')" % (windowId, prompt)
            system.db.runUpdateQuery(sql, database)

            choicesList = system.util.jsonDecode(choices)
            for choice in choicesList:
                sql = "insert into SfcInputChoices (windowId, choice) values ('%s', '%s')" % (windowId, choice)
                system.db.runUpdateQuery(sql, database) 

            payload = {WINDOW_ID: windowId, DATABASE: database, CONTROL_PANEL_ID: controlPanelId,\
                       CONTROL_PANEL_NAME: controlPanelName, ORIGINATOR: originator, WINDOW_PATH: windowPath}
            sendMessageToClient(project, messageHandler, payload)
        else: # waiting for reply
            logger.trace("Waiting for a response to a selectInput step...")
            response = checkForResponse(chartScope, stepScope, stepProperties)
            if response != None: 
                workDone = True
                if response != TIMED_OUT:
                    setResponse(chartScope, stepScope, stepProperties, response)                
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in %s' % (__name__), logger)
        workDone = True
    finally:
        if workDone:
            cleanup(chartScope, stepScope)
        return workDone
