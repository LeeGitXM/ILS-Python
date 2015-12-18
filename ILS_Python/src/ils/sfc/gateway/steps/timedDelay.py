'''
Created on Dec 16, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):
    from ils.sfc.gateway.util import getStepProperty, handleUnexpectedGatewayError, getDelaySeconds, getStepName, checkForCancelOrPause, sendMessageToClient, getTopChartRunId
    from ils.sfc.gateway.api import getChartLogger, s88Get
    from ils.sfc.common.util import createUniqueId, callMethod
    from ils.sfc.gateway.api import getTimeFactor
    from ils.sfc.common.constants import KEY, TAG, STRATEGY, STATIC, RECIPE, DELAY, RECIPE_LOCATION, CALLBACK, TAG_PATH, DELAY_UNIT, POST_NOTIFICATION, CHART_NAME, STEP_NAME, CHART_RUN_ID, MESSAGE, ACK_REQUIRED, WINDOW_ID, END_TIME
    
    import time
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    logger = getChartLogger(chartScope)
    logger.info("Executing TimedDelay block")
    timeDelayStrategy = getStepProperty(stepProperties, STRATEGY) 
    if timeDelayStrategy == STATIC:
        delay = getStepProperty(stepProperties, DELAY) 
    elif timeDelayStrategy == RECIPE:
        recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
        key = getStepProperty(stepProperties, KEY) 
        delay = s88Get(chartScope, stepScope, key, recipeLocation)
    elif timeDelayStrategy == CALLBACK:
        callback = getStepProperty(stepProperties, CALLBACK) 
        delay = callMethod(callback)
    elif timeDelayStrategy == TAG:
        from ils.sfc.gateway.api import readTag
        tagPath = getStepProperty(stepProperties, TAG_PATH)
        delay = readTag(chartScope, tagPath)
    else:
        handleUnexpectedGatewayError(chartScope, "unknown delay strategy: " + str(timeDelayStrategy))
        delay = 0
        
    delayUnit = getStepProperty(stepProperties, DELAY_UNIT)
    delaySeconds = getDelaySeconds(delay, delayUnit)
    unscaledDelaySeconds=delaySeconds
    timeFactor = getTimeFactor(chartScope)
    delaySeconds = delaySeconds * timeFactor
    logger.trace("Unscaled Time delay: %f, time factor: %f, scaled time delay: %f" % (unscaledDelaySeconds, timeFactor, delaySeconds))
    startTimeEpochSecs = time.time()
    endTimeEpochSecs = startTimeEpochSecs + delaySeconds
    postNotification = getStepProperty(stepProperties, POST_NOTIFICATION) 
    if postNotification:
        payload = dict()
        payload[CHART_NAME] = chartScope.chartPath
        payload[STEP_NAME] = getStepName(stepProperties)
        payload[CHART_RUN_ID] = getTopChartRunId(chartScope)
        payload[MESSAGE] = str(delay) + ' ' + delayUnit + " remaining."
        payload[ACK_REQUIRED] = False
        payload[WINDOW_ID] = createUniqueId()
        payload[END_TIME] = endTimeEpochSecs
        sendMessageToClient(chartScope, 'sfcPostDelayNotification', payload)
    
    #TODO: checking the real clock time is probably more accurate
    sleepIncrement = 1
    while delaySeconds > 0:
        # Handle Cancel/Pause

#        if status == CANCEL:
#            return
#        elif status == PAUSE:
#            sleep(sleepIncrement)
#            continue

        if checkForCancelOrPause(chartScope, logger):
            print "CANCELLED--dropping out of loop"
            return
        
        delaySeconds = delaySeconds - sleepIncrement
        time.sleep(sleepIncrement)
    
    if postNotification:
        sendMessageToClient(chartScope, 'sfcDeleteDelayNotification', payload)
