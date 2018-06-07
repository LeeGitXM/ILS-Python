'''
Created on May 29, 2015

@author: rforbes
'''
import system, string
from ils.common.config import getDatabaseClient, getTagProviderClient
from ils.sfc.recipeData.api import s88GetFromStep, s88GetRecord, s88SetFromName,\
    s88SetFromStep
from ils.common.util import formatDateTime

# This is called when the Download GUI window is opened.  The window is opened in response to a message sent 
# from the gateway to the client when the download GUI task runs in the gateway.  The gateway task populates the 
# SfcDownloadGUITable database table with a record for each output recipe data that will be displayed in the 
# GUI.  The Download GUI task really does no work - all it does is display information collected by the Write 
# Output and PV monitoring tasks. 
 
def internalFrameOpened(event):
    rootContainer = event.source.rootContainer
    window = event.source
    print "In monitorDownloads.internalFrameOpened()"

    database = getDatabaseClient()
    windowId = rootContainer.windowId
    
    SQL = "select State, TimerStepUUID, TimerKey from SfcDownloadGUI where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL, database)

    timerStepUUID = pds[0]["TimerStepUUID"]
    timerKey =  pds[0]["TimerKey"]

    rootContainer.startTime = None
    rootContainer.timerStepUUID = timerStepUUID
    rootContainer.timerKey = timerKey

    SQL = "select * from SfcWindow where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL, database)
    if len(pds) == 1:
        record = pds[0]
        rootContainer.title = record["title"]
        rootContainer.controlPanelId = record["controlPanelId"]
        rootContainer.chartRunId = record["chartRunId"]
    else:
        print "ERROR: Unable to find information for the Download GUI in the SfcWindow table."

    update(rootContainer)
    setWindowSize(rootContainer, window)

def setWindowSize(rootContainer, window):
    print "Setting the size of the window ..."
    table = rootContainer.getComponent("table")
    ds = table.data
    rows = ds.rowCount
    
    header = 75
    footer = 45
    rowHeight = 21
    maxAdjustment = 1.5
    
    windowHeight = window.getHeight()
    windowWidth = window.getWidth()
    requiredHeight = header + footer + (rows * rowHeight)
    print "The window Height is: %d, there are %d rows, the required height is: %d" % (windowHeight, rows, requiredHeight)
    if requiredHeight > windowHeight * maxAdjustment:
        system.gui.warningBox("The Download monitor window is too small to display all of the outputs!")
        print "The download monitor is too small to display all of the rows to be monitored, but the required size is more than %f times larger than the window, which is too much of an adjstment"
    elif requiredHeight > windowHeight:
        print "Adjusting the window height to fit all rows."
        window.setSize(int(windowWidth), int(requiredHeight))
        
        
def update(rootContainer):
    print "In monitorDownloads.update()"

    windowId = rootContainer.windowId
    timerStepUUID = rootContainer.timerStepUUID
    timerKey = rootContainer.timerKey
    database = getDatabaseClient()
    tagProvider = getTagProviderClient()
    
    state, secondsSinceLastUpdate = fetchWindowState(windowId, database)
    
    if state == "Error":
        return
    
    # If this window hasn't discovered a starttime, then check if someone started the timer.
    if rootContainer.startTime == None:
        startTime = s88GetFromStep(timerStepUUID, timerKey + ".StartTime", database)
        if startTime != None:
            rootContainer.startTime = startTime
            updateStartTime(windowId, startTime, database)
    else:
        startTime = rootContainer.startTime
        
    if startTime == None:
        startTimeFormatted = "  "
    else:
        startTimeFormatted = system.db.dateFormat(startTime, "dd-MMM-yy h:mm:ss a")
    
    if string.upper(state)  == "CREATED":
        initializeDatabaseTable(windowId, database, tagProvider)
        updateWindowState(windowId, database)    
    
    else:
        # If the database was just updated,  then skip the update.  This is useful
        # if there are two or more client watching the same download GUI - they don't both need to do 
        # the work of reading tags and updating the database. 
        if secondsSinceLastUpdate > 1.5:
            updateDatabaseTable(windowId, database)
            updateWindowState(windowId, database) 
    
    # Now update the Vision table from the data in the database table 
    SQL = "select * from SfcDownloadGUITable where windowId = '%s' order by rawTiming, DCSTagId " % (windowId)
    pds = system.db.runQuery(SQL, database)
    
    # Need to add a row at the top to specify the time that the download started.
    ds = system.dataset.toDataSet(pds)    
    ds = system.dataset.addRow(ds,0,["","","",None,None,None,None,None, "", startTimeFormatted,None, "pending", "monitoring", ""])
    
    table=rootContainer.getComponent("table")
    table.data=ds

def updateButtonState(rootContainer):
    print "In %s.updateButtonState()" % (__name__)
    
    chartRunId = rootContainer.chartRunId
    
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
    print "...fetching the window state..."
    SQL = "select State, DATEDIFF(second,LastUpdated,CURRENT_TIMESTAMP) SecondsSinceLastUpdate "\
        "from SfcDownloadGUI where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL, database)
    
    if len(pds) == 0:
        return "Error", 0
    
    state = pds[0]["State"]
    secondsSinceLastUpdate = pds[0]["SecondsSinceLastUpdate"]
    print "...fetched State: %s..." % (state)
    return state, secondsSinceLastUpdate

def updateWindowState(windowId, database):
    print "...updating the window state..."
    SQL = "update SfcDownloadGUI set state = 'updated', LastUpdated = CURRENT_TIMESTAMP where windowId = '%s'" % (windowId)
    system.db.runUpdateQuery(SQL, database)
    
def updateStartTime(windowId, startTime, database):
    print "...updating the startTime..."
    startTime=system.db.dateFormat(startTime, "MM/dd/yyyy H:mm:ss")
    startTime="%s"%(startTime)
    SQL = "update SfcDownloadGUI set StartTime = '%s' where windowId = '%s'" % (startTime, windowId)
    system.db.runUpdateQuery(SQL, database)


# Because download GUI works in conjunction with the writeOutput and PVMonitoring block, it is possible that 
# the recipe data that we are using to configure the table for download GUI has not been fully configured. 
# The difference between rawTiming and timing is the final rows whose raw timing is > 1000.  When the tag 
# is actually written then timing and stepTimestamp are updated but raw Timing remains the same. 
def initializeDatabaseTable(windowId, database, tagProvider):
    print "***Initializing*** the database table..."
    SQL = "select * from SfcDownloadGUITable where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL, database)

    # Note: the data can be an Input or an Output, which are both subclasses of IO
    # Oddly enough, Inputs do not have any additional attributes vs IO
    # get common IO attributes and set some defaults:
    for record in pds:
        recipeDataStepUUID = record["RecipeDataStepUUID"]
        recipeDataKey = record["RecipeDataKey"]
        
        recipeRecord = s88GetRecord(recipeDataStepUUID, recipeDataKey, database)
        print "Fetched recipe record: ", recipeRecord

        rawTiming = recipeRecord["TIMING"]
        tagPath = recipeRecord["TAG"]
        setpoint = recipeRecord["OUTPUTFLOATVALUE"]
        downloadStatus = recipeRecord["DOWNLOADSTATUS"]
        pvMonitorStatus = recipeRecord["PVMONITORSTATUS"]
        pvMonitorActive = recipeRecord["PVMONITORACTIVE"]
        setpointStatus = recipeRecord["SETPOINTSTATUS"]
        pvValue = recipeRecord["PVFLOATVALUE"]
        stepTimestamp = recipeRecord["ACTUALDATETIME"]
        description = recipeRecord["DESCRIPTION"]
        valueType = recipeRecord["VALUETYPE"]
        units = recipeRecord["UNITS"]
#        guiUnits = tagValues[12].value

        if stepTimestamp == None or stepTimestamp == "None":
            stepTimestamp = ""
        else:
            stepTimestamp = system.db.dateFormat(stepTimestamp, "dd-MMM-yy h:mm:ss a")
        
        if rawTiming >=1000.0:
            timing = "NULL"
        else:
            timing = rawTiming
            
        if pvValue == None:
            formattedPV = ""
        elif pvMonitorActive == True:
            formattedPV = "%.2f" % pvValue
        else:
            formattedPV = "%.2f*" % pvValue

        # Determine the DCS Tag ID - this can either be the name of the tag/UDT or the item id
        import ils.io.api as api
        displayAttribute = record["LabelAttribute"]
        displayName = api.getDisplayName(tagProvider, tagPath, valueType, displayAttribute)

        if units != "":
            description = "%s (%s)" % (description, units)

        SQL = "update SfcDownloadGUITable set RawTiming=%s, Timing=%s, DcsTagId='%s', SetPoint='%s', PV='%s'," \
            "StepTimestamp='%s', DownloadStatus='%s', PVMonitorStatus='%s', SetpointStatus='%s', " \
            "Description = '%s' where windowId = '%s' and RecipeDataKey = '%s'  " % \
            (str(rawTiming), str(timing), displayName, str(setpoint), formattedPV, \
             stepTimestamp, str(downloadStatus), str(pvMonitorStatus), str(setpointStatus), \
             description, windowId, recipeDataKey)

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
    print "...updating the database table..."
    SQL = "select * from SfcDownloadGUITable where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL, database)

    for record in pds:
        recipeDataStepUUID = record["RecipeDataStepUUID"]
        recipeDataKey = record["RecipeDataKey"]
        
        recipeRecord = s88GetRecord(recipeDataStepUUID, recipeDataKey, database)
        
        downloadStatus = recipeRecord["DOWNLOADSTATUS"]
        pvMonitorStatus = recipeRecord["PVMONITORSTATUS"]
        pvMonitorActive = recipeRecord["PVMONITORACTIVE"]
        setpointStatus = recipeRecord["SETPOINTSTATUS"]
        pvValue = recipeRecord["PVFLOATVALUE"]
        stepTimestamp = recipeRecord["ACTUALDATETIME"]
        
        if pvValue == None:
            formattedPV = ""
        elif pvMonitorActive == True:
            formattedPV = "%.2f" % pvValue
        else:
            formattedPV = "%.2f*" % pvValue

        if stepTimestamp == None or stepTimestamp == "None":
            stepTimestamp = ""
        else:
            stepTimestamp = system.db.dateFormat(stepTimestamp, "dd-MMM-yy h:mm:ss a")

        SQL = "update SfcDownloadGUITable set PV='%s', DownloadStatus='%s', PVMonitorStatus='%s', " \
            "SetpointStatus='%s', StepTimestamp='%s' "\
            "where windowId = '%s' and RecipeDataKey = '%s' " % \
            (str(formattedPV), str(downloadStatus), str(pvMonitorStatus), str(setpointStatus), \
             stepTimestamp, windowId, recipeDataKey)

        system.db.runUpdateQuery(SQL, database)

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
    timerStepUUID = rootContainer.timerStepUUID
    timerKey = rootContainer.timerKey
    s88SetFromStep(timerStepUUID, timerKey + ".command", command, db)

