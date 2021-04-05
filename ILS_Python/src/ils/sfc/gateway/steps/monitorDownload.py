'''
Created on Dec 17, 2015

This step used to be known as Download GUI

@author: rforbes
'''

import system, string
from ils.sfc.recipeData.api import s88Set, s88Get, s88GetRecipeDataId, s88GetRecipeDataIdFromStep, s88SetFromId
from ils.sfc.common.constants import PV_VALUE, PV_MONITOR_ACTIVE, PV_MONITOR_STATUS, SETPOINT_STATUS, SETPOINT_OK, STEP_PENDING, PV_NOT_MONITORED, WINDOW_ID, \
    WINDOW_PATH, BUTTON_LABEL, RECIPE_LOCATION, DOWNLOAD_STATUS, TARGET_STEP_UUID, IS_SFC_WINDOW, DOWNLOAD, \
    POSITION, SCALE, WINDOW_TITLE, MONITOR_DOWNLOADS_CONFIG, WRITE_CONFIRMED, NAME, ID, \
    TIMER_KEY, TIMER_LOCATION, TIMER_CLEAR, TIMER_SET, CLEAR_TIMER, START_TIMER, ACTUAL_TIMING, ACTUAL_DATETIME, \
    SECONDARY_SORT_KEY, SECONDARY_SORT_BY_ALPHABETICAL, SECONDARY_SORT_BY_ORDER
from system.ils.sfc import getMonitorDownloadsConfig
from ils.sfc.gateway.downloads import handleTimer
from ils.sfc.gateway.api import getIsolationMode, getChartLogger, handleUnexpectedGatewayError, sendMessageToClient, getStepProperty, getControlPanelId, \
    registerWindowWithControlPanel, getTopChartRunId, getDatabaseName

'''
I'd like the Download GUI block to work the same as PV Monitoring, but this block doesn't have a watch/monitoring setting!
The ONLY reason to put an input or output in watch mode in the PV Monitoring block is to display the PV in the download monitor block.
Since there is no way to reach out to the PV monitoring block from here, I have to assume that everything that is configured for this block 
should show up in the GUI. 
'''
IGNORE_DOWNLOAD_FLAG = False

def activate(scopeContext, stepProperties, state): 

    try:
        chartScope = scopeContext.getChartScope()
        stepScope = scopeContext.getStepScope()
        stepName=stepScope.get(NAME, "Unknown")
        stepUUID=stepScope.get(ID, "Unknown")
        database = getDatabaseName(chartScope)
        log = getChartLogger(chartScope)
        log.tracef("In monitorDownload.activate()...")
        
        print "***********************************"
        print stepScope
        print "Step UUID: ", stepUUID
        print "***********************************"
    
        timerLocation = getStepProperty(stepProperties, TIMER_LOCATION) 
        timerKey = getStepProperty(stepProperties, TIMER_KEY)
        secondarySortKey = getStepProperty(stepProperties, SECONDARY_SORT_KEY)
        log.tracef("...using timer %s.%s...", timerLocation, timerKey)
        timerRecipeDataId, timerRecipeDataType = s88GetRecipeDataId(chartScope, stepScope, timerKey, timerLocation)
         
        secondarySortKey = getStepProperty(stepProperties, SECONDARY_SORT_KEY)
        if secondarySortKey == None:
            secondarySortKey = SECONDARY_SORT_BY_ALPHABETICAL

        clearTimer = getStepProperty(stepProperties, TIMER_CLEAR)
        if clearTimer:
            handleTimer(timerRecipeDataId, CLEAR_TIMER, log, database)
            
        # This will clear and/or set the timer if the block is configured to do so               
        startTimer = getStepProperty(stepProperties, TIMER_SET)
        if startTimer:
            handleTimer(timerRecipeDataId, START_TIMER, log, database)
        
        recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION)
        
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

        log.tracef("Inserted a window with id: %s", str(windowId))
        
        SQL = "insert into SfcDownloadGUI (windowId, stepName, stepUUID, stepState, guiState, LastUpdated, TimerRecipeDataId, SecondarySortKey) "\
            " values ('%s', '%s', '%s', 'created', 'created', CURRENT_TIMESTAMP, %s, '%s')" \
            % (windowId, stepName, stepUUID, str(timerRecipeDataId), secondarySortKey)
        system.db.runUpdateQuery(SQL, database)
        
        log.infof("The step properties are: %s", str(stepProperties))
        
        # Reset the recipe data download and PV monitoring attributes
        for row in monitorDownloadsConfig.rows:
            log.tracef("Resetting recipe data with key: %s at %s", row.key, recipeLocation)
            
            recipeDataId, recipeDataType = s88GetRecipeDataId(chartScope, stepProperties, row.key, recipeLocation)
            log.tracef("...type:: %s", recipeDataType)

            if string.upper(recipeDataType) in ["OUTPUT", "OUTPUT RAMP"]:            
                download = s88Get(chartScope, stepScope, row.key + "." + DOWNLOAD, recipeLocation)
                if download or IGNORE_DOWNLOAD_FLAG:
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
                else:
                    log.tracef("Skipping output: <%s> because DOWNLOAD is False ", row.key)
            
            elif string.upper(recipeDataType) == "INPUT":
                # Initialize properties used by a PV monitoring process
                s88SetFromId(recipeDataId, recipeDataType, PV_MONITOR_ACTIVE, False, database)
                s88SetFromId(recipeDataId, recipeDataType, PV_VALUE, "NULL", database)
                s88SetFromId(recipeDataId, recipeDataType, PV_MONITOR_STATUS, PV_NOT_MONITORED, database)
                
                SQL = "insert into SfcDownloadGUITable (windowId, RecipeDataId, RecipeDataType, labelAttribute) "\
                        "values ('%s', '%s', '%s', '%s')" % (windowId, recipeDataId, recipeDataType, row.labelAttribute)
                print SQL
                system.db.runUpdateQuery(SQL, database)
        
        #TODO This is temprary to see if this is even used!
        recipeDataStepUUID = -1
        payload = {WINDOW_ID: windowId, WINDOW_PATH: windowPath, TARGET_STEP_UUID: recipeDataStepUUID, IS_SFC_WINDOW: True}
        sendMessageToClient(chartScope, messageHandler, payload)
        
        log.tracef("   Monitor Download payload: %s", str(payload))
        log.trace("...leaving monitorDownload.activate()")      
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in monitorDownload.py', log)

    return True