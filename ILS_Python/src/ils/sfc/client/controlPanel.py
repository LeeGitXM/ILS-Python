'''
Created on Oct 31, 2014

@author: rforbes
'''

controlPanels = []
controlPanelsByChartRunId = dict()
FLASH_INTERVAL = 3.
import system.dataset

def flash(obj):
    from java.awt import Color
    import threading 
    if not obj.flashing:
        return
    msgArea = obj.getMessageArea()
    if msgArea.getBackground() == Color.red:
        msgArea.setBackground(Color.blue)
    elif msgArea.getBackground() == Color.blue:
        msgArea.setBackground(Color.red)
    t = threading.Timer(FLASH_INTERVAL, flash, [obj])
    t.start() 

class ControlPanel:
    """Controller for an SFCControlPanel Vision window"""
    toolbarDataHeader = ['text', 'windowPath', 'windowId', 'chartRunId'] # these are the button properties
     
    def  __init__(self, _window, _chartProperties):
        self.window = _window
        self.rootContainer = self.window.rootContainer
        self.chartProperties = _chartProperties
        self.messageIndex = None
        self.messages = None
        self.timer = None
        self.flashing = False
    # the masks indicate a user override of enabling Pause/Resume/Cancel
        self.pauseMask = True
        self.resumeMask = True
        self.cancelMask = True
    # canXXX indicates whether the system would allow the operation
        self.canStart = True
        self.canPause = False
        self.canResume = False
        self.canCancel = False
        self.chartStarted = False
        self.toolbarDataset = system.dataset.toDataSet(ControlPanel.toolbarDataHeader, [])
        self.windowsById = dict()
        self.update()
 
    def getUser(self):
        from ils.sfc.common.constants import USER
        return self.chartProperties[USER]
    
    def getChartName(self):
        from ils.sfc.common.constants import CHART_NAME
        return self.chartProperties[CHART_NAME]
    
    def getChartRunId(self):
        from ils.sfc.common.constants import INSTANCE_ID
        return self.chartProperties.get(INSTANCE_ID, None)
    
    def update(self):
        '''something has changed; update the UI'''
        if not self.chartStarted:
            return
        from ils.sfc.common.sessions import getControlPanelMessages
        from ils.sfc.client.util import getDatabaseName 
        database = getDatabaseName(self.chartProperties)
        self.messages = getControlPanelMessages(self.getChartRunId(), database)
        numMessages = len(self.messages)
        if numMessages > 0:
            if self.messageIndex == None:
                self.messageIndex = numMessages - 1 # latest msg
            self.setMessage(self.messageIndex)
        
    def updateStatus(self, status):
        from java.awt import Color
        from ils.sfc.common.constants import RUNNING, PAUSED, CANCELED, STOPPED, ABORTED
        statusField = self.getStatusField()
        statusField.setText(status)
        if status == RUNNING:
            statusField.setBackground(Color.green)
            self.setCommandCapability(False, True, False, True)
        elif status == PAUSED:
            statusField.setBackground(Color.yellow)
            self.setCommandCapability(False, False, True, True)
        elif status == ABORTED:
            statusField.setBackground(Color.red)
            self.setCommandCapability(True, False, False, False)
            self.window.closable = True
            self.setChartStopped()
        elif status == STOPPED or status == CANCELED:
            statusField.setBackground(Color.blue)
            self.setCommandCapability(True, False, False, False)
            self.window.closable = True
            self.setChartStopped()
        else:
            #Some other transitory state
            statusField.setBackground(Color.gray)
            self.setCommandCapability(False, False, False, False)
            
    def setCommandMask(self, pause, resume, cancel):
        self.pauseMask= pause
        self.resumeMask = resume
        self.cancelMask = cancel
        self.enableChartButtons()
   
    def enableChartButtons(self):
        self.getStartButton().setEnabled(self.canStart)
        self.getPauseButton().setEnabled(self.canPause and self.pauseMask)
        self.getResumeButton().setEnabled(self.canResume and self.resumeMask)
        self.getCancelButton().setEnabled(self.canCancel and self.cancelMask)
 
    def setCommandCapability(self, start, pause, resume, cancel):
        self.canStart = start
        self.canPause = pause
        self.canCancel = cancel
        self.canResume = resume
        self.enableChartButtons()

    def setMessage(self, index):
        from java.awt import Color
        from ils.sfc.common.constants import MESSAGE,  CREATE_TIME, ACK_REQUIRED, ACK_TIME, ACK_TIMED_OUT
        if index >= len(self.messages) or index < 0:
            return
        self.messageIndex = index
        row = self.messages[index]
        msg = row[MESSAGE]
        createTime = row[CREATE_TIME]
        ackRequired = row[ACK_REQUIRED]
        ackTime = row[ACK_TIME]    
        ackTimedOut = row[ACK_TIMED_OUT]        
        self.getMessageArea().setText(msg)
        self.flashing = False
        if ackTimedOut:
            self.getMessageArea().setBackground(Color.pink)
        elif ackRequired and ackTime == None:
            self.flashing = True
            self.getMessageArea().setBackground(Color.red)
            flash(self)
        else: # ordinary message
            self.getMessageArea().setBackground(Color.white)
        self.getSelectedMsgField().setText("%d of %d" % (self.messageIndex + 1, len(self.messages)))       
        self.getAckButton().setEnabled(ackRequired and ackTime == None and not ackTimedOut)
        if ackTime != None:
            status = "<html>Acknowledged<br>" + str(ackTime) + "</html>"
        elif ackTimedOut:
            status = "<html>Ack Timed Out</html>"
        else:
            status = "<html>Created<br>" + str(createTime) + "</html>"
        self.getMessageStatusLabel().setText(status)
    
    def getComponent(self, name):
        return self.rootContainer.getComponent(name)

    def getMsgPanelComponent(self, name):
        return self.rootContainer.getComponent('messageCenterPanel').getComponent(name)

    def getToolbar(self):
        return self.rootContainer.getComponent('toolbar')
    
    def getStartButton(self):
        return self.getComponent('commandButtons').getComponent("startButton")
    
    def getPauseButton(self):
        return self.getComponent('commandButtons').getComponent("pauseButton")
    
    def getResumeButton(self):
        return self.getComponent('commandButtons').getComponent("resumeButton")
    
    def getCancelButton(self):
        return self.getComponent('commandButtons').getComponent("cancelButton")

    def getStatusField(self):
        return self.getComponent("statusLabel")

    def getOperationField(self):
        return self.getComponent("operationLabel")

    def getSelectedMsgField(self):
        return self.getMsgPanelComponent("selectedMsgField")
    
    def getMessageArea(self):
        return self.getMsgPanelComponent("messageArea")  

    def getMessageStatusLabel(self):
        return self.getMsgPanelComponent("messageStatusLabel")  

    def getAckButton(self):
        return self.getMsgPanelComponent("ackButton")  

    # Button Actions:
    def doNextMessage(self):
        self.setMessage(self.messageIndex + 1)
        
    def doPrevMessage(self):
        self.setMessage(self.messageIndex - 1)
        
    def doAcknowledge(self):
        from ils.sfc.common.constants import ID
        from ils.sfc.client.util import getDatabaseName
        from ils.sfc.common.sessions import acknowledgeControlPanelMessage
        msg = self.messages[self.messageIndex]
        msgId = msg[ID]
        database = getDatabaseName(self.chartProperties)
        acknowledgeControlPanelMessage(msgId, database)
        self.update()
        
    def doStart(self):
        from ils.sfc.common.constants import INSTANCE_ID
        runId = system.sfc.startChart(self.getChartName(), self.chartProperties)
        self.chartProperties[INSTANCE_ID] = runId
        controlPanelsByChartRunId[runId] = self
        self.window.rootContainer.chartRunId = runId
        self.chartStarted = True
        
    def doPause(self):
        payload = {'instanceId' : self.getChartRunId()}
        system.util.sendMessage(system.util.getProjectName(), 'sfcPauseChart', payload, "G")
    
    def doResume(self):
        payload = {'instanceId' : self.getChartRunId()}
        system.util.sendMessage(system.util.getProjectName(), 'sfcResumeChart', payload, "G")
    
    def doCancel(self):
        payload = {'instanceId' : self.getChartRunId()}
        system.util.sendMessage(system.util.getProjectName(), 'sfcCancelChart', payload, "G")
    
    def topWindow(self, windowId):
        window = self.windowsById[windowId]
        window.toFront()
        
    def addWindow(self, toolbarButtonLabel, window):
        from ils.sfc.client.windowUtil import getWindowId, getWindowPath
        '''Register a window with this control panel. Create a toolbar button for it.'''
        windowId = getWindowId(window)
        self.windowsById[windowId] = window
        newRow = [toolbarButtonLabel, getWindowPath(window), windowId, self.getChartRunId()]
        self.toolbarDataset = system.dataset.addRow(self.toolbarDataset, newRow)
        self.getToolbar().templateParams = self.toolbarDataset

    def removeWindow(self, windowId):
        for i in range(self.toolbarDataset.getRowCount()):
            rowWindowId = self.toolbarDataset.getValueAt(i,2)
            if rowWindowId == windowId:      
                window = self.windowsById.pop(windowId)        
                system.nav.closeWindow(window)
                self.toolbarDataset = system.dataset.deleteRow(self.toolbarDataset, i)
                self.getToolbar().templateParams = self.toolbarDataset
                break
                
    def removeWindows(self, windowPath):
        rowsToRemove = []
        for i in range(self.toolbarDataset.getRowCount()):
            rowWindowName = self.toolbarDataset.getValueAt(i,1)
            if rowWindowName == windowPath:
                rowWindowId = self.toolbarDataset.getValueAt(i,2)
                window = self.windowsById.pop(rowWindowId)     
                system.nav.closeWindow(window)
                rowsToRemove.append(i)
        self.toolbarDataset = system.dataset.deleteRows(self.toolbarDataset, rowsToRemove)
        self.getToolbar().templateParams = self.toolbarDataset

    def setChartStopped(self):
        '''set the chartStopped flag in any windows still open'''
        for window in self.windowsById.values():
            window.getRootContainer().chartStopped = True

    def closeAll(self):
        '''close all the windows associated with this CP'''
        for window in self.windowsById.values():
            system.nav.closeWindow(window)
            
#def reconnect():
#    from ils.sfc.client.util import registerClient
#    registerClient()

def createControlPanel(chartProperties):
    from ils.sfc.common.constants import CHART_NAME
    window = system.nav.openWindowInstance('SFC/ControlPanel')
    window.title = chartProperties[CHART_NAME]
    window.getRootContainer().chartPath = chartProperties[CHART_NAME]
    controller = ControlPanel(window, chartProperties)
    controlPanels.append(controller)
    return controller

def getControllerByChartPath(chartPath):
    for controller in controlPanels:
        if controller.getChartName() == chartPath:
            return controller
    return None
        
def getController(chartRunId):
    return controlPanelsByChartRunId.get(chartRunId, None)

def updateControlPanels():
    for controller in controlPanelsByChartRunId.values():
        controller.update()

def updateChartStatus(payload):
    from ils.sfc.common.constants import STATUS, INSTANCE_ID
    chartRunId = payload[INSTANCE_ID] 
    existingPanel = controlPanelsByChartRunId.get(chartRunId, None)
    # since we only have control panels for top-level charts, we will
    # frequently get status updates for lower level charts that have
    # no panel
    if existingPanel != None:
        status = payload[STATUS]
        existingPanel.updateStatus(status)

def updateCurrentOperation(payload):
    from ils.sfc.common.constants import STATUS, INSTANCE_ID
    chartRunId = payload[INSTANCE_ID] 
    operationName = payload[STATUS]
    existingPanel = controlPanelsByChartRunId.get(chartRunId, None)

    if existingPanel != None:
        existingPanel.getOperationField().setText(operationName)

def removeControlPanel(chartPath):
    cp = getControllerByChartPath(chartPath)
    if cp != None:
        controlPanels.remove(cp)
        if cp.getChartRunId() != None:
            controlPanelsByChartRunId.pop(cp.getChartRunId(), None)
        cp.flashing = False # stop the timer loop
        cp.window.dispose
    