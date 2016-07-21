'''
Created on Dec 9, 2015

@author: rforbes
'''
from system.gui import getParentWindow

controlPanelWindowPath = 'SFC/ControlPanel'
errorPopupWindowPath = 'SFC/ErrorPopup'
sfcWindowPrefix = 'SFC/'

def openControlPanel(controlPanelId, startImmediately):
    import system.nav
    cpWindow = findOpenControlPanel(controlPanelId)
    if cpWindow == None:
        cpWindow = system.nav.openWindowInstance(controlPanelWindowPath, {'controlPanelId': controlPanelId})
    else:
        cpWindow.toFront()
    if startImmediately:
        startChart(cpWindow)
        
def startChart(window):
    from ils.sfc.client.util import getStartInIsolationMode
    from ils.sfc.common.util import startChart, chartIsRunning
    import system.util, system.gui
    rootContainer = window.getRootContainer()
    cpId = rootContainer.controlPanelId
    isolationMode = getStartInIsolationMode()
    project = system.util.getProjectName()
    chartPath = getControlPanelChartPath(cpId)
    originator = system.security.getUsername()

    if not chartIsRunning(chartPath):
        startChart(chartPath, cpId, project, originator, isolationMode)
    else:
        system.gui.warningBox('This chart is already running')
        
def pauseChart(event):
    from system.sfc import pauseChart
    pauseChart(getParentWindow(event).rootContainer.chartRunId)

def resumeChart(event):
    from system.sfc import resumeChart
    resumeChart(getParentWindow(event).rootContainer.chartRunId)

def cancelChart(event):
    from system.sfc import cancelChart
    cancelChart(getParentWindow(event).rootContainer.chartRunId)
       
def updateChartStatus(event):
    '''Get the status of this panel's chart run and set the status field appropriately.
       Will show None if the chart is not running.'''
    from ils.sfc.common.util import getChartStatus
    from ils.sfc.common.constants import CANCELED
    import system.gui
    window = system.gui.getParentWindow(event)
    rootContainer = window.getRootContainer()
    runId = rootContainer.windowData.getValueAt(0,'chartRunId')
    status = getChartStatus(runId)
    statusField = window.rootContainer.getComponent('statusLabel')
    if statusField.text == '':
        oldStatus = None
    else:
        oldStatus = statusField.text
    if status != None:
        statusField.text = status
    else:
        statusField.text = ''
    if status != oldStatus and status == CANCELED:
        reset(event)
        
def reset(event):
    import system.gui
    window = system.gui.getParentWindow(event)
    rootContainer = window.getRootContainer()
    rootContainer.msgIndex = 0
    resetDb(rootContainer.controlPanelId)
    closeAllPopups()

def closeAllPopups():
    '''close all popup windows, except for control panels and error Popup (we usually cancel the chart on the first error).
       CAUTION: this will close ALL popups, for all charts!!!'''
    import system.gui, system.nav
    from ils.sfc.client.windowUtil import getWindowPath
    for window in system.gui.getOpenedWindows():
        windowPath = getWindowPath(window)
        if windowPath.startswith(sfcWindowPrefix) and windowPath != controlPanelWindowPath and windowPath != errorPopupWindowPath:
            system.nav.closeWindow(window)
       
def resetDb(controlPanelId):
    import system.db
    from ils.sfc.client.util import getDatabase
    database = getDatabase()
    system.db.runUpdateQuery("update SfcControlPanel set chartRunId = '', operation = '', msgQueue = '', enablePause = 1, enableResume = 1, enableCancel = 1 where controlPanelId = %d" % (controlPanelId), database)
    system.db.runUpdateQuery("delete from SfcDialogMsg", database)
    # order deletions so foreign key constraints are not violated:
    system.db.runUpdateQuery("delete from SfcInputChoices", database)
    system.db.runUpdateQuery("delete from SfcInput", database)
    system.db.runUpdateQuery("delete from SfcManualDataEntryTable", database)
    system.db.runUpdateQuery("delete from SfcManualDataEntry", database)
    system.db.runUpdateQuery("delete from SfcReviewFlowsTable", database)
    system.db.runUpdateQuery("delete from SfcReviewFlows", database)
    system.db.runUpdateQuery("delete from SfcReviewDataTable", database)
    system.db.runUpdateQuery("delete from SfcReviewData", database)
    system.db.runUpdateQuery("delete from SfcSaveData", database)
    system.db.runUpdateQuery("delete from SfcTimeDelayNotification", database)
    system.db.runUpdateQuery("delete from SfcWindow", database)
    #TODO: should we close all open SFC*  windows except for control panel?

def getControlPanelIdForName(controlPanelName):
    '''Get the control panel id given the name, or None'''
    import system.db
    from ils.sfc.client.util import getDatabase
    database = getDatabase()
    results = system.db.runQuery("select controlPanelId from SfcControlPanel where controlPanelName = '%s'" % (controlPanelName), database)
    if len(results) == 1:
        return results[0][0]
    else:
        return None

def createControlPanel(controlPanelName):    
    '''create a new control panel with the given name, returning the id.
       This name must be unique'''
    import system.db
    from ils.sfc.client.util import getDatabase
    database = getDatabase()
    system.db.runUpdateQuery("insert into SfcControlPanel (controlPanelName, chartPath) values ('%s', '')" % (controlPanelName), database)
    return getControlPanelIdForName(controlPanelName, False)

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

def getControlPanelIdForChartPath(chartPath):
    '''get the id of the SFC chart associated with the given chart path, or None'''
    import system.db
    from ils.sfc.client.util import getDatabase
    database = getDatabase()
    results = system.db.runQuery("select controlPanelId from SfcControlPanel where chartPath = '%s'" % (chartPath), database)
    if len(results) == 1:
        return results[0][0]
    else:
        return None

def setControlPanelChartPath(controlPanelId, chartPath):
    '''set the name of the SFC chart associated with the given control panel.
       this will fail if there is already a control panel for that chart.
       use getControlPanelForChartPath() to check'''
    from ils.sfc.client.util import getDatabase
    import system.db
    database = getDatabase()
    resetDb(controlPanelId) # remove any status from old chart
    system.db.runUpdateQuery("update SfcControlPanel set chartPath = '%s' where controlPanelId = %d" % (chartPath, controlPanelId), database)

def showMsgQueue(window):
    import system.nav
    rootContainer = window.getRootContainer()
    queueKey=rootContainer.windowData.getValueAt(0,'msgQueue')
    from ils.queue.message import view
    view(queueKey, useCheckpoint=True)

def ackMessage(window):
    from ils.sfc.common.cpmessage import acknowledgeControlPanelMessage
    from ils.sfc.client.util import getDatabase
    database = getDatabase()
    rootContainer = window.getRootContainer()
    msgIndex = rootContainer.msgIndex
    msgId = rootContainer.messages.getValueAt(msgIndex, 'id')
    acknowledgeControlPanelMessage(msgId, database)

def findOpenControlPanel(searchId):   
    import system.gui
    for window in system.gui.findWindow(controlPanelWindowPath):
        if window.getRootContainer().controlPanelId == searchId:
            return window
    return None

def openDynamicControlPanel(chartPath, startImmediately, panelName):
    '''Open a control panel to run the given chart, starting the chart
       if startImmediately is true. If no control panel is associated 
       with the given chart, use the one with the given name (creating that
       if it doesnt exist).
       This method is useful for development where a "scratch"
       control panel is used to run many different ad-hoc charts'''
    # First, check for an existing panel associated with this chart:
    controlPanelId = getControlPanelIdForChartPath(chartPath)
    if controlPanelId == None:
        # next, check for an existing panel with the given name, creating if not found:
        controlPanelId = getControlPanelIdForName(panelName)
        if controlPanelId == None:
            controlPanelId = createControlPanel(panelName)
        # re-set the panel's chart to the desired one:
        setControlPanelChartPath(controlPanelId, chartPath)
    openControlPanel(controlPanelId, startImmediately)