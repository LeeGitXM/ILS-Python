'''
Created on May 29, 2015

@author: rforbes
'''
import system

# This is called when the Download GFUI window is opened.  The window is opened in response to a message sent 
# from the gateway to the client when the download GUI task runs in the gateway.  The gateway task populated the 
# SfcDownloadGUITable database table with a record for each output recipe data that will be displayed in the 
# GUI.  Nothing else has been updated in the table about the state of each record.  What we need to do 
# initially is populate the rest of the table.  
 
 
def internalFrameOpened(rootContainer):
    print "In monitorDownloads.internalFrameOpened()"

    windowId = rootContainer.windowId
    database = 'XOM'
    configureTable(windowId, database)

def update(rootContainer):
    print "In monitorDownloads.update()"

    windowId = rootContainer.windowId
    database = 'XOM'
    
    SQL = "select * from SfcDownloadGUITable where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL, database)
    
    table=rootContainer.getComponent("table")
    table.data=pds
 

# Because download GUI works in conjunction with the writeOutput and PVMonitoring block, it is possible that 
# the recipe data that we are using to configure the table for download GUI has not been filly configured. 
def configureTable(windowId, database):
    SQL = "select * from SfcDownloadGUITable where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL, database)

    for record in pds:
        recipeDataPath=record["RecipeDataPath"]
        print recipeDataPath
        tagPaths=[]
        tagPaths.append(recipeDataPath + '/timing')
        tagPaths.append(recipeDataPath + '/tagPath')
        tagPaths.append(recipeDataPath + '/targetValue')
        tagPaths.append(recipeDataPath + '/downloadStatus')
        tagPaths.append(recipeDataPath + '/pvMonitorStatus')
        tagPaths.append(recipeDataPath + '/setpointStatus')
        tagPaths.append(recipeDataPath + '/pvValue')
        tagPaths.append(recipeDataPath + '/stepTimestamp')
        
        tagValues=system.tag.readAll(tagPaths)
        timing = tagValues[0].value
        tagPath = tagValues[1].value
        targetValue = tagValues[2].value
        downloadStatus = tagValues[3].value
        pvMonitorStatus = tagValues[4].value
        setpointStatus = tagValues[5].value
        pvValue = tagValues[6].value
        pvQuality = tagValues[6].quality
        stepTimestamp = tagValues[7].value
        
        if pvValue == None:
            pvValue="NULL"

        print "PV = %s.%s" % (str(pvValue), str(pvQuality))

        SQL = "update SfcDownloadGUITable set RawTiming=%s, Timing=%s, DcsTagId='%s', SetPoint=%s, PV=%s," \
            "StepTimestamp='%s', DownloadStatus='%s', PVMonitorStatus='%s', SetpointStatus='%s'" % \
            (str(timing), str(timing), str(tagPath), str(targetValue), str(pvValue), \
             stepTimestamp, str(downloadStatus), str(pvMonitorStatus), str(setpointStatus))

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
    
