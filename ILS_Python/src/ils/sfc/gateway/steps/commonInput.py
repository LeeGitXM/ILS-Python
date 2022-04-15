'''
Common code for input steps: Yes/No, Input, Input w. choices
Created on Dec 21, 2015
@author: rforbes
'''

import system, time
from ils.sfc.recipeData.api import s88Set
from ils.sfc.gateway.api import getStepProperty, getTimeoutTime, getControlPanelId, registerWindowWithControlPanel, \
        checkForResponse, logStepDeactivated, dbStringForFloat, getTopChartRunId, deleteAndSendClose, \
        getDatabaseName, getChartLogger, getProject, handleUnexpectedGatewayError
from ils.sfc.common.constants import RECIPE_LOCATION, KEY, TIMED_OUT, WAITING_FOR_REPLY, TIMEOUT_TIME, WINDOW_ID, POSITION, SCALE, WINDOW_TITLE, PROMPT, \
    DEACTIVATED, RESPONSE_KEY_AND_ATTRIBUTE, RESPONSE_LOCATION, FACTORY_ID, \
    REFERENCE_SCOPE, GLOBAL_SCOPE, OPERATION_SCOPE, PHASE_SCOPE, SUPERIOR_SCOPE, LOCAL_SCOPE, PRIOR_SCOPE, CHART_SCOPE, STEP_SCOPE
    

def initializeResponse(scopeContext, stepProperties, windowId):
    '''
    Clear the response recipe data so we know when the client has updated it.
    Also set up the entry in the global cache that is updated by the client when they responded to the window.
    
    I really screwed this up.  The commonInput isn't 100% common!!
    This applies to 4 steps: Yes/NO, Select Inpuy, Get Input, and Get Input with Limits.
    The selectInput is different from the other 3 so I need to make a special test for it.
    The other 3 steps, which follow the desired pattern, do not require the attribute to be added for the recipe data,
    but if it exists, then don't add ".value" again!  4/22/2021
    '''
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    logger = getChartLogger(chartScope)
    
    factoryId=getStepProperty(stepProperties, FACTORY_ID)
    
    if factoryId == "com.ils.selectInputStep":
        responseKey = getStepProperty(stepProperties, RESPONSE_KEY_AND_ATTRIBUTE)
    else:
        responseKey = getStepProperty(stepProperties, KEY)
        if responseKey.find(".") < 0:
            responseKey = responseKey + ".value"
        
    responseLocation = getStepProperty(stepProperties, RECIPE_LOCATION)
    logger.tracef("In %s.initializeResponse(), initializing <%s.%s>", __name__, responseLocation, responseKey)
    
    if responseLocation in [ REFERENCE_SCOPE, GLOBAL_SCOPE, OPERATION_SCOPE, PHASE_SCOPE, SUPERIOR_SCOPE, LOCAL_SCOPE, PRIOR_SCOPE]:
        s88Set(chartScope, stepScope, responseKey, "NULL", responseLocation)
    elif responseLocation == CHART_SCOPE:
        chartScope.responseKey = None
    elif responseLocation == STEP_SCOPE:
        stepScope.responseKey = None
    else:
        logger.errorf("Error in %s.initializeResponse():, unexpected responseLocation: %s", __name__, responseLocation)
    

def checkForTimeout(stepScope):
    '''Common code for checking the timeout of a step, generally one that has a UI'''
    timeoutTime = stepScope[TIMEOUT_TIME]

    if timeoutTime != None and time.time() > timeoutTime:
        timeout =  True        
    else:
        timeout = False

    return timeout

    
def cleanup(chartScope, stepProperties, stepScope):
    logger = getChartLogger(chartScope)
    logger.tracef("In %s.cleanup, cleaning up for a common input step...", __name__)

    try:
        database = getDatabaseName(chartScope)
        project = getProject(chartScope)
        windowId = stepScope.get(WINDOW_ID, None)
        if windowId != None:
            system.db.runUpdateQuery("delete from SfcInput where windowId = '%s'" % (windowId), database)   
            deleteAndSendClose(project, windowId, database)
    except:
        chartLogger = getChartLogger(chartScope)
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in cleanup in commonInput.py', chartLogger)
