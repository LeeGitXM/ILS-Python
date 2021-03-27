'''
Created on Dec 9, 2015

@author: rforbes
'''

import system
from ils.common.config import getDatabaseClient
from ils.sfc.client.util import getStartInIsolationMode
from ils.sfc.common.util import startChart, chartIsRunning, getChartStatus
from ils.sfc.common.constants import HANDLER, WINDOW
from ils.common.windowUtil import positionWindow
from ils.sfc.client.windowUtil import getWindowPath
from ils.sfc.common.notify import sfcNotify

immuneWindowList = ['SFC/ControlPanel', 'SFC/ErrorPopup', 'SFC/DownloadKey', 'SFC/RecipeDataBrowser', 'SFC/RecipeDataEditor', 'SFC/RecipeDataKey', 
                    'SFC/RecipeDataTypeChooser', 'SFC/RecipeDataViewer', 'SFC/SfcHierarchy', 'SFC/SfcHierarchyWithRecipeBrowser', 'SFC/SFC Runner',
                    'SFC/ControlPanelSFCViewer']

sfcWindowPrefix = 'SFC/'

from ils.log.LogRecorder import LogRecorder
log = LogRecorder(__name__)

def internalFrameOpened(event):
    print "In internalFrameOpened..."
    rootContainer = event.source.rootContainer
    rootContainer.selectedMessage=0
    rootContainer.autoIndex=True
    
def openControlPanel(controlPanelName, controlPanelId, startImmediately, position="CENTER"):
    print "In openControlPanel()..."
    
    chartPath = getControlPanelChartPath(controlPanelName)
    print "...the chart path for this control panel is: ", chartPath
    if not chartIsRunning(chartPath):
        print "...the chart is not running so reset the control panel..."
        resetControlPanel(controlPanelName)
    
    cpWindow = findOpenControlPanel(controlPanelName)
    if cpWindow == None:
        print "...opening a new control panel..."
        cpWindow = system.nav.openWindowInstance("SFC/ControlPanel", {'controlPanelName': controlPanelName, 'controlPanelId': controlPanelId})
        
        positionWindow(cpWindow, position)
    else:
        print "...bringing an open control panel to the front..."
        cpWindow.toFront()
        
    isolationMode = getStartInIsolationMode()
    rootContainer = cpWindow.rootContainer
    rootContainer.isolationMode = isolationMode
            
    if startImmediately:
        '''
        There can only be one instance, regardless of isolation or production.
        '''
        if not chartIsRunning(chartPath):
            print "In %s - starting %s" % (__name__, controlPanelName)
            project = system.util.getProjectName()
            originator = system.security.getUsername()
            startChart(chartPath, controlPanelName, project, originator, isolationMode)
        else:
            system.gui.warningBox('This chart is already running')
        
        system.db.refresh(rootContainer, "windowData")

def startChartFromControlPanel(rootContainer):
    controlPanelName = rootContainer.controlPanelName
    chartPath = getControlPanelChartPath(controlPanelName)
    originator = system.security.getUsername()
    project = system.util.getProjectName()
    isolationMode = getStartInIsolationMode()
    
    startChart(chartPath, controlPanelName, project, originator, isolationMode)
        
def pauseChart(event):
    system.sfc.pauseChart(system.gui.getParentWindow(event).rootContainer.chartRunId)

def resumeChart(event):
    system.sfc.resumeChart(system.gui.getParentWindow(event).rootContainer.chartRunId)

def cancelChart(event):
    system.sfc.cancelChart(system.gui.getParentWindow(event).rootContainer.chartRunId)
    closeAllPopups()
       
def updateChartStatus(event):
    '''Get the status of this panel's chart run and set the status field appropriately.
       Will show None if the chart is not running.'''

    database = getDatabaseClient()
    window = system.gui.getParentWindow(event)
    rootContainer = window.getRootContainer()
    
    ds = rootContainer.windowData
    if ds.rowCount < 1:
        print "Exiting updateChartStatus() because there is no window data"
        return
    
    chartRunId = ds.getValueAt(0,'chartRunId')
    status = getChartStatus(chartRunId)
    statusField = window.rootContainer.getComponent('statusLabel')
    if statusField.text == '':
        oldStatus = None
    else:
        oldStatus = statusField.text
    if status != None:
        statusField.text = status
    else:
        statusField.text = ''

    # Fetch the enable/disable state of the control panel command buttons.
    SQL = "Select * from SfcControlPanel where chartRunId = '%s'" % (chartRunId)
    pds = system.db.runPrepQuery(SQL, database=database)
    
    if len(pds) <> 1:
        return
    
    record = pds[0]
    rootContainer.enableCancel = record["EnableCancel"]
    rootContainer.enablePause = record["EnablePause"]
    rootContainer.enableReset = record["EnableReset"]
    rootContainer.enableResume = record["EnableResume"]
    rootContainer.enableStart = record["EnableStart"]
    
    # The operation really isn't dynamic, but who knows when it gets set
    rootContainer.operation = record["Operation"]

    # Presses the reset button should reset things, not cancelling the chart!
#    if status != oldStatus and status == CANCELED:
#        reset(event)


def updateMessageCenter(rootContainer):
    # print "Updating the message center... "
    database = getDatabaseClient()
    controlPanelId = rootContainer.controlPanelId
    selectedMessage = rootContainer.selectedMessage
    SQL = "select id, createTime, message, priority, ackRequired, priority + CAST(ackRequired as varchar(5)) as state "\
        " from SfcControlPanelMessage where controlPanelId = %s order by createTime asc" % (str(controlPanelId))
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
        messageArea = rootContainer.getComponent("messageCenterPanel").getComponent("messageArea")
        messageArea.background = system.gui.color("255,255,255")
    else:
        txt = "%i of %i" % (selectedMessage + 1, numMessages)
    rootContainer.selectedMessageText = txt

def reset(event):
    print "In %s.reset()" % (__name__)
    database = getDatabaseClient()
    window = system.gui.getParentWindow(event)
    rootContainer = window.getRootContainer()
    rootContainer.selectedMessage = 0
    controlPanelId = rootContainer.controlPanelId
    controlPanelName = rootContainer.controlPanelName
    
    ''' 
    Get all of the registered windows and send a message to ALL clients to close them.
    Even though this action is started from a client we need to notify ALL clients because the gateway may have
    asked lots of clients to show the windows
    '''
    project = system.util.getProjectName()
    messageHandler = 'sfcCloseWindowByName'
    message = 'sfcMessage'
    post = "?"
    
    SQL = "select windowPath from SfcWindow where controlPanelId = %s" % (controlPanelId)
    pds = system.db.runQuery(SQL, database) 
    for record in pds:
        windowPath = record["windowPath"]
        print "Closing %s on all clients..." % (windowPath)
        payload = {HANDLER: messageHandler, WINDOW: windowPath}
        sfcNotify(project, message, payload, post, controlPanelName, controlPanelId, database)
    
    resetControlPanel(rootContainer.controlPanelName)
    closeAllPopups()

def closeAllPopups():
    '''close all popup windows, except for control panels and error Popup (we usually cancel the chart on the first error).
       CAUTION: this will close ALL popups, for all charts!!!'''
    for window in system.gui.getOpenedWindows():
        windowPath = getWindowPath(window)
        if windowPath.startswith(sfcWindowPrefix) and windowPath not in immuneWindowList:
            system.nav.closeWindow(window)
    
def resetControlPanel(controlPanelName):
    print "Resetting the database for control panel: ", controlPanelName
    database = getDatabaseClient()
    controlPanelId = getControlPanelIdForName(controlPanelName)
    system.db.runUpdateQuery("update SfcControlPanel set chartRunId = '', operation = '', enablePause = 1, enableResume = 1, enableCancel = 1 where controlPanelName = '%s'" % (controlPanelName), database)
    system.db.runUpdateQuery("delete from SfcControlPanelMessage where controlPanelId = %s" % controlPanelId, database)
    system.db.runUpdateQuery("delete from SfcWindow where chartRunId = chartRunId ", database)


def getControlPanelIdForChartRunId(chartRunId, db):
    '''Get the control panel id given the name, or None'''
    controlPanelId = system.db.runScalarQuery("select controlPanelId from SfcControlPanel where chartRunId = '%s'" % (chartRunId), db)
    return controlPanelId
    
def getControlPanelIdForName(controlPanelName):
    '''Get the control panel id given the name, or None'''
    print "Fetching the id for controlPanel named: ", controlPanelName
    database = getDatabaseClient()
    results = system.db.runQuery("select controlPanelId from SfcControlPanel where controlPanelName = '%s'" % (controlPanelName), database)
    if len(results) == 1:
        return results[0][0]
    else:
        print "A control panel was not found!"
        return None

def createControlPanel(controlPanelName):    
    '''create a new control panel with the given name, returning the id.
       This name must be unique'''
    database = getDatabaseClient()
    system.db.runUpdateQuery("insert into SfcControlPanel (controlPanelName, chartPath) values ('%s', '')" % (controlPanelName), database)
    return getControlPanelIdForName(controlPanelName)

def getControlPanelChartPath(controlPanelName):
    '''get the name of the SFC chart associated with the given control panel'''
    database = getDatabaseClient()
    results = system.db.runQuery("select chartPath from SfcControlPanel where controlPanelName = '%s'" % (controlPanelName), database)
    if len(results) == 1:
        return results[0][0]
    else:
        return None

def getControlPanelIdForChartPath(chartPath):
    '''get the id of the SFC chart associated with the given chart path, or None'''
    database = getDatabaseClient()
    results = system.db.runQuery("select controlPanelId from SfcControlPanel where chartPath = '%s'" % (chartPath), database)
    if len(results) == 1:
        return results[0][0]
    else:
        return None

def setControlPanelChartPath(controlPanelId, chartPath):
    '''set the name of the SFC chart associated with the given control panel.
       this will fail if there is already a control panel for that chart.
       use getControlPanelForChartPath() to check'''
    database = getDatabaseClient()
    system.db.runUpdateQuery("update SfcControlPanel set chartPath = '%s' where controlPanelId = %d" % (chartPath, controlPanelId), database)

def showMsgQueue(window):
    rootContainer = window.getRootContainer()
    controlPanelId = rootContainer.controlPanelId
    database = getDatabaseClient()
    
    SQL = "Select MsgQueue from SfcControlPanel where ControlPanelId = %s" % (str(controlPanelId))
    queueKey=system.db.runScalarQuery(SQL, database)
    
    print "The queue is: ", queueKey
    from ils.queue.message import view
    view(queueKey, useCheckpoint=True)
    
def showRecipeDataBrowser():
    window = system.nav.openWindow("SFC/SfcHierarchyWithRecipeBrowser")
    system.nav.centerWindow(window)

def ackMessage(window):
    ''' Called from a pushbutton on the control panel.   '''
    db = getDatabaseClient()
    rootContainer = window.getRootContainer()
    selectedMessage = rootContainer.selectedMessage
    msgId = rootContainer.messages.getValueAt(selectedMessage, 'id')
    SQL = "DELETE from SfcControlPanelMessage where id = '%s'" % msgId
    numUpdated = system.db.runUpdateQuery(SQL, db)
    
def findOpenControlPanel(controlPanelName):   
    for window in system.gui.findWindow('SFC/ControlPanel'):
        if window.getRootContainer().controlPanelName == controlPanelName:
            return window
    return None

def openDynamicControlPanel(chartPath, startImmediately, controlPanelName, position="CENTER"):
    '''
    Open a control panel to run the given chart, starting the chart
    if startImmediately is true. If no control panel is associated 
    with the given chart, use the one with the given name (creating that
    if it doesnt exist).
    This method is useful for development where a "scratch"
    control panel is used to run many different ad-hoc charts
    '''
    # First, check for an existing panel associated with this chart:
    controlPanelId = getControlPanelIdForChartPath(chartPath)
    log.infof("In %s.openDynamicControlPanel() - The id for chart %s is %s", __name__, chartPath, str(controlPanelId)) 

    if controlPanelId == None:
        # next, check for an existing panel with the given name, creating if not found:
        controlPanelId = getControlPanelIdForName(controlPanelName)
        print "The control panel id for chart %s is %s" % (controlPanelName, str(controlPanelId))
        if controlPanelId == None:
            print "Creating a control panel..."
            controlPanelId = createControlPanel(controlPanelName)
        # re-set the panel's chart to the desired one:
        setControlPanelChartPath(controlPanelId, chartPath)
    
    print "Opening a control panel named: ", controlPanelName
    openControlPanel(controlPanelName, controlPanelId, startImmediately, position)