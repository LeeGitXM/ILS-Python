'''
Created on May 29, 2015

@author: rforbes
'''
import system

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
        print "In timerWorker() - Request an update..."
        payload = {'id': rootContainer.timerId, 'instanceId':rootContainer.instanceId}
        project = system.util.getProjectName()
        sendMessageToGateway(project, 'sfcUpdateDownloads', payload)
    
