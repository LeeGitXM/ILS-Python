'''
Created on Jul 18, 2017

@author: phass
'''

import system
from ils.config.client import getDatabase


def internalFrameOpened(event):
    print "In %s.internalFrameOpened()" % (__name__)
    db = getDatabase()
    rootContainer = event.source.rootContainer
    windowId = rootContainer.windowId
    
    SQL = "select message from SfcBusyNotification where windowId = '%s'" % (windowId)
    message = system.db.runScalarQuery(SQL, database=db)
    rootContainer.message = message
    
    SQL = "select title from SfcWindow where windowId = '%s'" % (windowId)
    title = system.db.runScalarQuery(SQL, database=db)
    rootContainer.title = title

'''
This is called from a timer on the window.
'''
def refresh(rootContainer):
    db = getDatabase()
    windowId = rootContainer.windowId
    
    SQL = "select message from SfcBusyNotification where windowId = '%s'" % (windowId)
    message = system.db.runScalarQuery(SQL, database=db)
    rootContainer.message = message