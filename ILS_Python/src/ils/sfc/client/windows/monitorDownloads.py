'''
Created on May 29, 2015

@author: rforbes
'''
import system, string
from ils.common.config import getDatabaseClient, getTagProviderClient

# This is called when the Download GUI window is opened.  The window is opened in response to a message sent 
# from the gateway to the client when the download GUI task runs in the gateway.  The gateway task populates the 
# SfcDownloadGUITable database table with a record for each output recipe data that will be displayed in the 
# GUI.  The Download GUI task really does no work - all it does is display information collected by the Write 
# Output and PV monitoring tasks. 
 
def internalFrameOpened(rootContainer):
    print "In monitorDownloads.internalFrameOpened()"

    state, timerTagPath = fetchWindowInfo(windowId, database)
    rootContainer.timerTagPath = timerTagPath

    update(rootContainer)

def update(rootContainer):
    print "In monitorDownloads.update()"

    windowId = rootContainer.windowId
    timerTagPath = rootContainer.timerTagPath
    database = getDatabaseClient()
    tagProvider = getTagProviderClient()
    
    state, secondsSinceLastUpdate = fetchWindowState(windowId, database)
    
    startTime = system.tag.read(timerTagPath + "/startTime").value
    
    if startTime == None:
        startTime = system.tag.read(timerTagPath).value
        if startTime != None:
            updateStartTime(windowId, startTime, database)
        
    rootContainer.startTime = startTime
    startTimeFormatted = system.db.dateFormat(startTime, "dd-MMM-yy h:mm:ss a")
    
    if string.upper(state)  == "CREATED":
        initializeDatabaseTable(windowId, database, tagProvider)
        updateWindowState(windowId, database)    
    
    else:
        # If the database was just updated, then skip the update.  This is useful
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
    ds = system.dataset.addRow(ds,0,["","",None,None,None,None,None, "", startTimeFormatted,None, "pending", "monitoring", ""])
    
    table=rootContainer.getComponent("table")
    table.data=ds

def fetchWindowInfo(windowId, database):
    print "...fetching the window info..."
    
    SQL = "select State, TimerTagPath "\
        "from SfcDownloadGUI where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL, database)

    state = pds[0]["State"]
    timerTagPath = pds[0]["TimerTagPath"]
    
    print "...fetched State: %s, tagPath: %s" % (state, timerTagPath)
    return state, timerTagPath

def fetchWindowState(windowId, database):
    print "...fetching the window state..."
    SQL = "select State, DATEDIFF(second,LastUpdated,CURRENT_TIMESTAMP) SecondsSinceLastUpdate "\
        "from SfcDownloadGUI where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL, database)
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
        recipeDataPath=record["RecipeDataPath"]
        labelAttribute=record["LabelAttribute"]
        
        tagPaths=[]
        tagPaths.append(recipeDataPath + '/timing')
        tagPaths.append(recipeDataPath + '/tagPath')
        tagPaths.append(recipeDataPath + '/value')
        tagPaths.append(recipeDataPath + '/downloadStatus')
        tagPaths.append(recipeDataPath + '/pvMonitorStatus')
        tagPaths.append(recipeDataPath + '/pvMonitorActive')
        tagPaths.append(recipeDataPath + '/setpointStatus')
        tagPaths.append(recipeDataPath + '/pvValue')
        tagPaths.append(recipeDataPath + '/stepTimestamp')
        tagPaths.append(recipeDataPath + '/description')
        tagPaths.append(recipeDataPath + '/valueType')
        tagPaths.append(recipeDataPath + '/units')
        tagPaths.append(recipeDataPath + '/guiUnits')
        
        tagValues=system.tag.readAll(tagPaths)
        rawTiming = tagValues[0].value
        tagPath = tagValues[1].value
        setpoint = tagValues[2].value
        downloadStatus = tagValues[3].value
        pvMonitorStatus = tagValues[4].value
        pvMonitorActive = tagValues[5].value
        setpointStatus = tagValues[6].value
        pvValue = tagValues[7].value
        pvQuality = tagValues[7].quality
        stepTimestamp = tagValues[8].value
        description = tagValues[9].value
        valueType = tagValues[10].value
        units = tagValues[11].value
        guiUnits = tagValues[12].value
        
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
        displayName = api.getDisplayName(tagProvider, tagPath, valueType, labelAttribute)

        if units != "":
            description = "%s (%s)" % (description, units)

        SQL = "update SfcDownloadGUITable set RawTiming=%s, Timing=%s, DcsTagId='%s', SetPoint='%s', PV='%s'," \
            "StepTimestamp='%s', DownloadStatus='%s', PVMonitorStatus='%s', SetpointStatus='%s', " \
            "Description = '%s' where windowId = '%s' and RecipeDataPath = '%s'  " % \
            (str(rawTiming), str(timing), displayName, str(setpoint), formattedPV, \
             stepTimestamp, str(downloadStatus), str(pvMonitorStatus), str(setpointStatus), \
             description, windowId, recipeDataPath)

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
        recipeDataPath=record["RecipeDataPath"]
        
        tagPaths=[]
        tagPaths.append(recipeDataPath + '/downloadStatus')
        tagPaths.append(recipeDataPath + '/pvMonitorStatus')
        tagPaths.append(recipeDataPath + '/pvMonitorActive')
        tagPaths.append(recipeDataPath + '/setpointStatus')
        tagPaths.append(recipeDataPath + '/pvValue')
        tagPaths.append(recipeDataPath + '/stepTimestamp')
        
        tagValues=system.tag.readAll(tagPaths)
        
        downloadStatus = tagValues[0].value
        pvMonitorStatus = tagValues[1].value
        pvMonitorActive = tagValues[2].value
        setpointStatus = tagValues[3].value
        pvValue = tagValues[4].value
        pvQuality = tagValues[4].quality
        stepTimestamp = tagValues[5].value
        
        if pvValue == None:
            formattedPV = ""
        elif pvMonitorActive == True:
            formattedPV = "%.2f" % pvValue
        else:
            formattedPV = "%.2f*" % pvValue

        SQL = "update SfcDownloadGUITable set PV='%s', DownloadStatus='%s', PVMonitorStatus='%s', " \
            "SetpointStatus='%s', StepTimestamp='%s' "\
            "where windowId = '%s' and RecipeDataPath = '%s' " % \
            (str(formattedPV), str(downloadStatus), str(pvMonitorStatus), str(setpointStatus), \
             stepTimestamp, windowId, recipeDataPath)

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
    timerTagPath = rootContainer.timerTagPath
    system.tag.write(timerTagPath + "/state", "stop")

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
    timerTagPath = rootContainer.timerTagPath
    system.tag.write(timerTagPath + "/state", "pause")
    
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
    timerTagPath = rootContainer.timerTagPath
    system.tag.write(timerTagPath + "/state", "resume")
    
    from system.sfc import resumeChart
    resumeChart(chartRunId)
    
def getChartRunId(rootContainer):
    windowId = rootContainer.windowId
    
    SQL = "select chartRunId from sfcControlPanel CP, sfcWindow W "\
        " where W.controlPanelId = CP.controlPanelId "\
        " and W.windowId = '%s'" % (windowId)
        
    chartRunId = system.db.runScalarQuery(SQL)
    return chartRunId

