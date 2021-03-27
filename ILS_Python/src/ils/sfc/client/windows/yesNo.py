'''
Created on Dec 3, 2015

@author: rforbes
'''
import system
from ils.sfc.common.constants import YES_RESPONSE, NO_RESPONSE
from ils.common.config import getDatabaseClient
from ils.sfc.client.util import setClientDone, setClientResponse
from ils.log.LogRecorder import LogRecorder
log = LogRecorder(__name__)

def internalFrameOpened(event):
    log.infof("In %s.internalFrameOpened()", __name__) 
    rootContainer = event.source.rootContainer
    windowId = rootContainer.windowId
    db = getDatabaseClient()
    
    title = system.db.runScalarQuery("select title from sfcWindow where windowId = '%s'" % (windowId), db)
    rootContainer.title = title
    
    SQL = "select * from SfcInput where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL, database=db)
    if len(pds) <> 1:
        system.gui.errorBox("Error initializing the YesNo window, window not found in SfcInput")
        return
    
    record = pds[0]

    rootContainer.prompt = record["prompt"]
    rootContainer.keyAndAttribute = record["keyAndAttribute"]
    rootContainer.targetStepId = record["targetStepId"]
    rootContainer.chartId = record["chartId"]
    rootContainer.stepId = record["stepId"]
    rootContainer.responseLocation = record["responseLocation"]

def yesActionPerformed(event):
    log.infof("YES was pressed")
    setResponse(event, YES_RESPONSE)
  
def noActionPerformed(event):
    log.infof("NO was pressed")
    setResponse(event, NO_RESPONSE)
    
def setResponse(event, response):
    rootContainer = event.source.parent
    setClientResponse(rootContainer, response)
    setClientDone(rootContainer)
    system.nav.closeParentWindow(event)