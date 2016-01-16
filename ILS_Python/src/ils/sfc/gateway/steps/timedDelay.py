'''
Created on Dec 16, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):
    from ils.sfc.gateway.util import createWindowRecord, getControlPanelId, getStepProperty, \
        handleUnexpectedGatewayError, getDelaySeconds, checkForCancelOrPause, deleteAndSendClose, \
        sendOpenWindow
    from ils.sfc.gateway.api import getDatabaseName, getChartLogger, s88Get, getProject
    from ils.sfc.common.util import callMethod, isEmpty
    from ils.sfc.gateway.util import getStepId
    from ils.sfc.gateway.api import getTimeFactor
    from ils.sfc.common.constants import KEY, TAG, STRATEGY, STATIC, RECIPE, DELAY, RECIPE_LOCATION, CALLBACK, TAG_PATH, DELAY_UNIT, POST_NOTIFICATION, \
        BUTTON_LABEL, POSITION, SCALE, WINDOW_TITLE, MESSAGE
    import system.db
    import time
    print 'timedDelay.py: activate'
    try:
        chartScope = scopeContext.getChartScope()
        stepScope = scopeContext.getStepScope()
        chartLogger = getChartLogger(chartScope)
        
        # Recover state from work in progress:
        endTimeEpochSecs = stepScope.get('_endTimeEpochSecs', None)
        postNotification = getStepProperty(stepProperties, POST_NOTIFICATION) 
        workIsDone = True # in case of error, this will prevent more calls
        
        if endTimeEpochSecs == None:
            print 'first time--initializing'
            chartLogger.trace("Executing TimedDelay block")
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
            stepScope['_endTimeEpochSecs'] = endTimeEpochSecs
            if postNotification:
                message = getStepProperty(stepProperties, MESSAGE) 
                # window common properties:
                database = getDatabaseName(chartScope)
                controlPanelId = getControlPanelId(chartScope)
                buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL) 
                if isEmpty(buttonLabel):
                    buttonLabel = 'Delay'
                position = getStepProperty(stepProperties, POSITION) 
                scale = getStepProperty(stepProperties, SCALE) 
                title = getStepProperty(stepProperties, WINDOW_TITLE) 
                windowId = createWindowRecord(controlPanelId, 'SFC/TimeDelayNotification', buttonLabel, position, scale, title, database)
                numInserted = system.db.runUpdateQuery("insert into SfcTimeDelayNotification (windowId, message, endTime) values ('%s', '%s', %f)" % (windowId, message, endTimeEpochSecs), database)
                if numInserted == 0:
                    handleUnexpectedGatewayError(chartScope, 'Failed to insert row into SfcTimeDelayNotification', chartLogger)
                sendOpenWindow(chartScope, windowId, stepId, database)
            
        secondsLeft = endTimeEpochSecs - time.time()
        sleepSeconds = min(secondsLeft, 5)
        print 'sleeping for 5 secs'
        time.sleep(sleepSeconds)
        workIsDone = sleepSeconds == secondsLeft
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in timedDelay.py', chartLogger)        
        return True
    finally:
        if workIsDone:
            print 'done; cleaning up'
            if postNotification:
                system.db.runUpdateQuery("delete from SfcTimeDelayNotification where windowId = '%s'" % (windowId), database)
                project = getProject(chartScope)
                deleteAndSendClose(project, windowId, database)
            return True
        else:
            print 'not done yet'
            return False