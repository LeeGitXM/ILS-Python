'''
Created on Nov 24, 2015

@author: rforbes
'''

FLASH_INTERVAL = 3.
import system.dataset
                      
viewsById = dict() # map of all control panel views indexed by id

class ControlPanelView:
    toolbarDataHeader = ['text', 'windowPath', 'windowId', 'chartRunId'] # these are the button properties

    def  __init__(self, _session):
        self.session = _session
        self.pauseMask = True
        self.resumeMask = True
        self.cancelMask = True
    # canXXX indicates whether the system would allow the operation
        self.canStart = True
        print 'canStart'
        self.canPause = False
        self.canResume = False
        self.canCancel = False
        self.toolbarDataset = system.dataset.toDataSet(ControlPanelView.toolbarDataHeader, [])
        self.windowsById = dict()
        self.msgQueue = 'Unknown' 
        self.window = system.nav.openWindowInstance('SFC/ControlPanel2', {'sessionId':self.session.sessionId})
        self.window.title = self.session.chartName
        self.rootContainer = self.window.getRootContainer()
        addControlPanelView(self)
        self.enableChartButtons()
        
    def updateModel(self, _session):
        self.session = _session
        self.update()
        
    def update(self):
        '''something has changed; update the UI'''
        self.updateStatus()

    def updateMessages(self):
        if not self.session.chartStarted():
            return
        from ils.sfc.common.cpmessage import getControlPanelMessages
        self.messages = getControlPanelMessages(self.session.chartRunId, self.session.database)
        print 'updateMessages', self.messages
        numMessages = len(self.session.messages)
        if numMessages > 0:
            if self.session.messageIndex == None:
                self.session.messageIndex = numMessages - 1 # latest msg
            self.setMessage(self.messageIndex)

    def setMessage(self, index):
        from java.awt import Color
        from ils.sfc.common.constants import MESSAGE,  CREATE_TIME, ACK_REQUIRED, ACK_TIME, ACK_TIMED_OUT
        if index >= len(self.session.messages) or index < 0:
            return
        self.session.messageIndex = index
        row = self.session.messages[index]
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
            flashMessageArea(self)
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

    def updateStatus(self):
        from java.awt import Color
        from ils.sfc.common.constants import RUNNING, PAUSED, CANCELED, STOPPED, ABORTED
        print 'updateStatus'
        status = self.session.chartStatus
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
        elif status == STOPPED or status == CANCELED:            
            if status == STOPPED:
                statusField.setBackground(Color.blue)
            else:
                statusField.setBackground(Color.orange)
            self.setCommandCapability(True, False, False, False)
            self.window.closable = True
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

    def setMessageQueue(self, queue):
        self.msgQueue = queue

    def getMessageQueue(self):
        return self.msgQueue

    def doStart(self):
        from ils.sfc.common.constants import SESSION_ID
        from ils.sfc.client.gatewayMsgs import sendMessageToGateway
        payload = dict()
        payload[SESSION_ID] = self.session.sessionId
        sendMessageToGateway('sfcStartChart', payload)

def flashMessageArea(obj):
    '''Start a timer that will flash the message area background'''
    from java.awt import Color
    import threading 
    if not obj.flashing:
        return
    msgArea = obj.getMessageArea()
    if msgArea.getBackground() == Color.red:
        msgArea.setBackground(Color.blue)
    elif msgArea.getBackground() == Color.blue:
        msgArea.setBackground(Color.red)
    t = threading.Timer(FLASH_INTERVAL, flashMessageArea, [obj])
    t.start() 

def getControlPanelView(sessionId):
    return viewsById.get(sessionId, None)

def addControlPanelView(controlPanelView):
    viewsById[controlPanelView.session.sessionId] = controlPanelView

def removeControlPanelView(cpid):
    viewsById.remove(cpid)

def sessionChanged(session):
    view = viewsById.get(session.sessionId, None)
    if view != None:
        print 'view found; updating'
        view.updateModel(session)
    else:
        'creating new view'
        ControlPanelView(session)

def sessionsChanged(newSessionData):
    window = system.gui.getWindow('Reconnect')
    sessionTable = window.getRootContainer().getComponent("sessionTable")
    sessionTable.data = newSessionData
    
