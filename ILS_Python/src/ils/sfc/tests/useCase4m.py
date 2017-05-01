'''
Created on Apr 25, 2017

@author: phass
'''

import system, time
from ils.sfc.common.util import callMethodWithParams
from system.ils.sfc import getReviewData
from ils.sfc.common.util import isEmpty
from ils.common.cast import jsonToDict
from ils.sfc.gateway.steps.commonInput import cleanup, checkForTimeout
from ils.sfc.gateway.util import getStepProperty, getTimeoutTime, getControlPanelId, registerWindowWithControlPanel, \
        logStepDeactivated, getTopChartRunId, handleUnexpectedGatewayError, hasStepProperty
from ils.sfc.gateway.api import getDatabaseName, getChartLogger, sendMessageToClient, getProject
from ils.sfc.recipeData.api import s88Set, s88Get, s88GetTargetStepUUID
from ils.sfc.common.constants import BUTTON_LABEL, TIMED_OUT, WAITING_FOR_REPLY, TIMEOUT_TIME, \
    WINDOW_ID, POSITION, SCALE, WINDOW_TITLE, PROMPT, WINDOW_PATH, DEACTIVATED, RECIPE_LOCATION, KEY, TARGET_STEP_UUID, \
    PRIMARY_REVIEW_DATA_WITH_ADVICE, SECONDARY_REVIEW_DATA_WITH_ADVICE, PRIMARY_REVIEW_DATA, SECONDARY_REVIEW_DATA, \
    BUTTON_KEY_LOCATION, BUTTON_KEY, ACTIVATION_CALLBACK

def activationCallback(scopeContext, stepProperties):
    print "Hello there!"
    
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    
    # Test that the arguments that passed are usable
    title = getStepProperty(stepProperties, WINDOW_TITLE) 
    database = getDatabaseName(chartScope)
    windowId = stepScope[WINDOW_ID]
    
    print "--------------------------"
    print "Title:     ", title
    print "Database:  ", database
    print "Window Id: ", windowId
    print "--------------------------"