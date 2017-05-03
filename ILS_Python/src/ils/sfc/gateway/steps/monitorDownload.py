'''
Created on Dec 17, 2015

This step used to be known as Download GUI

@author: rforbes
'''

import system
from ils.sfc.recipeData.api import s88Set, s88GetTargetStepUUID
from ils.sfc.common.constants import PV_VALUE, PV_MONITOR_ACTIVE, PV_MONITOR_STATUS, SETPOINT_STATUS, SETPOINT_OK, STEP_PENDING, PV_NOT_MONITORED, WINDOW_ID, \
    WINDOW_PATH, BUTTON_LABEL, RECIPE_LOCATION, DOWNLOAD_STATUS, TARGET_STEP_UUID, IS_SFC_WINDOW, \
    POSITION, SCALE, WINDOW_TITLE, MONITOR_DOWNLOADS_CONFIG, WRITE_CONFIRMED, \
    TIMER_KEY, TIMER_LOCATION, TIMER_CLEAR, TIMER_SET, CLEAR_TIMER, START_TIMER, ACTUAL_TIMING, ACTUAL_DATETIME
from system.ils.sfc import getMonitorDownloadsConfig
from ils.sfc.gateway.downloads import handleTimer
from ils.sfc.gateway.util import sendMessageToClient, getStepProperty, handleUnexpectedGatewayError, getControlPanelId, registerWindowWithControlPanel, getTopChartRunId
from system.ils.sfc import getDatabaseName
from ils.sfc.gateway.api import getIsolationMode, getChartLogger

def activate(scopeContext, stepProperties, state): 

    try:
        chartScope = scopeContext.getChartScope()
        stepScope = scopeContext.getStepScope()
        logger = getChartLogger(chartScope)
        logger.trace("In monitorDownload.activate()...")
    
        timerLocation = getStepProperty(stepProperties, TIMER_LOCATION) 
        timerKey = getStepProperty(stepProperties, TIMER_KEY)
        timerStepUUID = s88GetTargetStepUUID(chartScope, stepScope, timerLocation)
        
        clearTimer = getStepProperty(stepProperties, TIMER_CLEAR)
        if clearTimer:
            handleTimer(chartScope, stepScope, stepProperties, timerKey, timerLocation, CLEAR_TIMER, logger)
            
        # This will clear and/or set the timer if the block is configured to do so               
        startTimer = getStepProperty(stepProperties, TIMER_SET)
        if startTimer:
            handleTimer(chartScope, stepScope, stepProperties, timerKey, timerLocation, START_TIMER, logger)
        
        recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION)
        recipeDataStepUUID = s88GetTargetStepUUID(chartScope, stepScope, recipeLocation)
        
        configJson = getStepProperty(stepProperties, MONITOR_DOWNLOADS_CONFIG)
        monitorDownloadsConfig = getMonitorDownloadsConfig(configJson)
        isolationMode = getIsolationMode(chartScope)
        chartRunId = getTopChartRunId(chartScope)
        database = getDatabaseName(isolationMode)
        
        # Insert a window record into the database
        controlPanelId = getControlPanelId(chartScope)
        buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL)
        position = getStepProperty(stepProperties, POSITION)
        scale = getStepProperty(stepProperties, SCALE)
        title = getStepProperty(stepProperties, WINDOW_TITLE)
        windowPath = "SFC/MonitorDownloads"
        messageHandler = "sfcOpenWindow"
        
        windowId = registerWindowWithControlPanel(chartRunId, controlPanelId, windowPath, buttonLabel, position, scale, title, database)
        stepScope[WINDOW_ID] = windowId # This step completes as soon as the GUI is posted do I doubt I need to save this.

        print "Inserted a window with id: ", windowId
        
        SQL = "insert into SfcDownloadGUI (windowId, state, LastUpdated, TimerStepUUID, TimerKey) values ('%s', 'created', CURRENT_TIMESTAMP, '%s', '%s')" % (windowId, timerStepUUID, timerKey)
        system.db.runUpdateQuery(SQL, database)
        
        # Reset the recipe data download and PV monitoring attributes
        for row in monitorDownloadsConfig.rows:
            logger.trace("Resetting recipe data with key: %s" % (row.key))
            
            # Initialize properties used by the write output process
            s88Set(chartScope, stepScope, row.key + "." + DOWNLOAD_STATUS, STEP_PENDING, recipeLocation)
            s88Set(chartScope, stepScope, row.key + "." + WRITE_CONFIRMED, "NULL", recipeLocation)
                
            # Initialize properties used by a PV monitoring process
            s88Set(chartScope, stepScope, row.key + "." + PV_MONITOR_ACTIVE, False, recipeLocation)
            s88Set(chartScope, stepScope, row.key + "." + PV_VALUE, "NULL", recipeLocation)
            s88Set(chartScope, stepScope, row.key + "." + PV_MONITOR_STATUS, PV_NOT_MONITORED, recipeLocation)
            s88Set(chartScope, stepScope, row.key + "." + SETPOINT_STATUS, SETPOINT_OK, recipeLocation)
            s88Set(chartScope, stepScope, row.key + "." + ACTUAL_TIMING, "NULL", recipeLocation)
            s88Set(chartScope, stepScope, row.key + "." + ACTUAL_DATETIME, "NULL", recipeLocation)
            
            SQL = "insert into SfcDownloadGUITable (windowId, RecipeDataStepUUID, RecipeDataKey, labelAttribute) "\
                "values ('%s', '%s', '%s', '%s')" % (windowId, recipeDataStepUUID, row.key, row.labelAttribute)

            system.db.runUpdateQuery(SQL, database)
        
        payload = {WINDOW_ID: windowId, WINDOW_PATH: windowPath, TARGET_STEP_UUID: recipeDataStepUUID, IS_SFC_WINDOW: True}
        sendMessageToClient(chartScope, messageHandler, payload)
        
        logger.tracef("   Monitor Download payload: %s", str(payload))
        logger.trace("...leaving monitorDownload.activate()")      
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in monitorDownload.py', logger)

    return True