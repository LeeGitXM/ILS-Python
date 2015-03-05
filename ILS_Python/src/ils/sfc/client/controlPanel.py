'''
Created on Oct 31, 2014

@author: rforbes
'''

CONTROL_PANEL_NAME = 'SFC/SFCControlPanel'
controlPanelsByChartRunId = dict()
FLASH_INTERVAL = 3.
import system.dataset

def flash(obj):
    from java.awt import Color
    import threading
    if not obj.flashing:
        return
    print 'flash'
    msgArea = obj.getMessageArea()
    if msgArea.getBackground() == Color.red:
        msgArea.setBackground(Color.blue)
    elif msgArea.getBackground() == Color.blue:
        msgArea.setBackground(Color.red)
    t = threading.Timer(FLASH_INTERVAL, flash, [obj])
    t.start() 

class ControlPanel:
    """Controller for an SFCControlPanel Vision window"""
    window = None
    rootContainer = None
    chartProperties = None
    messageIndex = None
    messages = None
    timer = None
    flashing = False
    pauseMask = True
    resumeMask = True
    cancelMask = True
    toolbarDataHeader = ['text', 'windowPath', 'windowId', 'chartRunId'] # these are the button properties
    toolbarDataset = system.dataset.toDataSet(toolbarDataHeader, [])
    windowsById = dict()
    
    def  __init__(self, _window, _chartProperties):
        self.window = _window
        self.rootContainer = self.window.rootContainer
        self.chartProperties = _chartProperties
        self.update()
 
    def getUser(self):
        from ils.sfc.common.constants import USER
        return self.chartProperties[USER]
    
    def getChartName(self):
        from ils.sfc.common.constants import CHART_NAME
        return self.chartProperties[CHART_NAME]
    
    def getChartRunId(self):
        from ils.sfc.common.constants import INSTANCE_ID
        return self.chartProperties[INSTANCE_ID]
    
    def getDatabase(self):
        from ils.sfc.common.constants import DATABASE
        return self.chartProperties[DATABASE]
    
    def update(self):
        '''something has changed; update the UI'''
        from ils.sfc.common.sessions import getControlPanelMessages
        self.messages = getControlPanelMessages(self.getChartRunId(), self.getDatabase())
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
            self.enableChartButtons(True, False, True)
        elif status == PAUSED:
            statusField.setBackground(Color.yellow)
            self.enableChartButtons(False, True, True)
        elif status == ABORTED:
            statusField.setBackground(Color.red)
            self.enableChartButtons(False, False, False)
        elif status == STOPPED or status == CANCELED:
            statusField.setBackground(Color.blue)
            self.enableChartButtons(False, False, False)
        else:
            #Some other transitory state
            statusField.setBackground(Color.gray)
            self.enableChartButtons(False, False, False)
            
    def setCommandMask(self, pause, resume, cancel):
        self.pauseMask= pause
        self.resumeMask = resume
        self.cancelMask = cancel
        self.enableChartButtons(self.getPauseButton().isEnabled(), self.getResumeButton().isEnabled(), self.getCancelButton().isEnabled())
    
    def enableChartButtons(self, pause, resume, cancel):
        self.getPauseButton().setEnabled(pause and self.pauseMask)
        self.getResumeButton().setEnabled(resume and self.resumeMask)
        self.getCancelButton().setEnabled(cancel and self.cancelMask)

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
        elif ackRequired:
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
        from ils.sfc.common.sessions import acknowledgeControlPanelMessage
        msg = self.messages[self.messageIndex]
        msgId = msg[ID]
        acknowledgeControlPanelMessage(msgId, self.getDatabase())
        self.update()
        
    def doPause(self):
        from system.sfc import pauseChart
        pauseChart(self.getChartRunId())
    
    def doResume(self):
        from system.sfc import resumeChart
        resumeChart(self.getChartRunId())
    
    def doCancel(self):
        from system.sfc import cancelChart
        cancelChart(self.getChartRunId())
    
    def topWindow(self, windowId):
        window = self.windowsById[windowId]
        window.toFront()
        
    def addWindow(self, label, windowPath, window, windowId):
        self.windowsById[windowId] = window
        newRow = [label, windowPath, windowId, self.getChartRunId()]
        self.toolbarDataset = system.dataset.addRow(self.toolbarDataset, newRow)
        self.getToolbar().templateParams = self.toolbarDataset

    def removeWindow(self, windowId):
        for i in range(self.toolbarDataset.getRowCount()):
            rowWindowId = self.toolbarDataset.getValueAt(i,2)
            print 'comparing ', rowWindowId, windowId
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
             
#def reconnect():
#    from ils.sfc.client.util import registerClient
#    registerClient()

def createControlPanel(chartProperties):
    from ils.sfc.common.constants import INSTANCE_ID
    window = system.nav.openWindowInstance(CONTROL_PANEL_NAME)
    chartRunId = chartProperties[INSTANCE_ID]
    window.getRootContainer().chartRunId = chartRunId
    controller = ControlPanel(window, chartProperties)
    controlPanelsByChartRunId[chartRunId] = controller
    return controller

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

def removeControlPanel(chartRunId):
    cp = controlPanelsByChartRunId.pop(chartRunId, None)
    if cp != None:
        cp.flashing = False # stop the timer loop
        cp.window.dispose
    