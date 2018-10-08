'''
Created on Dec 17, 2015

This step used to be known as Download GUI

@author: rforbes
'''

import system
from ils.sfc.recipeData.api import s88Set, s88GetStep, s88Get, s88GetRecipeDataId, s88GetRecipeDataIdFromStep, s88SetFromId
from ils.sfc.common.constants import PV_VALUE, PV_MONITOR_ACTIVE, PV_MONITOR_STATUS, SETPOINT_STATUS, SETPOINT_OK, STEP_PENDING, PV_NOT_MONITORED, WINDOW_ID, \
    WINDOW_PATH, BUTTON_LABEL, RECIPE_LOCATION, DOWNLOAD_STATUS, TARGET_STEP_UUID, IS_SFC_WINDOW, DOWNLOAD, \
    POSITION, SCALE, WINDOW_TITLE, MONITOR_DOWNLOADS_CONFIG, WRITE_CONFIRMED, \
    TIMER_KEY, TIMER_LOCATION, TIMER_CLEAR, TIMER_SET, CLEAR_TIMER, START_TIMER, ACTUAL_TIMING, ACTUAL_DATETIME
from system.ils.sfc import getMonitorDownloadsConfig
from ils.sfc.gateway.downloads import handleTimer
from ils.sfc.gateway.api import getIsolationMode, getChartLogger, handleUnexpectedGatewayError, sendMessageToClient, getStepProperty, getControlPanelId, \
    registerWindowWithControlPanel, getTopChartRunId, getDatabaseName

def activate(scopeContext, stepProperties, state): 

    try:
        chartScope = scopeContext.getChartScope()
        stepScope = scopeContext.getStepScope()
        database = getDatabaseName(chartScope)
        logger = getChartLogger(chartScope)
        logger.tracef("In monitorDownload.activate()...")
    
        timerLocation = getStepProperty(stepProperties, TIMER_LOCATION) 
        timerKey = getStepProperty(stepProperties, TIMER_KEY)
        logger.tracef("...using timer %s.%s...", timerLocation, timerKey)
        timerRecipeDataId, timerRecipeDataType = s88GetRecipeDataId(chartScope, stepScope, timerKey, timerLocation)
        
        clearTimer = getStepProperty(stepProperties, TIMER_CLEAR)
        if clearTimer:
            handleTimer(timerRecipeDataId, CLEAR_TIMER, logger, database)
            
        # This will clear and/or set the timer if the block is configured to do so               
        startTimer = getStepProperty(stepProperties, TIMER_SET)
        if startTimer:
            handleTimer(timerRecipeDataId, START_TIMER, logger, database)
        
        recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION)
        recipeDataStepUUID, stepName = s88GetStep(chartScope, stepScope, recipeLocation)
        
        configJson = getStepProperty(stepProperties, MONITOR_DOWNLOADS_CONFIG)
        monitorDownloadsConfig = getMonitorDownloadsConfig(configJson)
        isolationMode = getIsolationMode(chartScope)
        chartRunId = getTopChartRunId(chartScope)
        
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
        
        SQL = "insert into SfcDownloadGUI (windowId, state, LastUpdated, TimerRecipeDataId) values ('%s', 'created', CURRENT_TIMESTAMP, %s)" % (windowId, str(timerRecipeDataId) )
        system.db.runUpdateQuery(SQL, database)
        
        # Reset the recipe data download and PV monitoring attributes
        for row in monitorDownloadsConfig.rows:
            logger.trace("Resetting recipe data with key: %s at %s" % (row.key, recipeLocation))
            
            download = s88Get(chartScope, stepScope, row.key + "." + DOWNLOAD, recipeLocation)
            if download:
                recipeDataId, recipeDataType = s88GetRecipeDataId(chartScope, stepProperties, row.key, recipeLocation)
                
                # Initialize properties used by the write output process
                s88SetFromId(recipeDataId, recipeDataType, DOWNLOAD_STATUS, STEP_PENDING, database)
                s88SetFromId(recipeDataId, recipeDataType, WRITE_CONFIRMED, "NULL", database)
                    
                # Initialize properties used by a PV monitoring process
                s88SetFromId(recipeDataId, recipeDataType, PV_MONITOR_ACTIVE, False, database)
                s88SetFromId(recipeDataId, recipeDataType, PV_VALUE, "NULL", database)
                s88SetFromId(recipeDataId, recipeDataType, PV_MONITOR_STATUS, PV_NOT_MONITORED, database)
                s88SetFromId(recipeDataId, recipeDataType, SETPOINT_STATUS, SETPOINT_OK, database)
                s88SetFromId(recipeDataId, recipeDataType, ACTUAL_TIMING, "NULL", database)
                s88SetFromId(recipeDataId, recipeDataType, ACTUAL_DATETIME, "NULL", database)
                
                SQL = "insert into SfcDownloadGUITable (windowId, RecipeDataId, RecipeDataType, labelAttribute) "\
                    "values ('%s', '%s', '%s', '%s')" % (windowId, recipeDataId, recipeDataType, row.labelAttribute)
    
                system.db.runUpdateQuery(SQL, database)
        
        payload = {WINDOW_ID: windowId, WINDOW_PATH: windowPath, TARGET_STEP_UUID: recipeDataStepUUID, IS_SFC_WINDOW: True}
        sendMessageToClient(chartScope, messageHandler, payload)
        
        logger.tracef("   Monitor Download payload: %s", str(payload))
        logger.trace("...leaving monitorDownload.activate()")      
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in monitorDownload.py', logger)

    return True