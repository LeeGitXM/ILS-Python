'''
Created on Jul 18, 2017

@author: phass
'''

import system
from ils.common.config import getDatabaseClient

def internalFrameOpened(event):
    print "In %s.internalFrameOpened()" % (__name__)
    db = getDatabaseClient()
    rootContainer = event.source.rootContainer
    windowId = rootContainer.windowId
    
    SQL = "select message from SfcBusyNotification where windowId = '%s'" % (windowId)
    message = system.db.runScalarQuery(SQL, database=db)
    rootContainer.message = message
    
    SQL = "select title from SfcWindow where windowId = '%s'" % (windowId)
    title = system.db.runScalarQuery(SQL, database=db)
    rootContainer.title = title