'''
Created on Dec 16, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):
    from ils.sfc.gateway.util import createWindowRecord, getControlPanelId, getStepProperty, \
        handleUnexpectedGatewayError, getDelaySeconds, checkForCancelOrPause, deleteAndSendClose, \
        sendOpenWindow
    from ils.sfc.gateway.api import getDatabaseName, getChartLogger, s88Get
    from ils.sfc.common.util import callMethod
    from ils.sfc.gateway.util import getStepId
    from ils.sfc.gateway.api import getTimeFactor
    from ils.sfc.common.constants import KEY, TAG, STRATEGY, STATIC, RECIPE, DELAY, RECIPE_LOCATION, CALLBACK, TAG_PATH, DELAY_UNIT, POST_NOTIFICATION, \
        BUTTON_LABEL, POSITION, SCALE, WINDOW_TITLE, MESSAGE
    import system.db
    import time
    
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    chartLogger = getChartLogger(chartScope)
    chartLogger.info("Executing TimedDelay block")
    stepId = getStepId(stepProperties) 
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
    chartLogger.trace("Unscaled Time delay: %f, time factor: %f, scaled time delay: %f" % (unscaledDelaySeconds, timeFactor, delaySeconds))
    startTimeEpochSecs = time.time()
    endTimeEpochSecs = startTimeEpochSecs + delaySeconds
    
    postNotification = getStepProperty(stepProperties, POST_NOTIFICATION) 
    if postNotification:
        message = getStepProperty(stepProperties, MESSAGE) 
        # window common properties:
        database = getDatabaseName(chartScope)
        controlPanelId = getControlPanelId(chartScope)
        buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL) 
        position = getStepProperty(stepProperties, POSITION) 
        scale = getStepProperty(stepProperties, SCALE) 
        title = getStepProperty(stepProperties, WINDOW_TITLE) 
        windowId = createWindowRecord(controlPanelId, 'SFC/TimeDelayNotification', buttonLabel, position, scale, title, database)
        numInserted = system.db.runUpdateQuery("insert into SfcTimeDelayNotification (windowId, message, endTime) values ('%s', '%s', %f)" % (windowId, message, endTimeEpochSecs), database)
        if numInserted == 0:
            handleUnexpectedGatewayError(chartScope, 'Failed to insert row into SfcTimeDelayNotification', chartLogger)
    sendOpenWindow(chartScope, windowId, stepId, database)
        
    #TODO: checking the real clock time is probably more accurate
    sleepIncrement = 1
    while delaySeconds > 0:
        # Handle Cancel/Pause

#        if status == CANCEL:
#            return
#        elif status == PAUSE:
#            sleep(sleepIncrement)
#            continue

        if checkForCancelOrPause(chartScope, chartLogger):
            print "CANCELLED--dropping out of loop"
            break
        
        delaySeconds = delaySeconds - sleepIncrement
        time.sleep(sleepIncrement)
    
    if postNotification:
        system.db.runUpdateQuery("delete from SfcTimeDelayNotification where windowId = '%s'" % (windowId), database)
        deleteAndSendClose(chartScope, windowId, database)