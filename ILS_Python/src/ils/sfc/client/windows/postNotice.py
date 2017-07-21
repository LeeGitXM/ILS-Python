'''
Created on Jul 18, 2017

@author: phass
'''

import system
from ils.common.config import getDatabaseClient

def internalFrameOpened(event):
    print "In internalFrameOpened()" 
    rootContainer = event.source.rootContainer
    windowId = rootContainer.windowId
    
    db = getDatabaseClient()
    
    SQL = "select message, ackRequired from SfcDialogMessage where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL, database=db)
    record=pds[0]
    message=record["message"]
    ackRequired=record["ackRequired"]
    rootContainer.theMessage = message
    rootContainer.ackRequired = ackRequired
    
    SQL = "select title from SfcWindow where windowId = '%s'" % (windowId)
    title = system.db.runScalarQuery(SQL, database=db)
    rootContainer.title = title