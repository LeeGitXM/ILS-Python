'''
Created on Oct 31, 2014

@author: rforbes
'''
import system.sfc

CONTROL_PANEL_NAME = 'SFCControlPanel'
controlPanelsByChartRunId = dict()

class ControlPanel:
    """Controller for an SFCControlPanel Vision window"""
    window = None
    rootContainer = None
    chartProperties = None
    messageIndex = None
    messages = None
    
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
        from java.awt import Color
        from ils.sfc.common.sessions import getControlPanelMessages
        from ils.sfc.common.sessions import getSession
        from ils.sfc.common.constants import STATUS, RUNNING, PAUSED, STOPPED, ABORTED, OPERATION
        self.messages = getControlPanelMessages(self.getChartRunId(), self.getDatabase())
        numMessages = len(self.messages)
        if numMessages > 0:
            if self.messageIndex == None:
                self.messageIndex = numMessages - 1 # latest msg
            self.setMessage(self.messageIndex)
        session = getSession(self.getChartRunId(), self.getDatabase())
        status = session[STATUS]
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
        elif status == STOPPED:
            statusField.setBackground(Color.blue)
            self.enableChartButtons(False, False, False)
        operation = session[OPERATION]
        self.getOperationField().setText(operation)
        
    def enableChartButtons(self, pause, resume, cancel):
        self.getPauseButton().setEnabled(pause)
        self.getResumeButton().setEnabled(resume)
        self.getCancelButton().setEnabled(cancel)
         
    def setMessage(self, index):
        from java.awt import Color
        from ils.sfc.common.constants import MESSAGE,  CREATE_TIME, ACK_REQUIRED, ACK_TIME
        if index >= len(self.messages) or index < 0:
            return
        self.messageIndex = index
        row = self.messages[index]
        msg = row[MESSAGE]
        createTime = row[CREATE_TIME]
        ackRequired = row[ACK_REQUIRED]
        ackTime = row[ACK_TIME]    
        self.getMessageArea().setText(msg)
        if ackRequired:
            self.getMessageArea().setBackground(Color.red)
        else:
            self.getMessageArea().setBackground(Color.white)
        self.getSelectedMsgField().setText("%d of %d" % (self.messageIndex + 1, len(self.messages)))       
        self.getAckButton().setEnabled(ackRequired and ackTime == None)
        if ackTime != None:
            status = "<html>Acknowledged<br>" + str(ackTime) + "</html>"
        else:
            status = "<html>Created<br>" + str(createTime) + "</html>"
        self.getMessageStatusLabel().setText(status)
        
    def getComponent(self, name):
        return self.rootContainer.getComponent(name)

    def getMsgPanelComponent(self, name):
        return self.rootContainer.getComponent('messageCenterPanel').getComponent(name)
    
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
        from ils.sfc.gateway.api import pauseChart
        pauseChart(self.chartProperties)
    
    def doResume(self):
        from ils.sfc.gateway.api import resumeChart
        resumeChart(self.chartProperties)
    
    def doCancel(self):
        from ils.sfc.gateway.api import cancelChart
        cancelChart(self.chartProperties)
    
    # Message Handlers:

def reconnect():
    from ils.sfc.common.sessions import getRunningSessions
    from ils.sfc.common.util import getDatabaseFromSystem
    from ils.sfc.common.constants import CHART_NAME, CHART_RUN_ID, DATABASE, INSTANCE_ID, USER
    database = getDatabaseFromSystem()
    user = system.security.getUsername()
    runningSessions = getRunningSessions(user, database)
    for session in runningSessions:
        chartProperties = dict()
        chartProperties[USER] = user
        chartProperties[DATABASE] = database
        chartProperties[CHART_NAME] = session[CHART_NAME]
        chartProperties[INSTANCE_ID] = session[CHART_RUN_ID]
        createControlPanel(chartProperties)

def createControlPanel(chartProperties):
    from ils.sfc.common.constants import INSTANCE_ID
    window = system.nav.openWindowInstance(CONTROL_PANEL_NAME)
    chartRunId = chartProperties[INSTANCE_ID]
    window.getRootContainer().chartRunId = chartRunId
    controller = ControlPanel(window, chartProperties)
    controlPanelsByChartRunId[chartRunId] = controller

def getController(chartRunId):
    return controlPanelsByChartRunId.get(chartRunId, None)

def updateControlPanels():
    for controller in controlPanelsByChartRunId.values():
        controller.update()

def removeControlPanel(chartRunId):
    controlPanelsByChartRunId.pop(chartRunId, None)
    