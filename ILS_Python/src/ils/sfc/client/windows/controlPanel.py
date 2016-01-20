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
    from ils.sfc.client.util import getDatabase
    rootContainer = event.source.parent.parent
    database = getDatabase()
    system.db.runUpdateQuery("update SfcControlPanel set chartRunId = '', operation = '', msgQueue = '', enablePause = 1, enableResume = 1, enableCancel = 1 where controlPanelId = %d" % (rootContainer.controlPanelId), database)
    rootContainer.msgIndex = 0
    system.db.runUpdateQuery("delete from SfcDialogMsg", database)
    system.db.runUpdateQuery("delete from SfcReviewFlowsTable", database)
    system.db.runUpdateQuery("delete from SfcReviewFlows", database)
    system.db.runUpdateQuery("delete from SfcReviewDataTable", database)
    system.db.runUpdateQuery("delete from SfcReviewData", database)
    system.db.runUpdateQuery("delete from SfcManualDataEntryTable", database)
    system.db.runUpdateQuery("delete from SfcManualDataEntry", database)
    system.db.runUpdateQuery("delete from SfcTimeDelayNotification", database)
    system.db.runUpdateQuery("delete from SfcInputChoices", database)
    system.db.runUpdateQuery("delete from SfcInput", database)
    system.db.runUpdateQuery("delete from SfcWindow", database)
    #TODO: should we close all open SFC*  windows except for control panel?

def getControlPanelId(controlPanelName, createIfNotFound = True):
    '''Get the control panel id given the name, creating a new record if not found
       and createIfNotFound flag is set.'''
    import system.db
    from ils.sfc.client.util import getDatabase
    database = getDatabase()
    results = system.db.runQuery("select controlPanelId from SfcControlPanel where controlPanelName = '%s'" % (controlPanelName), database)
    if len(results) == 1:
        return results[0][0]
    elif createIfNotFound:
        system.db.runUpdateQuery("insert into SfcControlPanel (controlPanelName, chartPath) values ('%s', '')" % (controlPanelName), database)
        return getControlPanelId(controlPanelName, False)
    else:
        return None
    
def getControlPanelChartPath(controlPanelId):
    '''get the name of the SFC chart associated with the given control panel'''
    import system.db
    from ils.sfc.client.util import getDatabase
    database = getDatabase()
    results = system.db.runQuery("select chartPath from SfcControlPanel where controlPanelId = %d" % (controlPanelId), database)
    if len(results) == 1:
        return results[0][0]
    else:
        return None

def setControlPanelChartPath(controlPanelId, chartPath):
    '''set the name of the SFC chart associated with the given control panel'''
    from ils.sfc.client.util import getDatabase
    import system.db
    database = getDatabase()
    system.db.runUpdateQuery("update SfcControlPanel set chartPath = '%s' where controlPanelId = %d" % (chartPath, controlPanelId), database)

def showMsgQueue(window):
    import system.nav
    rootContainer = window.getRootContainer()
    msgQueueWindow = system.nav.openWindow('Queue/Message Queue')
    msgQueueWindow.getRootContainer().key = rootContainer.windowData.getValueAt(0,'msgQueue')

def ackMessage(window):
    from ils.sfc.common.cpmessage import acknowledgeControlPanelMessage
    from ils.sfc.client.util import getDatabase
    database = getDatabase()
    rootContainer = window.getRootContainer()
    msgIndex = rootContainer.msgIndex
    msgId = rootContainer.messages.getValueAt(msgIndex, 'id')
    acknowledgeControlPanelMessage(msgId, database)
    