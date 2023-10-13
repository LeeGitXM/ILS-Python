'''
Created on Dec 9, 2015

@author: rforbes
'''

import system
from ils.config.client import getDatabase, getIsolationMode
from ils.sfc.client.util import getStartInIsolationMode, startChart
from ils.sfc.common.util import chartIsRunning, getChartStatus
from ils.sfc.common.constants import HANDLER, WINDOW, WINDOW_ID
from ils.common.windowUtil import positionWindow
from ils.sfc.client.windowUtil import getWindowPath
from ils.sfc.common.notify import sfcNotify

immuneWindowList = ['SFC/ControlPanel', 'SFC/ErrorPopup', 'SFC/DownloadKey', 'SFC/RecipeDataBrowser', 'SFC/RecipeDataEditor', 'SFC/RecipeDataKey', 
                    'SFC/RecipeDataTypeChooser', 'SFC/RecipeDataViewer', 'SFC/SfcHierarchy', 'SFC/SfcHierarchyWithRecipeBrowser', 'SFC/SFC Runner',
                    'SFC/ControlPanelSFCViewer', 'SFC/Viewer']

sfcWindowPrefix = 'SFC/'

from ils.log import getLogger
log = getLogger(__name__)

def internalFrameOpened(event):
    log.infof("In %s.internalFrameOpened()...", __name__)
    rootContainer = event.source.rootContainer
    rootContainer.selectedMessage=0
    rootContainer.autoIndex=True
    
def openControlPanel(controlPanelName, controlPanelId, startImmediately, position="CENTER"):
    log.infof("In %s.openControlPanel()...", __name__)
    db = getDatabase()
    isolationMode = getIsolationMode()
    chartPath = getControlPanelChartPath(controlPanelName, db)
    log.infof("...the chart path for this control panel is: %s", chartPath)
    if not chartIsRunning(chartPath, isolationMode):
        log.infof("...the chart is not running so reset the control panel...")
        resetControlPanel(controlPanelName)
    
    cpWindow = findOpenControlPanel(controlPanelName)
    if cpWindow == None:
        log.infof("...opening a new control panel...")
        cpWindow = system.nav.openWindowInstance("SFC/ControlPanel", {'controlPanelName': controlPanelName, 'controlPanelId': controlPanelId})
        
        positionWindow(cpWindow, position)
    else:
        log.infof("...bringing an open control panel to the front...")
        cpWindow.toFront()
        
    isolationMode = getStartInIsolationMode()
    rootContainer = cpWindow.rootContainer
    rootContainer.isolationMode = isolationMode
            
    if startImmediately:
        log.infof("Start immediately (if not already running)...")
        '''
        There can only be one instance, regardless of isolation or production.
        '''
        if not chartIsRunning(chartPath):
            log.infof("In %s - starting %s", __name__, controlPanelName)
            project = system.util.getProjectName()
            originator = system.security.getUsername()
            startChart(chartPath, controlPanelName, project, originator, isolationMode)
        else:
            system.gui.warningBox('This chart is already running')
        
        log.infof("Refreshing the root container...")
        system.db.refresh(rootContainer, "windowData")

def startChartFromControlPanel(rootContainer):
    controlPanelName = rootContainer.controlPanelName
    db = getDatabase()
    chartPath = getControlPanelChartPath(controlPanelName, db)
    originator = system.security.getUsername()
    project = system.util.getProjectName()
    isolationMode = getStartInIsolationMode()
    
    startChart(chartPath, controlPanelName, project, originator, isolationMode)
        
def pauseChart(event):
    log.infof("In %s.pauseChart()...", __name__)
    system.sfc.pauseChart(system.gui.getParentWindow(event).rootContainer.chartRunId)

def resumeChart(event):
    log.infof("In %s.resumeChart()...", __name__)
    system.sfc.resumeChart(system.gui.getParentWindow(event).rootContainer.chartRunId)

def cancelChart(event):
    log.infof("In %s.cancelChart()...", __name__)
    system.sfc.cancelChart(system.gui.getParentWindow(event).rootContainer.chartRunId)
    '''
    Commented this out to prevent reset bleeding when there are two unit procedures with two control panels on the same client.
    PAH 10/12/23 - TRAC#974
    '''
    #closeAllPopups()
       
def updateChartStatus(event):
    '''Get the status of this panel's chart run and set the status field appropriately.
       Will show None if the chart is not running.'''

    db = getDatabase()
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
    pds = system.db.runPrepQuery(SQL, database=db)
    
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
    db = getDatabase()
    controlPanelId = rootContainer.controlPanelId
    selectedMessage = rootContainer.selectedMessage
    SQL = "select id, createTime, message, priority, ackRequired, priority + CAST(ackRequired as varchar(5)) as state "\
        " from SfcControlPanelMessage where controlPanelId = %s order by createTime asc" % (str(controlPanelId))
    pds = system.db.runQuery(SQL, database=db)
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
    db = getDatabase()
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
    
    SQL = "select windowPath, windowId from SfcWindow where controlPanelId = %s" % (controlPanelId)
    pds = system.db.runQuery(SQL, database=db) 
    for record in pds:
        windowPath = record["windowPath"]
        windowId = record["windowId"]
        print "Closing %s - %d on all clients..." % (windowPath, windowId)
        payload = {HANDLER: messageHandler, WINDOW: windowPath, WINDOW_ID: windowId}
        sfcNotify(project, message, payload, post, controlPanelName, controlPanelId, db)
    
    resetControlPanel(rootContainer.controlPanelName)
    
    '''
    Commented this out to prevent reset bleeding when there are two unit procedures with two control panels on the same client.
    PAH 10/12/23 - TRAC#974
    '''
    #closeAllPopups()

def closeAllPopups():
    '''close all popup windows, except for control panels and error Popup (we usually cancel the chart on the first error).
       CAUTION: this will close ALL popups, for all charts!!!'''
    for window in system.gui.getOpenedWindows():
        windowPath = getWindowPath(window)
        if windowPath.startswith(sfcWindowPrefix) and windowPath not in immuneWindowList:
            system.nav.closeWindow(window)
    
def resetControlPanel(controlPanelName):
    print "Resetting the database for control panel: ", controlPanelName
    db = getDatabase()
    system.db.runUpdateQuery("update SfcControlPanel set chartRunId = '', operation = '', enablePause = 1, enableResume = 1, "\
        " enableCancel = 1 where controlPanelName = '%s'" % (controlPanelName), database=db)

    controlPanelId = getControlPanelIdForName(controlPanelName, db)
    print "Found control panel id <%s> for <%s>" % (str(controlPanelId), controlPanelName)
    if controlPanelId != None:
        system.db.runUpdateQuery("delete from SfcControlPanelMessage where controlPanelId = %s" % controlPanelId, database=db)
        
        ''' Added this back in with a slightly different where clause, not sure why it was ever removed. -PAH 7/28/21 '''
        system.db.runUpdateQuery("delete from SfcWindow where controlPanelId = %s" % controlPanelId, database=db)

def getControlPanelIdForChartRunId(chartRunId, db):
    '''Get the control panel id given the name, or None'''
    controlPanelId = system.db.runScalarQuery("select controlPanelId from SfcControlPanel where chartRunId = '%s'" % (chartRunId), database=db)
    return controlPanelId
    
def getControlPanelIdForName(controlPanelName, db=""):
    '''Get the control panel id given the name, or None'''
    results = system.db.runQuery("select controlPanelId from SfcControlPanel where controlPanelName = '%s'" % (controlPanelName), database=db)
    if len(results) == 1:
        return results[0][0]
    else:
        return None

def createControlPanel(controlPanelName, db=""):    
    '''create a new control panel with the given name, returning the id.
       This name must be unique'''
    system.db.runUpdateQuery("insert into SfcControlPanel (controlPanelName, chartPath, enableCancel, enablePause, enableReset, enableResume, enableStart) "\
                             "values ('%s', '', 1, 1, 1, 1, 1)" % (controlPanelName), database=db)
    return getControlPanelIdForName(controlPanelName)

def getControlPanelChartPath(controlPanelName, db):
    '''get the name of the SFC chart associated with the given control panel'''
    results = system.db.runQuery("select chartPath from SfcControlPanel where controlPanelName = '%s'" % (controlPanelName), database=db)
    if len(results) == 1:
        return results[0][0]
    else:
        return None

def getControlPanelIdForChartPath(chartPath, db):
    '''get the id of the SFC chart associated with the given chart path, or None'''
    results = system.db.runQuery("select controlPanelId from SfcControlPanel where chartPath = '%s'" % (chartPath), database=db)
    if len(results) == 1:
        return results[0][0]
    else:
        return None

def setControlPanelChartPath(controlPanelId, chartPath, msgQueueKey, db):
    '''set the name of the SFC chart associated with the given control panel.
       this will fail if there is already a control panel for that chart.
       use getControlPanelForChartPath() to check'''
    system.db.runUpdateQuery("update SfcControlPanel set chartPath = '%s', msgQueue = '%s' where controlPanelId = %d" % (chartPath, msgQueueKey, controlPanelId), database=db)

def showMsgQueue(window):
    rootContainer = window.getRootContainer()
    controlPanelId = rootContainer.controlPanelId
    db = getDatabase()
    
    SQL = "Select MsgQueue from SfcControlPanel where ControlPanelId = %s" % (str(controlPanelId))
    queueKey=system.db.runScalarQuery(SQL, database=db)

    print "The queue for control panel %d is %s" % (controlPanelId, queueKey)
    
    if queueKey == None:
        print "Using the default queue named: SFC in leue of an unspecified queue"
        queueKey = "SFC"
    
    from ils.queue.message import view
    view(queueKey, useCheckpoint=True)
    
def showRecipeDataBrowser():
    window = system.nav.openWindow("SFC/SfcHierarchyWithRecipeBrowser")
    system.nav.centerWindow(window)

def ackMessage(window):
    ''' Called from a pushbutton on the control panel.   '''
    db = getDatabase()
    rootContainer = window.getRootContainer()
    selectedMessage = rootContainer.selectedMessage
    msgId = rootContainer.messages.getValueAt(selectedMessage, 'id')
    SQL = "DELETE from SfcControlPanelMessage where id = '%s'" % msgId
    numUpdated = system.db.runUpdateQuery(SQL, database=db)
    
def findOpenControlPanel(controlPanelName):   
    for window in system.gui.findWindow('SFC/ControlPanel'):
        if window.getRootContainer().controlPanelName == controlPanelName:
            return window
    return None

def openDynamicControlPanel(chartPath, startImmediately, controlPanelName, msgQueueKey="SFC", position="CENTER"):
    '''
    Open a control panel to run the given chart, starting the chart if startImmediately is true. If no control panel is associated 
    with the given chart, use the one with the given name (creating it if it doesn't exist).
    This method is useful for development where a "scratch" control panel is used to run many different ad-hoc charts.
    This should only be called from a client. 
    '''
    # First, check for an existing panel associated with this chart:
    db = getDatabase()
    
    # check for an existing panel with the given name, creating if not found:
    log.infof("In %s.openDynamicControlPanel() - looking for a control panel named %s", __name__, controlPanelName)
    controlPanelId = getControlPanelIdForName(controlPanelName, db)
    log.infof("...found an existing control panel with id: %s", str(controlPanelId))
    if controlPanelId == None:
        log.infof("Creating a control panel...")
        controlPanelId = createControlPanel(controlPanelName, db)
        log.infof("...the new control panel id is: %s", str(controlPanelId))
    
    # reset the panel's chart to the desired one:
    setControlPanelChartPath(controlPanelId, chartPath, msgQueueKey, db)
    
    log.infof("Opening a control panel named <%s> with id: %s", controlPanelName, str(controlPanelId)) 
    openControlPanel(controlPanelName, controlPanelId, startImmediately, position)
    