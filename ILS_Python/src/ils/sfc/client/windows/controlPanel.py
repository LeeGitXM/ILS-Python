'''
Created on Dec 9, 2015

@author: rforbes
'''

import system
from ils.sfc.client.util import getDatabase
from ils.sfc.common.util import handleUnexpectedClientError
controlPanelWindowPath = 'SFC/ControlPanel'
errorPopupWindowPath = 'SFC/ErrorPopup'
sfcWindowPrefix = 'SFC/'

def internalFrameOpened(event):
    print "In internalFrameOpened..."
    rootContainer = event.source.rootContainer
    rootContainer.selectedMessage=0
    rootContainer.autoIndex=True
    
def openControlPanel(controlPanelName, startImmediately):
    print "In openControlPanel..."
    cpWindow = findOpenControlPanel(controlPanelName)
    if cpWindow == None:
        cpWindow = system.nav.openWindowInstance(controlPanelWindowPath, {'controlPanelName': controlPanelName})
    else:
        cpWindow.toFront()
    if startImmediately:
        startChart(cpWindow.rootContainer)
        
def startChart(rootContainer):
    from ils.sfc.client.util import getStartInIsolationMode
    from ils.sfc.common.util import startChart, chartIsRunning
    controlPanelName = rootContainer.controlPanelName
    isolationMode = getStartInIsolationMode()
    project = system.util.getProjectName()
    chartPath = getControlPanelChartPath(controlPanelName)
    originator = system.security.getUsername()

    if not chartIsRunning(chartPath):
        print "In %s - starting %s" % (__name__, controlPanelName)
        chartRunId=startChart(chartPath, controlPanelName, project, originator, isolationMode)
    else:
        system.gui.warningBox('This chart is already running')
    
    system.db.refresh(rootContainer, "windowData")
        
def pauseChart(event):
    from system.sfc import pauseChart
    pauseChart(system.gui.getParentWindow(event).rootContainer.chartRunId)

def resumeChart(event):
    from system.sfc import resumeChart
    resumeChart(system.gui.getParentWindow(event).rootContainer.chartRunId)

def cancelChart(event):
    from system.sfc import cancelChart
    cancelChart(system.gui.getParentWindow(event).rootContainer.chartRunId)
    closeAllPopups()
       
def updateChartStatus(event):
    '''Get the status of this panel's chart run and set the status field appropriately.
       Will show None if the chart is not running.'''
    from ils.sfc.common.util import getChartStatus
    from ils.sfc.common.constants import CANCELED
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

    # Presses the reset button should reset things, not cancelling the chart!
#    if status != oldStatus and status == CANCELED:
#        reset(event)


def updateMessageCenter(rootContainer):
    # print "Updating the message center... "
    database = getDatabase()
    chartRunId = rootContainer.chartRunId
    selectedMessage = rootContainer.selectedMessage
    SQL = "select id, createTime, message, priority, ackRequired, priority + CAST(ackRequired as varchar(5)) as state "\
        " from SfcControlPanelMessage where chartRunId = '%s' order by createTime asc" % (chartRunId)
    pds = system.db.runQuery(SQL, database)
    rootContainer.messages = pds
    numMessages = len(pds)
    
    if numMessages-1 == selectedMessage:
        rootContainer.autoIndex = True
    
    # If the last message was selected and we added a new message then automatically select it.
    if rootContainer.autoIndex:
        selectedMessage = numMessages - 1
        rootContainer.selectedMessage = selectedMessage

    updateSelectedMessageText(rootContainer)

def updateSelectedMessageText(rootContainer):
    selectedMessage = rootContainer.selectedMessage
    numMessages = rootContainer.messages.rowCount
    if numMessages == 0:
        txt = ""
    else:
        txt = "%i of %i" % (selectedMessage + 1, numMessages)
    rootContainer.selectedMessageText = txt

def reset(event):
    window = system.gui.getParentWindow(event)
    rootContainer = window.getRootContainer()
    rootContainer.selectedMessage = 0
    resetDb(rootContainer)
    closeAllPopups()

def closeAllPopups():
    '''close all popup windows, except for control panels and error Popup (we usually cancel the chart on the first error).
       CAUTION: this will close ALL popups, for all charts!!!'''
    from ils.sfc.client.windowUtil import getWindowPath
    for window in system.gui.getOpenedWindows():
        windowPath = getWindowPath(window)
        if windowPath.startswith(sfcWindowPrefix) and windowPath != controlPanelWindowPath and windowPath != errorPopupWindowPath:
            system.nav.closeWindow(window)
       
def resetDb(rootContainer):
    controlPanelName=rootContainer.controlPanelName
    chartRunId=rootContainer.chartRunId
    print "Resetting the database for chart run: ", chartRunId
    database = getDatabase()
    system.db.runUpdateQuery("update SfcControlPanel set chartRunId = '', operation = '', msgQueue = '', enablePause = 1, enableResume = 1, enableCancel = 1 where controlPanelName = '%s'" % (controlPanelName), database)
    system.db.runUpdateQuery("delete from SfcControlPanelMessage where chartRunId = '%s'" % chartRunId, database)
    system.db.runUpdateQuery("delete from SfcDialogMessage", database)
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
    database = getDatabase()
    results = system.db.runQuery("select controlPanelId from SfcControlPanel where controlPanelName = '%s'" % (controlPanelName), database)
    if len(results) == 1:
        return results[0][0]
    else:
        return None

def createControlPanel(controlPanelName):    
    '''create a new control panel with the given name, returning the id.
       This name must be unique'''
    database = getDatabase()
    system.db.runUpdateQuery("insert into SfcControlPanel (controlPanelName, chartPath) values ('%s', '')" % (controlPanelName), database)
    return getControlPanelIdForName(controlPanelName, False)

def getControlPanelChartPath(controlPanelName):
    '''get the name of the SFC chart associated with the given control panel'''
    database = getDatabase()
    results = system.db.runQuery("select chartPath from SfcControlPanel where controlPanelName = '%s'" % (controlPanelName), database)
    if len(results) == 1:
        return results[0][0]
    else:
        return None

def getControlPanelIdForChartPath(chartPath):
    '''get the id of the SFC chart associated with the given chart path, or None'''
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
    database = getDatabase()
    system.db.runUpdateQuery("update SfcControlPanel set chartPath = '%s' where controlPanelId = %d" % (chartPath, controlPanelId), database)

def showMsgQueue(window):
    rootContainer = window.getRootContainer()
    queueKey=rootContainer.windowData.getValueAt(0,'msgQueue')
    from ils.queue.message import view
    view(queueKey, useCheckpoint=True)

def ackMessage(window):
    ''' Called from a pushbutton on the control panel.   '''
    db = getDatabase()
    rootContainer = window.getRootContainer()
    selectedMessage = rootContainer.selectedMessage
    msgId = rootContainer.messages.getValueAt(selectedMessage, 'id')
    SQL = "DELETE from SfcControlPanelMessage where id = '%s'" % msgId
    numUpdated = system.db.runUpdateQuery(SQL, db)
    if(numUpdated != 1):
        handleUnexpectedClientError("setting ack time in control panel msg table failed")
    
def findOpenControlPanel(controlPanelName):   
    for window in system.gui.findWindow(controlPanelWindowPath):
        if window.getRootContainer().controlPanelName == controlPanelName:
            return window
    return None

def openDynamicControlPanel(chartPath, startImmediately, controlPanelName):
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
        controlPanelId = getControlPanelIdForName(controlPanelName)
        if controlPanelId == None:
            controlPanelId = createControlPanel(controlPanelName)
        # re-set the panel's chart to the desired one:
        setControlPanelChartPath(controlPanelId, chartPath)
    openControlPanel(controlPanelName, startImmediately)