'''
Created on May 29, 2015

@author: rforbes
'''

def getMonitorDownloadWindow():
    ''' get the monitor download window. If it is not yet open, 
    will wait for a short period of time to try to get it.'''
    import time
    import system.gui
    for i in range(5):
        try:
            return system.gui.getWindow('SFC/MonitorDownload')
        except:
            # window not open yet
            time.sleep(2) # seconds
    return None
        
def initializeTable(window, rows, timerStart):
    from  system.dataset import toDataSet
    header = ['Timing', 'DCS Tag ID', 'Setpoint', 'Description', 'Step Time', 'PV', 'setpointColor', 'stepTimeColor', 'pvColor', 'key']    
    table = window.getRootContainer().getComponent('table')
    initialData = toDataSet(header, rows)
    table.data = initialData
    window.getRootContainer().timerStart = timerStart
  
def findRow(dataset, key):
    for row in range(dataset.rowCount):
        rowKey = dataset.getValueAt(row, 9)
        if rowKey == key:
            return row
    return -1

def updateSetpointStatus(window, key):
    from ils.sfc.common.constants import RED, ORANGE, YELLOW, WHITE 
    table = window.getRootContainer().getComponent('table')
    dataset = table.data
    row = findRow(dataset, key)
    stepTimeStatus = table.data.getValueAt(row, 7)
    pvStatus = table.data.getValueAt(row, 8)
    if stepTimeStatus == RED or pvStatus == ORANGE or pvStatus == RED or pvStatus == YELLOW:
        status = YELLOW
    else:
        status = WHITE
    updateStatus(window, key, status, 6)

def updateStepTimeStatus(window, key, data):
    updateStatus(window, key, data, 7)
    updateSetpointStatus(window, key)

def updatePVStatus(window, key, data):
    updateStatus(window, key, data, 8)
    updateSetpointStatus(window, key)

def updateStatus(window, key, data, col):
    import system.dataset
    table = window.getRootContainer().getComponent('table')
    dataset = table.data
    row = findRow(dataset, key)
    #  print 'updateStatus', key, data, row, col
    if(dataset.getValueAt(row,col) != data):
        table.data = system.dataset.setValue(dataset, row, col, data)
    
