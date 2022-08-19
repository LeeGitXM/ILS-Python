'''
Created on Dec 16, 2015

@author: rforbes
'''

import system
from ils.sfc.recipeData.api import s88Get
from ils.sfc.gateway.api import getDatabaseName, getChartLogger, getProject, handleUnexpectedGatewayError, sendMessageToClient, readTag, logStepDeactivated, \
    getControlPanelId, getStepProperty, getControlPanelName, getDelaySeconds, registerWindowWithControlPanel, getTopChartRunId, getOriginator, deleteAndSendClose,\
    notifyGatewayError
from ils.sfc.common.util import isEmpty, callMethodWithParams
from ils.sfc.gateway.api import getTimeFactor
from ils.sfc.common.constants import KEY, TAG, STRATEGY, STATIC, RECIPE, DELAY, CHART_SCOPE, \
    RECIPE_LOCATION, CALLBACK, TAG_PATH, DELAY_UNIT, POST_NOTIFICATION, WINDOW_ID, \
    BUTTON_LABEL, POSITION, SCALE, WINDOW_TITLE, MESSAGE, DEACTIVATED, \
    DATABASE, CONTROL_PANEL_ID, CONTROL_PANEL_NAME, ORIGINATOR, WINDOW_PATH, STEP_NAME, IS_SFC_WINDOW

def activate(scopeContext, stepProperties, state):
    chartScope = scopeContext.getChartScope() 
    stepScope = scopeContext.getStepScope()
    log = getChartLogger(chartScope)
    stepName = getStepProperty(stepProperties, STEP_NAME)
    log.tracef("In %s.activate() with %s", __name__, stepName)

    # This really does not do what I expect.  First of all, if I cancel the chart while this step is running, this is not called.
    # Second, This is called when this block is placed in a loop AFTER the first time through.  This behavior does not make any sense, 
    # I'm not sure if this is getting screwed up in our Java layer or is the engine a little wonky.
    if state == DEACTIVATED:
        log.tracef("Handling deactivate request for a TimedDelay block named %s", stepName)
        stepScope['_endTime'] = None
        logStepDeactivated(chartScope, stepProperties)
        cleanup(chartScope, stepScope, stepProperties)
        return True
       
    try:
        # Recover state from work in progress:
        endTime = stepScope.get('_endTime', None)
        postNotification = getStepProperty(stepProperties, POST_NOTIFICATION) 
        workIsDone = False
        firstTime = False
        
        if endTime == None:
            log.tracef("Executing TimedDelay block %s - First time initialization", stepName)
            startTime = system.date.now()
            stepScope['_startTime'] = startTime
            firstTime = True

        else:
            startTime = stepScope['_startTime']
            
        # Do the calculations every time through because, depending on the strategy, the desired delay could change
        timeDelayStrategy = getStepProperty(stepProperties, STRATEGY) 
        log.tracef("...the strategy is %s", timeDelayStrategy)
        if timeDelayStrategy == STATIC:
            delay = getStepProperty(stepProperties, DELAY) 
        elif timeDelayStrategy == RECIPE:
            recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION)
            key = getStepProperty(stepProperties, KEY)
            log.tracef("  Getting the delay from %s.%s", recipeLocation, key)
            delay = s88Get(chartScope, stepScope, key, recipeLocation)
            log.tracef("    ...the raw delay is %s", str(delay))
        elif timeDelayStrategy == CALLBACK:
            callback = getStepProperty(stepProperties, CALLBACK)                 
            keys = ['scopeContext', 'stepProperties']
            values = [scopeContext, stepProperties]
            delay = callMethodWithParams(callback, keys, values)
        elif timeDelayStrategy == TAG:
            tagPath = getStepProperty(stepProperties, TAG_PATH)
            delay = readTag(chartScope, tagPath)
        elif timeDelayStrategy == CHART_SCOPE:
            key = getStepProperty(stepProperties, KEY)
            log.tracef("  Getting the delay from chart.%s", key)
            delay = chartScope.get(key, None)
            if delay == None:
                delay = 5
                notifyGatewayError(chartScope, stepProperties, "Chart scope variable named <%s> was not found, using default 5 second delay" % (key), log)
        else:
            handleUnexpectedGatewayError(chartScope, "unknown delay strategy: " + str(timeDelayStrategy))
            delay = 0

        delayUnit = getStepProperty(stepProperties, DELAY_UNIT)
        delaySeconds = getDelaySeconds(delay, delayUnit)
        unscaledDelaySeconds=delaySeconds
        timeFactor = getTimeFactor(chartScope)
        delaySeconds = delaySeconds * timeFactor
        log.tracef("Unscaled Time delay: %s, time factor: %s, scaled time delay: %s", str(unscaledDelaySeconds), str(timeFactor), str(delaySeconds))

        stepScope['tooltip'] = "Starting a %s second delay" % (str(unscaledDelaySeconds))
        
        endTime = system.date.addSeconds(startTime, int(delaySeconds))
        log.tracef("The end time is: %s", str(endTime))
        stepScope['_endTime'] = endTime

        secondsLeft = system.date.secondsBetween(system.date.now(), endTime)
        if secondsLeft > 60 * 60:
            hoursLeft = round(10.0 * secondsLeft / (60.0 * 60.0)) / 10.0
            tooltip = "%s hours left" % ( str(hoursLeft) )
        elif secondsLeft > 60:
            minutesLeft = round(10.0 * secondsLeft / 60.0 ) / 10.0
            tooltip = "%s minutes left" % ( str(minutesLeft) )
        else:
            tooltip = "%s seconds left..." % (str(secondsLeft))
            
        stepScope['tooltip'] = tooltip
        log.tracef("Executing TimedDelay block %s - %s...", stepName, tooltip)
        
        workIsDone = system.date.now() >= endTime
        if workIsDone:
            log.tracef("TimedDelay block %s IS DONE!", stepName)
        elif firstTime and postNotification:
            message = getStepProperty(stepProperties, MESSAGE) 
            # window common properties:
            database = getDatabaseName(chartScope)
            controlPanelId = getControlPanelId(chartScope)
            controlPanelName = getControlPanelName(chartScope)
            originator = getOriginator(chartScope)
            database = getDatabaseName(chartScope)
            chartRunId = getTopChartRunId(chartScope)
            
            buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL) 
            if isEmpty(buttonLabel):
                buttonLabel = 'Delay'
            position = getStepProperty(stepProperties, POSITION) 
            scale = getStepProperty(stepProperties, SCALE) 
            title = getStepProperty(stepProperties, WINDOW_TITLE) 
            message = getStepProperty(stepProperties, MESSAGE) 
            windowPath = 'SFC/TimeDelayNotification'
            messageHandler = "sfcOpenWindow"
            
            windowId = registerWindowWithControlPanel(chartRunId, controlPanelId, windowPath, buttonLabel, position, scale, title, database)
            stepScope[WINDOW_ID] = windowId
            
            formattedEndTime = system.date.format(endTime, "MM/dd/yyyy HH:mm:ss")
            sql = "insert into SfcTimeDelayNotification (windowId, message, endTime) values ('%s', '%s', '%s')" % (windowId, message, formattedEndTime)
            numInserted = system.db.runUpdateQuery(sql, database)
            if numInserted == 0:
                handleUnexpectedGatewayError(chartScope, stepProperties, 'Failed to insert row into SfcTimeDelayNotification', log)
            
            payload = {WINDOW_ID: windowId, DATABASE: database, CONTROL_PANEL_ID: controlPanelId,\
                   CONTROL_PANEL_NAME: controlPanelName, ORIGINATOR: originator, WINDOW_PATH: windowPath, IS_SFC_WINDOW: True}
            sendMessageToClient(chartScope, messageHandler, payload)
            
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in timedDelay.py', log)        
        workIsDone = True
    finally:
        if workIsDone:
            cleanup(chartScope, stepScope, stepProperties)
            
            # This will get the block ready in the event it is in a loop
            stepScope['_endTime'] = None
        return workIsDone
        
def cleanup(chartScope, stepScope, stepProperties):
    import system.db

    try:
        database = getDatabaseName(chartScope)
        project = getProject(chartScope)
        windowId = stepScope.get(WINDOW_ID, None)
        postNotification = getStepProperty(stepProperties, POST_NOTIFICATION) 
        if postNotification:
            system.db.runUpdateQuery("delete from SfcTimeDelayNotification where windowId = '%s'" % (windowId), database)
            project = getProject(chartScope)
            deleteAndSendClose(project, windowId, database)
    except:
        log = getChartLogger(chartScope)
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in cleanup in commonInput.py', log)
    