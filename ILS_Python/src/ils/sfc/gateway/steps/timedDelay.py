'''
Created on Dec 16, 2015

@author: rforbes
'''

import system, time
from ils.sfc.gateway.util import createWindowRecord, getControlPanelId, getStepProperty, getControlPanelName, \
    handleUnexpectedGatewayError, getDelaySeconds, sendOpenWindow, registerWindowWithControlPanel, getTopChartRunId, \
    getOriginator
from ils.sfc.gateway.api import getDatabaseName, getChartLogger, s88Get, getProject, sendMessageToClient
from ils.sfc.common.util import callMethod, isEmpty
from ils.sfc.gateway.util import getStepId, logStepDeactivated
from ils.sfc.gateway.api import getTimeFactor
from ils.sfc.common.constants import KEY, TAG, STRATEGY, STATIC, RECIPE, DELAY, \
    RECIPE_LOCATION, CALLBACK, TAG_PATH, DELAY_UNIT, POST_NOTIFICATION, WINDOW_ID, \
    BUTTON_LABEL, POSITION, SCALE, WINDOW_TITLE, MESSAGE, DEACTIVATED, ACTIVATED, PAUSED, CANCELLED, \
    DATABASE, CONTROL_PANEL_ID, CONTROL_PANEL_NAME, ORIGINATOR, WINDOW_PATH


def activate(scopeContext, stepProperties, state):
    chartScope = scopeContext.getChartScope() 
    stepScope = scopeContext.getStepScope()
    chartLogger = getChartLogger(chartScope)

    if state == DEACTIVATED:
        chartLogger.trace("Handling deactivate request for a TimedDelay block")
        logStepDeactivated(chartScope, stepProperties)
        cleanup(chartScope, stepScope, stepProperties)
        return False
       
    try:
        # Recover state from work in progress:
        endTime = stepScope.get('_endTime', None)
        postNotification = getStepProperty(stepProperties, POST_NOTIFICATION) 
        workIsDone = False
        
        if endTime == None:
            chartLogger.trace("Executing TimedDelay block - First time initialization")
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
            
            startTime = system.date.now()
            endTime = system.date.addSeconds(startTime, int(delaySeconds))
            stepScope['_endTime'] = endTime
            if postNotification:
                message = getStepProperty(stepProperties, MESSAGE) 
                # window common properties:
                database = getDatabaseName(chartScope)
                controlPanelId = getControlPanelId(chartScope)
                controlPanelName = getControlPanelName(chartScope)
                originator = getOriginator(chartScope)
                project = getProject(chartScope)
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
                
                print "Window Title:", title
                print "Window Message: ", message
                
                windowId = registerWindowWithControlPanel(chartRunId, controlPanelId, windowPath, buttonLabel, position, scale, title, database)
                stepScope[WINDOW_ID] = windowId
                
                formattedEndTime = system.date.format(endTime, "MM/dd/yyyy HH:mm:ss")
                sql = "insert into SfcTimeDelayNotification (windowId, message, endTime) values ('%s', '%s', '%s')" % (windowId, message, formattedEndTime)
                numInserted = system.db.runUpdateQuery(sql, database)
                if numInserted == 0:
                    handleUnexpectedGatewayError(chartScope, 'Failed to insert row into SfcTimeDelayNotification', chartLogger)
                
                payload = {WINDOW_ID: windowId, DATABASE: database, CONTROL_PANEL_ID: controlPanelId,\
                       CONTROL_PANEL_NAME: controlPanelName, ORIGINATOR: originator, WINDOW_PATH: windowPath}
                sendMessageToClient(project, messageHandler, payload)
                
                #sendOpenWindow(chartScope, windowId, stepId, database)
        else:
            chartLogger.trace("Executing TimedDelay block - checking for work done...")
            workIsDone = system.date.now() >= endTime
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in timedDelay.py', chartLogger)        
        workIsDone = True
    finally:
        if workIsDone:
            cleanup(chartScope, stepScope, stepProperties)
        return workIsDone
        
def cleanup(chartScope, stepScope, stepProperties):
    import system.db
    from ils.sfc.gateway.util import getStepProperty, deleteAndSendClose, handleUnexpectedGatewayError
    from ils.sfc.gateway.api import getDatabaseName, getProject, getChartLogger
    from ils.sfc.common.constants import WINDOW_ID
    from ils.sfc.common.constants import POST_NOTIFICATION
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
        chartLogger = getChartLogger(chartScope)
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in cleanup in commonInput.py', chartLogger)
    