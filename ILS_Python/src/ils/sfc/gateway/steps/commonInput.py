'''
Common code for input steps: Yes/No, Input, Input w. choices
Created on Dec 21, 2015
@author: rforbes
'''

import system, time
from ils.sfc.gateway.util import getStepProperty, getTimeoutTime, getControlPanelId, registerWindowWithControlPanel, \
        checkForResponse, logStepDeactivated, getStepId, dbStringForFloat, handleUnexpectedGatewayError, getTopChartRunId, \
        deleteAndSendClose, handleUnexpectedGatewayError
from ils.sfc.gateway.api import s88Set, getDatabaseName, getChartLogger, getProject
from ils.sfc.common.constants import RECIPE_LOCATION, KEY, TIMED_OUT, WAITING_FOR_REPLY, TIMEOUT_TIME, WINDOW_ID, POSITION, SCALE, WINDOW_TITLE, PROMPT
from system.ils.sfc.common.Constants import DEACTIVATED, ACTIVATED, PAUSED, CANCELLED
    
def activate(scopeContext, stepProperties, state, buttonLabel, windowType, message, choices=None, lowLimit=None, highLimit=None):
    '''
    Action for java InputStep
    Get an response from the user; block until a
    response is received, put response in chart properties
    '''

    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    chartLogger = getChartLogger(chartScope)
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
            setResponse(chartScope, stepScope, stepProperties, None)
            stepScope[WAITING_FOR_REPLY] = True
            timeoutTime = getTimeoutTime(chartScope, stepProperties)
            stepScope[TIMEOUT_TIME] = timeoutTime
            controlPanelId = getControlPanelId(chartScope)
            print 'controlPanelId', controlPanelId
            position = getStepProperty(stepProperties, POSITION) 
            scale = getStepProperty(stepProperties, SCALE) 
            title = getStepProperty(stepProperties, WINDOW_TITLE) 
            # step-specific properties:
            prompt = getStepProperty(stepProperties, PROMPT)
            database = getDatabaseName(chartScope)
            chartRunId = getTopChartRunId(chartScope)
            windowId = registerWindowWithControlPanel(chartRunId, controlPanelId, windowType, buttonLabel, position, scale, title, database)
            stepScope[WINDOW_ID] = windowId
            # Note: the low/high limits are formatted as strings so we can insert 'null' if desired
            lowLimit = dbStringForFloat(lowLimit)
            highLimit = dbStringForFloat(highLimit)
            sql = "insert into SfcInput (windowId, prompt, lowLimit, highLimit) values ('%s', '%s', %s, %s)" % (windowId, prompt, lowLimit, highLimit)
            numInserted = system.db.runUpdateQuery(sql, database)
            if numInserted == 0:
                handleUnexpectedGatewayError(chartScope, 'Failed to insert row into SfcInput', chartLogger)
                
            if choices != None:
                choicesList = system.util.jsonDecode(choices)
                for choice in choicesList:
                    system.db.runUpdateQuery("insert into SfcInputChoices (windowId, choice) values ('%s', '%s')" % (windowId, choice), database)                   
                
            sendOpenWindow(chartScope, windowId, stepId, database)
        else: # waiting for reply
            response = checkForResponse(chartScope, stepScope, stepProperties)
            if response != None: 
                workDone = True
                if response != TIMED_OUT:
                    setResponse(chartScope, stepScope, stepProperties, response)                
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in commonInput.py', chartLogger)
        workDone = True
    finally:
        if workDone:
            cleanup(chartScope, stepScope)
        return workDone

def checkForTimeout(stepScope):
    '''Common code for checking the timeout of a step, generally one that has a UI'''
    timeoutTime = stepScope[TIMEOUT_TIME]

    if timeoutTime != None and time.time() > timeoutTime:
        timeout =  True        
    else:
        timeout = False

    return timeout

def setResponse(chartScope, stepScope, stepProperties, response):
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
    key = getStepProperty(stepProperties, KEY) 
    s88Set(chartScope, stepScope, key, response, recipeLocation)
    
def cleanup(chartScope, stepScope):
    print "Cleaning up for a common input step"
    try:
        database = getDatabaseName(chartScope)
        project = getProject(chartScope)
        windowId = stepScope.get(WINDOW_ID, None)
        if windowId != None:
            system.db.runUpdateQuery("delete from SfcInputChoices where windowId = '%s'" % (windowId), database)
            system.db.runUpdateQuery("delete from SfcInput where windowId = '%s'" % (windowId), database)   
            deleteAndSendClose(project, windowId, database)
    except:
        chartLogger = getChartLogger(chartScope)
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in cleanup in commonInput.py', chartLogger)

