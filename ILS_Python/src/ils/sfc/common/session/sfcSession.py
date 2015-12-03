'''
Created on Nov 24, 2015

@author: rforbes
'''

class SfcSession:
    
    def  __init__(self, _chartName, _isolationMode, _project, _user):
        from system.ils.sfc import getDatabaseName
        from ils.sfc.common.util import createUniqueId
        self.chartName = _chartName
        self.isolationMode = _isolationMode
        self.project = _project
        self.user = _user
        self.chartRunId = None
        self.chartStatus = None
        self.messageQueue = 'Unknown'
        self.messages = None
        self.messageIndex = -1
        self.database = getDatabaseName(self.isolationMode)     
        self.sessionId = createUniqueId()
 
    def chartStarted(self):
        return self.chartRunId != None
