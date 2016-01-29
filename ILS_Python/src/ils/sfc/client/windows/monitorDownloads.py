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

# Obsolete comments
#Nothing else has been updated in the table about the state of each record.  What we need to do 
# initially is populate the rest of the table.
 
def internalFrameOpened(rootContainer):
    print "In monitorDownloads.internalFrameOpened()"

    update(rootContainer)
#    configureTable(windowId, database)

def update(rootContainer):
    print "In monitorDownloads.update()"

    windowId = rootContainer.windowId
    database = getDatabaseClient()
    tagProvider = getTagProviderClient()
    
    state, elapsedSeconds = fetchWindowState(windowId, database)
    
    if string.upper(state)  == "CREATED":
        initializeDatabaseTable(windowId, database, tagProvider)
        updateWindowState(windowId, database)
    
    else:
        # If the database was updated less than 10 seconds ago, then skip the update.  This is useful
        # if there are two or more client watching the same download GUI - they don't both need to do 
        # the work of reading tags and updating the database. 
        if elapsedSeconds > 10.0:
            updateDatabaseTable(windowId, database)
    
    # Now update the Vision table from the data in the database table 
    SQL = "select * from SfcDownloadGUITable where windowId = '%s' order by rawTiming, DCSTagId " % (windowId)
    pds = system.db.runQuery(SQL, database)
    
    table=rootContainer.getComponent("table")
    table.data=pds

def fetchWindowState(windowId, database):
    print "...fetching the window state..."
    
    SQL = "select State, DATEDIFF(second,Timestamp,CURRENT_TIMESTAMP) ElapsedSeconds from SfcDownloadGUI where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL, database)
    
    state = pds[0]["State"]
    elapsedSeconds = pds[0]["ElapsedSeconds"]
    
    print "Fetched State: %s, Elapsed Seconds: %s" % (state, str(elapsedSeconds))
    
    return state, elapsedSeconds

def updateWindowState(windowId, database):
    print "...updating the window state..."
    
    SQL = "update SfcDownloadGUI set state = 'updated', timestamp = CURRENT_TIMESTAMP where windowId = '%s'" % (windowId)
    rows = system.db.runUpdateQuery(SQL, database)
    
    print "Updated %i rows" % (rows)


# Because download GUI works in conjunction with the writeOutput and PVMonitoring block, it is possible that 
# the recipe data that we are using to configure the table for download GUI has not been fully configured. 
# The difference between rawTiming and timing is the final rows whose raw timing is > 1000.  When the tag 
# is actually written then timing and stepTimestamp are updated but raw Timing remains the same. 
def initializeDatabaseTable(windowId, database, tagProvider):
    print "Initializing the database table..."
    SQL = "select * from SfcDownloadGUITable where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL, database)

    # Note: the data can be an Input or an Output, which are both subclasses of IO
    # Oddly enough, Inputs do not have any additional attributes vs IO
    # get common IO attributes and set some defaults:
    for record in pds:
        recipeDataPath=record["RecipeDataPath"]
        labelAttribute=record["LabelAttribute"]
        print recipeDataPath
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
        timing = tagValues[0].value
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
            (str(timing), str(timing), displayName, str(setpoint), formattedPV, \
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
    print "Updating the database table..."
    SQL = "select * from SfcDownloadGUITable where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL, database)

    for record in pds:
        recipeDataPath=record["RecipeDataPath"]
        
        print recipeDataPath
        tagPaths=[]
        tagPaths.append(recipeDataPath + '/downloadStatus')
        tagPaths.append(recipeDataPath + '/pvMonitorStatus')
        tagPaths.append(recipeDataPath + '/setpointStatus')
        tagPaths.append(recipeDataPath + '/pvValue')
        tagPaths.append(recipeDataPath + '/timing')
        tagPaths.append(recipeDataPath + '/stepTimestamp')
        
        tagValues=system.tag.readAll(tagPaths)
        
        downloadStatus = tagValues[0].value
        pvMonitorStatus = tagValues[1].value
        setpointStatus = tagValues[2].value
        pvValue = tagValues[3].value
        pvQuality = tagValues[3].quality
        timing = tagValues[4].value
        stepTimestamp = tagValues[5].value
        
        if pvValue == None:
            pvValue="NULL"

        print "PV = %s.%s" % (str(pvValue), str(pvQuality))

        SQL = "update SfcDownloadGUITable set PV=%s,DownloadStatus='%s', PVMonitorStatus='%s', " \
            "SetpointStatus='%s', Timing=%s, StepTimestamp='%s' "\
            "where windowId = '%s' and RecipeDataPath = '%s' " % \
            (str(pvValue), str(downloadStatus), str(pvMonitorStatus), str(setpointStatus), \
             str(timing), stepTimestamp, windowId, recipeDataPath)

        system.db.runUpdateQuery(SQL, database)

def getMonitorDownloadWindow(chartRunId, timerId):
    ''' get the monitor download window. If it is not yet open, 
    will wait for a short period of time to try to get it.'''
    import time
    import system.gui 
    from system.ils.sfc.common.Constants import SFC_MONITOR_DOWNLOADS_WINDOW
    for i in range(5):
        windows = system.gui.findWindow(SFC_MONITOR_DOWNLOADS_WINDOW)
        for window in windows:
            if window.getRootContainer().timerId == timerId and \
                window.getRootContainer().instanceId == chartRunId:
                return window        
        time.sleep(2) # seconds
    return None
 
   
def updateTable(window, rows, timerStart):
    from  system.dataset import toDataSet
    print "Updating the table"
    header = ['RawTiming','Timing', 'DCS Tag ID', 'Setpoint', 'Description', 'Step Time', 'PV', 'stepStatus', 'pvStatus', 'setpointStatus']    
    table = window.getRootContainer().getComponent('table')
    newData = toDataSet(header, rows)

    # Sort the dataset by the timing
    newData = system.dataset.sort(newData, 'RawTiming')
    
    table.data = newData
    window.getRootContainer().timerStart = timerStart

def timerWorker(window):  
    import time
    from ils.sfc.client.util import sendMessageToGateway
    import system.util
    
    rootContainer = window.getRootContainer()
    
    timerField = rootContainer.getComponent('timerField')
    timerStart = rootContainer.timerStart
    if timerStart == None or timerStart == 0:
        timerField.text = "0.0"
    else:
        elapsedMinutes = (time.time() - timerStart) / 60.
        timerField.text = "%.1f" % elapsedMinutes
    
    if rootContainer.chartStopped:
        rootContainer.getComponent('abortButton').enabled = False
        rootContainer.getComponent('pauseButton').enabled = False
        rootContainer.getComponent('resumeButton').enabled = False

    if not(rootContainer.stopUpdates):
        #request an update from the gateway
        print "In timerWorker() - updating..."
#        payload = {'id': rootContainer.timerId, 'instanceId':rootContainer.instanceId}
#        project = system.util.getProjectName()
#        sendMessageToGateway(project, 'sfcUpdateDownloads', payload)
    
