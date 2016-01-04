'''
Created on Dec 9, 2015

@author: rforbes
'''
from system.gui import getParentWindow
from ils.sfc.client.windowUtil import getRootContainer

def openControlPanel(controlPanelId, startImmediately):
    import system.gui
    system.gui.openWindow('SFC/ControlPanel', {'controlPanelId': controlPanelId, 'startImmediately': startImmediately})

def startChart(event):
    from ils.sfc.client.util import startChart
    rootContainer = getRootContainer(event)
    cpId = rootContainer.controlPanelId
    #TODO: check if chart is running to set canStart flag
    canStart = True
    if canStart:
        startChart(cpId)
        
def pauseChart(event):
    from system.sfc import pauseChart
    pauseChart(getParentWindow(event).rootContainer.chartRunId)

def resumeChart(event):
    from system.sfc import resumeChart
    resumeChart(getParentWindow(event).rootContainer.chartRunId)

def cancelChart(event):
    from system.sfc import cancelChart
    cancelChart(getParentWindow(event).rootContainer.chartRunId)
       
def getChartStatus(event):
    '''Get the status of this panel's chart run and set the status field appropriately.
       Will show None if the chart is not running.'''
    from ils.sfc.client.util import getChartStatus
    rootContainer = getRootContainer(event)
    statusField = rootContainer.getComponent('statusLabel')
    runId = rootContainer.windowData.getValueAt(0,'chartRunId')
    status = getChartStatus(runId)
    statusField.text = status
    
def reset(event):
    import system.db
    rootContainer = event.source.parent.parent
    database = system.tag.read('[Client]Database').value
    system.db.runUpdateQuery("update SfcControlPanel set chartRunId = '', operation = '', msgQueue = '' where controlPanelId = %d" % (rootContainer.controlPanelId), database)
    rootContainer.msgIndex = 0
    system.db.runUpdateQuery("delete from SfcReviewDataTable", database)
    system.db.runUpdateQuery("delete from SfcReviewData", database)
    system.db.runUpdateQuery("delete from SfcManualDataEntryTable", database)
    system.db.runUpdateQuery("delete from SfcManualDataEntry", database)
    system.db.runUpdateQuery("delete from SfcTimeDelayNotification", database)
    system.db.runUpdateQuery("delete from SfcInput", database)
    system.db.runUpdateQuery("delete from SfcWindow", database)

def getControlPanelChartPath(controlPanelId):
    import system.db
    results = system.db.runQuery("select chartPath from SfcControlPanel where controlPanelId = %d" % (controlPanelId))
    if len(results) == 1:
        return results[0][0]
    else:
        return None

def getControlPanelId(controlPanelName):
    import system.db
    results = system.db.runQuery("select controlPanelId from SfcControlPanel where controlPanelName = '%s'" % (controlPanelName))
    if len(results) == 1:
        return results[0][0]
    else:
        return None
    
def setControlPanelChartPath(controlPanelId, chartPath):
    import system.db
    '''start a chart using the given contrl panel and over-writing that control panel's
       chart path in the database'''
    system.db.runUpdateQuery("update SfcControlPanel set chartPath = '%s' where controlPanelId = %d" % (chartPath, controlPanelId))
     