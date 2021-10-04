'''
Created on May 29, 2015

@author: rforbes
'''
import system, string
from ils.common.config import getDatabaseClient, getTagProviderClient
from ils.sfc.recipeData.api import s88GetFromId, s88GetRecordFromId, s88SetFromId
from ils.sfc.recipeData.constants import TIMER
from ils.sfc.common.constants import SECONDARY_SORT_BY_ALPHABETICAL, SECONDARY_SORT_BY_ORDER
from ils.common.util import escapeSqlQuotes
from ils.sfc.common.util import getChartStatus
from ils.log.LogRecorder import LogRecorder
log = LogRecorder(__name__)

# This is called when the Download GUI window is opened.  The window is opened in response to a message sent 
# from the gateway to the client when the download GUI task runs in the gateway.  The gateway task populates the 
# SfcDownloadGUITable database table with a record for each output recipe data that will be displayed in the 
# GUI.  The Download GUI task really does no work - all it does is display information collected by the Write 
# Output and PV monitoring tasks. 
 
def internalFrameOpened(event):
    rootContainer = event.source.rootContainer
    window = event.source
    log.infof("In monitorDownloads.internalFrameOpened()")

    database = getDatabaseClient()
    provider = getTagProviderClient()
    windowId = rootContainer.windowId
    rootContainer.startTime = None
    
    ''' It would be a good idea to check that the tag exists, if they screwed up the gateway startup script then it may not exist. '''
    guiAdjustmentTagPath = "[%s]Configuration/SFC/sfcMaxDownloadGuiAdjustment" % provider
    exists = system.tag.exists(guiAdjustmentTagPath)
    if exists:
        maxAdjustment = system.tag.read(guiAdjustmentTagPath).value
    else:
        maxAdjustment = 1.7
        log.warnf("Using default max adjustment of %f because configuration tag %s does not exist!", maxAdjustment, guiAdjustmentTagPath)
    
    SQL = "select StepState, GuiState, TimerRecipeDataId, SecondarySortKey, StepName, StepUUID "\
        "from SfcDownloadGUI where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL, database)

    timerRecipeDataId = pds[0]["TimerRecipeDataId"]
    rootContainer.timerRecipeDataId = timerRecipeDataId
    secondarySortKey = pds[0]["SecondarySortKey"]
    rootContainer.secondarySortKey = secondarySortKey
    rootContainer.stepName = pds[0]["StepName"]
    rootContainer.stepUUID = pds[0]["StepUUID"]

    SQL = "select * from SfcWindow where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL, database)
    if len(pds) == 1:
        record = pds[0]
        rootContainer.title = record["title"]
        rootContainer.controlPanelId = record["controlPanelId"]
        
        chartRunId = record["chartRunId"]
        rootContainer.chartRunId = chartRunId
        
        chartStatus = getChartStatus(chartRunId)
        rootContainer.chartStatus = chartStatus
    else:
        print "ERROR: Unable to find information for the Download GUI in the SfcWindow table."

    update(rootContainer)
    setWindowSize(rootContainer, maxAdjustment, window)

def setWindowSize(rootContainer, maxAdjustment, window):
    log.tracef( "Setting the size of the window ...")
    table = rootContainer.getComponent("table")
    ds = table.data
    rows = ds.rowCount
    
    header = 75
    footer = 45
    rowHeight = 21
    
    windowHeight = window.getHeight()
    windowWidth = window.getWidth()
    requiredHeight = header + footer + (rows * rowHeight)
    log.tracef("The window Height is: %s, there are %s rows, the required height is: %s (max size = %s)", str(windowHeight), str(rows), str(requiredHeight), str(windowHeight * maxAdjustment))
    
    if requiredHeight > windowHeight * maxAdjustment:
        rootContainer.allRowsShowing = False
        window.setSize(int(windowWidth), int(windowHeight * maxAdjustment))
        log.tracef("The download monitor is too small to display all of the rows to be monitored, but the required size is %s, which is too much of an adjustment", str(requiredHeight))
    elif requiredHeight > windowHeight:
        log.tracef("Adjusting the window height to fit all rows.")
        rootContainer.allRowsShowing = True
        window.setSize(int(windowWidth), int(requiredHeight))
    else:
        rootContainer.allRowsShowing = True
        log.tracef("---the window is big enough---")
        
        
def update(rootContainer):
    log.infof( "In %s.update()", __name__)

    windowId = rootContainer.windowId
    timerRecipeDataId = rootContainer.timerRecipeDataId
    secondarySortKey = rootContainer.secondarySortKey
    database = getDatabaseClient()
    tagProvider = getTagProviderClient()
    
    guiState, stepState, secondsSinceLastUpdate = fetchWindowState(windowId, database)
    
    rootContainer.stepState = stepState
    
    if guiState == "Error":
        return
    
    # If this window hasn't discovered a starttime, then check if someone started the timer.
    if rootContainer.startTime == None:
#        startTime = s88GetFromStep(timerStepUUID, timerKey + ".StartTime", database)
        startTime = s88GetFromId(timerRecipeDataId, TIMER, "StartTime", database)
        if startTime != None:
            rootContainer.startTime = startTime
            updateStartTime(windowId, startTime, database)
    else:
        startTime = rootContainer.startTime
        
    if startTime == None:
        startTimeFormatted = "  "
    else:
        startTimeFormatted = system.db.dateFormat(startTime, "dd-MMM-yy h:mm:ss a")
    
    if string.upper(guiState)  == "CREATED":
        initializeDatabaseTable(windowId, database, tagProvider)
        updateWindowState(windowId, database)    
    
    else:
        '''
         If the database was just updated,  then skip the update.  This is useful
         if there are two or more client watching the same download GUI - they don't both need to do 
         the work of reading tags and updating the database. 
        '''
        if secondsSinceLastUpdate > 1.5:
            updateDatabaseTable(windowId, database)
            updateWindowState(windowId, database) 
    
    # Now update the Vision table from the data in the database table 
    if secondarySortKey == SECONDARY_SORT_BY_ALPHABETICAL:
        SQL = "select * from SfcDownloadGUITable where windowId = '%s' order by rawTiming, DCSTagId " % (windowId)
    else:
        '''
        Sort by order in the config table (SECONDARY_SORT_BY_ORDER).  The reason this works, without adding a term to the order by is that the rows
        are inserted into the database in the order that they are in the config table and if you don't specify the order, they will come out in the order that
        they go in.
        '''
        SQL = "select * from SfcDownloadGUITable where windowId = '%s' order by rawTiming " % (windowId)

    pds = system.db.runQuery(SQL, database)
    
    # Need to add a row at the top to specify the time that the download started.
    ds = system.dataset.toDataSet(pds)    
    ds = system.dataset.addRow(ds,0,["","","",None,None,None,None,None, "", startTimeFormatted,None, "pending", "monitoring", ""])
    
    table=rootContainer.getComponent("table")
    table.data=ds

def updateButtonState(rootContainer):
    log.tracef("In %s.updateButtonState()", __name__)
    
    chartRunId = rootContainer.chartRunId
    chartStatus = getChartStatus(chartRunId)
    rootContainer.chartStatus = chartStatus
    
    # Fetch the enable/disable state of the control panel command buttons.
    database = getDatabaseClient()
    SQL = "Select * from SfcControlPanel where chartRunId = '%s'" % (chartRunId)
    pds = system.db.runPrepQuery(SQL, database=database)
    
    if len(pds) <> 1:
        return
    
    record = pds[0]
    rootContainer.enableCancel = record["EnableCancel"]
    rootContainer.enablePause = record["EnablePause"]
    rootContainer.enableResume = record["EnableResume"]
    

def fetchWindowState(windowId, database):
    log.tracef( "...fetching the window state...")
    SQL = "select StepState, GuiState, DATEDIFF(second,LastUpdated,CURRENT_TIMESTAMP) SecondsSinceLastUpdate "\
        "from SfcDownloadGUI where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL, database)
    
    if len(pds) == 0:
        return "Error", 0
    
    guiState = pds[0]["GuiState"]
    stepState = pds[0]["StepState"]
    
    secondsSinceLastUpdate = pds[0]["SecondsSinceLastUpdate"]
    log.tracef("...fetched GUI State: %s, step State: %s...", guiState, stepState)
    return guiState, stepState, secondsSinceLastUpdate

def updateWindowState(windowId, database):
    log.tracef("...updating the window state...")
    SQL = "update SfcDownloadGUI set GuiState = 'updated', LastUpdated = CURRENT_TIMESTAMP where windowId = '%s'" % (windowId)
    system.db.runUpdateQuery(SQL, database)
    
def updateStartTime(windowId, startTime, database):
    log.tracef("...updating the startTime...")
    startTime=system.db.dateFormat(startTime, "MM/dd/yyyy H:mm:ss")
    startTime="%s"%(startTime)
    SQL = "update SfcDownloadGUI set StartTime = '%s' where windowId = '%s'" % (startTime, windowId)
    system.db.runUpdateQuery(SQL, database)


def initializeDatabaseTable(windowId, database, tagProvider):
    '''
    Because download GUI works in conjunction with the writeOutput and PVMonitoring block, it is possible that 
    the recipe data that we are using to configure the table for download GUI has not been fully configured. 
    The difference between rawTiming and timing is the final rows whose raw timing is > 1000.  When the tag 
    is actually written then timing and stepTimestamp are updated but raw Timing remains the same.     
    '''
    log.infof("***Initializing*** the database table...")
    SQL = "select * from SfcDownloadGUITable where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL, database)

    # Note: the data can be an Input or an Output, which are both subclasses of IO
    # Oddly enough, Inputs do not have any additional attributes vs IO
    # get common IO attributes and set some defaults:
    for record in pds:
        recipeDataId = record["RecipeDataId"]
        recipeDataType = record["RecipeDataType"]
        recipeRecord = s88GetRecordFromId(recipeDataId, recipeDataType, database)
        log.tracef("Fetched recipe record: %s", str(recipeRecord))
        
        if  string.upper(recipeDataType) in ["OUTPUT", "OUTPUT RAMP"]:
            rawTiming = recipeRecord["TIMING"]
            tagPath = recipeRecord["TAG"]
            
            valueType = string.upper(recipeRecord["VALUETYPE"])
            log.tracef("   valueType:%s", valueType)
            if valueType == "FLOAT":
                setpoint = recipeRecord["OUTPUTFLOATVALUE"]
                pvValue = recipeRecord["PVFLOATVALUE"]
            elif valueType == "INTEGER":
                setpoint = recipeRecord["OUTPUTINTEGERVALUE"]
                pvValue = recipeRecord["PVINTEGERVALUE"]
            elif valueType == "STRING":
                setpoint = recipeRecord["OUTPUTSTRINGVALUE"]
                pvValue = recipeRecord["PVSTRINGVALUE"]
            elif valueType == "BOOLEAN":
                setpoint = recipeRecord["OUTPUTBOOLEANVALUE"]
                pvValue = recipeRecord["PVBOOLEANVALUE"]
             
            downloadStatus = recipeRecord["DOWNLOADSTATUS"]
            pvMonitorStatus = recipeRecord["PVMONITORSTATUS"]
            pvMonitorActive = recipeRecord["PVMONITORACTIVE"]
            setpointStatus = recipeRecord["SETPOINTSTATUS"]
            stepTimestamp = recipeRecord["ACTUALDATETIME"]
            description = recipeRecord["DESCRIPTION"]
            valueType = recipeRecord["VALUETYPE"]
            units = recipeRecord["UNITS"]
            outputType = recipeRecord["OUTPUTTYPE"]
            
        elif string.upper(recipeDataType) == "INPUT":
            rawTiming = "NULL"
            tagPath = recipeRecord["TAG"]
            setpoint = recipeRecord["TARGETFLOATVALUE"]
            downloadStatus = "pending"   # This will make cell background white
            pvMonitorStatus = recipeRecord["PVMONITORSTATUS"]
            pvMonitorActive = recipeRecord["PVMONITORACTIVE"]
            setpointStatus = ""
            pvValue = recipeRecord["PVFLOATVALUE"]
            stepTimestamp = None
            description = recipeRecord["DESCRIPTION"]
            valueType = recipeRecord["VALUETYPE"]
            units = recipeRecord["UNITS"]
            outputType = "INPUT"
            
        else:
            print "*** Illegal recipe data type: ", recipeDataType
            return
        
        if setpoint in [None, "None"]:
            setpoint = ""
    
        if stepTimestamp == None or stepTimestamp == "None":
            stepTimestamp = ""
        else:
            stepTimestamp = system.db.dateFormat(stepTimestamp, "dd-MMM-yy h:mm:ss a")
        
        if rawTiming >=1000.0:
            timing = "NULL"
        else:
            timing = rawTiming
            
        if units in [None, "None", "-- None Selected --"]:
            units = ""
        
        if description in [None, "None"]:
            description = ""
            
        description = escapeSqlQuotes(description)
        formattedPV = formatPV(valueType, pvMonitorActive, pvValue)
        formattedSP = formatPV(valueType, True, setpoint)
        
        log.tracef("   valueType:%s, PV: %s, SP: %s", valueType, formattedPV, formattedSP)

        # Determine the DCS Tag ID - this can either be the name of the tag/UDT or the item id
        import ils.io.api as api
        displayAttribute = record["LabelAttribute"]
        displayName = api.getDisplayName(tagProvider, tagPath, valueType, displayAttribute, outputType)

        if units != "":
            description = "%s (%s)" % (description, units)

        SQL = "update SfcDownloadGUITable set RawTiming=%s, Timing=%s, DcsTagId='%s', SetPoint='%s', PV='%s'," \
            "StepTimestamp='%s', DownloadStatus='%s', PVMonitorStatus='%s', SetpointStatus='%s', " \
            "Description = '%s' where windowId = '%s' and RecipeDataId = %d  " % \
            (str(rawTiming), str(timing), displayName, formattedSP, formattedPV, \
             stepTimestamp, str(downloadStatus), str(pvMonitorStatus), str(setpointStatus), \
             description, windowId, recipeDataId)
    
        system.db.runUpdateQuery(SQL, database)

# This is very similar to the initialize method above except that it does not update rows that have already 
# completed monitoring and it only updates the really dynamic fields.   
# Because download GUI works in conjunction with the writeOutput and PVMonitoring block, it is possible that 
# the recipe data that we are using to configure the table for download GUI has not been fully configured. 
# The timing, setpoint, and ?? are not supposed to be dynamic so they don't need to be updated here.  However 
# there may be a race condition where this runs before the recipe data is completely configured.  If that 
# happens then we may need to read all tags and update all fields in database.  It doesn't seem like that 
# would be much additional overhead anyway.
def updateDatabaseTable(windowId, database):
    log.tracef("...updating the database table...")
    SQL = "select * from SfcDownloadGUITable where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL, database)

    i = 0
    for record in pds:
        recipeDataId = record["RecipeDataId"]
        recipeDataType = record["RecipeDataType"]
        recipeRecord = s88GetRecordFromId(recipeDataId, recipeDataType, database)
        
        log.tracef("Updating row %d, a %s", i, recipeDataType)
        
        if string.upper(recipeDataType) in ["OUTPUT", "OUTPUT RAMP"]:
            downloadStatus = recipeRecord["DOWNLOADSTATUS"]
            pvMonitorStatus = recipeRecord["PVMONITORSTATUS"]
            pvMonitorActive = recipeRecord["PVMONITORACTIVE"]
            setpointStatus = recipeRecord["SETPOINTSTATUS"]
            
            valueType = string.upper(recipeRecord["VALUETYPE"])
            log.tracef("   valueType:%s", valueType)
            if valueType == "FLOAT":
                pvValue = recipeRecord["PVFLOATVALUE"]
            elif valueType == "INTEGER":
                pvValue = recipeRecord["PVINTEGERVALUE"]
            elif valueType == "STRING":
                pvValue = recipeRecord["PVSTRINGVALUE"]
            elif valueType == "BOOLEAN":
                pvValue = recipeRecord["PVBOOLEANVALUE"]
                
            log.tracef("   value: %s", str(pvValue))

            stepTimestamp = recipeRecord["ACTUALDATETIME"]
            
        elif string.upper(recipeDataType) == "INPUT":
            downloadStatus = "pending"  # This will make cell background white
            pvMonitorStatus = recipeRecord["PVMONITORSTATUS"]
            pvMonitorActive = recipeRecord["PVMONITORACTIVE"]
            setpointStatus = ""
            
            valueType = string.upper(recipeRecord["VALUETYPE"])
            log.tracef("   valueType:%s", valueType)
            if valueType == "FLOAT":
                pvValue = recipeRecord["PVFLOATVALUE"]
            elif valueType == "INTEGER":
                pvValue = recipeRecord["PVINTEGERVALUE"]
            elif valueType == "STRING":
                pvValue = recipeRecord["PVSTRINGVALUE"]
            elif valueType == "BOOLEAN":
                pvValue = recipeRecord["PVBOOLEANVALUE"]
                
            stepTimestamp = None
        else:
            log.errorf("*** Illegal recipe data type: %s", recipeDataType)
            return
        
        formattedPV = formatPV(valueType, pvMonitorActive, pvValue)

        if stepTimestamp == None or stepTimestamp == "None":
            stepTimestamp = ""
        else:
            stepTimestamp = system.db.dateFormat(stepTimestamp, "dd-MMM-yy h:mm:ss a")

        SQL = "update SfcDownloadGUITable set PV='%s', DownloadStatus='%s', PVMonitorStatus='%s', " \
            "SetpointStatus='%s', StepTimestamp='%s' "\
            "where windowId = '%s' and RecipeDataId = %s " % \
            (str(formattedPV), str(downloadStatus), str(pvMonitorStatus), str(setpointStatus), \
             stepTimestamp, windowId, str(recipeDataId) )

        log.tracef("SQL: %s", SQL)
        system.db.runUpdateQuery(SQL, database)
        i = i + 1

#---------------------------------------------------------------------------------------   
# The following methods support the buttons on the download window
#
def cancelChart(event):
    print "Cancelling..."
    rootContainer = event.source.parent
        
    chartRunId = getChartRunId(rootContainer)
    if chartRunId == None:
        system.gui.warningBox("Unable to locate a chartRunId, chart cannot be cancelled")
        return

    # This might be a temporary measure as we also need to honor the Pause / resume from the control panel
    handleTimer(rootContainer, "stop")

    from system.sfc import cancelChart
    cancelChart(chartRunId)

def pauseChart(event):
    print "Pausing..."
    rootContainer = event.source.parent
        
    chartRunId = getChartRunId(rootContainer)
    if chartRunId == None:
        system.gui.warningBox("Unable to locate a chartRunId, chart cannot be cancelled")
        return

    # This might be a temporary measure as we also need to honor the Pause / resume from the control panel
    handleTimer(rootContainer, "pause") 
    
    from system.sfc import pauseChart
    pauseChart(chartRunId)

def resumeChart(event):
    print "Resuming..."
    rootContainer = event.source.parent
        
    chartRunId = getChartRunId(rootContainer)
    if chartRunId == None:
        system.gui.warningBox("Unable to locate a chartRunId, chart cannot be cancelled")
        return
    
    # This might be a temporary measure as we also need to honor the Pause / resume from the control panel
    handleTimer(rootContainer, "resume")
    
    from system.sfc import resumeChart
    resumeChart(chartRunId)
    
def getChartRunId(rootContainer):
    windowId = rootContainer.windowId
    db = getDatabaseClient()
    SQL = "select chartRunId from sfcWindow where windowId = '%s'" % (windowId)
    print SQL
    chartRunId = system.db.runScalarQuery(SQL, database=db)
    return chartRunId

def handleTimer(rootContainer, command):
    print command + "ing the timer"
    db = getDatabaseClient()
    timerRecipeDataId = rootContainer.timerRecipeDataId
    s88SetFromId(timerRecipeDataId, TIMER, "command", command, db)

def formatPV(valueType, pvMonitorActive, pvValue):
    if valueType == "FLOAT":
        if pvValue == None:
            formattedPV = ""
        elif pvMonitorActive == True:
            formattedPV = "%.2f" % pvValue
        else:
            formattedPV = "%.2f*" % pvValue
    else:
        if pvValue in [None, "NULL", ""]:
            formattedPV = ""
        elif pvMonitorActive == True:
            formattedPV = "%s" % pvValue
        else:
            formattedPV = "%s*" % (str(pvValue))
    
    return formattedPV