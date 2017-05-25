'''
Created on Dec 3, 2015

@author: rforbes
'''

import system, time
from ils.sfc.common.constants import YES_RESPONSE, NO_RESPONSE
from ils.common.config import getDatabaseClient
from ils.sfc.recipeData.core import splitKey, setRecipeData

def internalFrameOpened(event):
    print "In internalFrameOpened() for a YesNo window..." 
    rootContainer = event.source.rootContainer
    windowId = rootContainer.windowId
    print "The windowId is: ",windowId
    
    SQL = "select * from SfcWindow where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL)
    if len(pds) <> 1:
        system.gui.errorBox("Error initializing the YesNo window, window not found in SfcWindow")
        return
    
    record=pds[0]
    rootContainer.title = record["title"]
    
    SQL = "select * from SfcInput where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL)
    if len(pds) <> 1:
        system.gui.errorBox("Error initializing the YesNo window, window not found in SfcInput")
        return
    
    record = pds[0]

    rootContainer.prompt = record["prompt"]
    rootContainer.keyAndAttribute = record["keyAndAttribute"]
    rootContainer.targetStepUUID = record["targetStepUUID"]

def yesActionPerformed(event):
    print "YES was pressed"
    setResponse(event, YES_RESPONSE)
  
def noActionPerformed(event):
    print "NO was pressed"
    setResponse(event, NO_RESPONSE)
    
def setResponse(event, response):
    db = getDatabaseClient()
    rootContainer = event.source.parent
    targetStepUUID = rootContainer.targetStepUUID
    keyAndAttribute = rootContainer.keyAndAttribute
    key,attribute = splitKey(keyAndAttribute)
    setRecipeData(targetStepUUID, key, attribute, response, db)
    system.nav.closeParentWindow(event)