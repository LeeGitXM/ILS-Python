'''
Created on May 29, 2015

@author: rforbes
'''

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
    header = ['Timing', 'DCS Tag ID', 'Setpoint', 'Description', 'Step Time', 'PV', 'setpointColor', 'stepTimeColor', 'pvColor']    
    table = window.getRootContainer().getComponent('table')
    newData = toDataSet(header, rows)
    table.data = newData
    window.getRootContainer().timerStart = timerStart

def timerWorker(window):  
    import time
    from ils.sfc.common.util import formatTime
    import system.util
    
    rootContainer = window.getRootContainer()
    
    clockField = rootContainer.getComponent('clockField')
    clockField.text = formatTime(time.time())
    
    timerStart = rootContainer.timerStart
    if timerStart != None:
        timerField = rootContainer.getComponent('timerField')
        elapsedMinutes = (time.time() - timerStart) / 60.
        timerField.text = "%.1f" % elapsedMinutes
    
    if rootContainer.chartStopped:
        rootContainer.getComponent('abortButton').enabled = False
        rootContainer.getComponent('pauseButton').enabled = False
        rootContainer.getComponent('resumeButton').enabled = False
    else:
        #request an update from the gateway
        payload = {'id': rootContainer.timerId, 'instanceId':rootContainer.instanceId}
        project = system.util.getProjectName()
        system.util.sendMessage(project, 'sfcUpdateDownloads', payload, "G")
    
