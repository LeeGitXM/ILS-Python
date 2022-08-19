'''
Created on Jan 5, 2016

@author: rforbes
'''

import system
from ils.config.client import getDatabase

def internalFrameOpened(event):
    print "In internalDrameOpened()" 
    rootContainer = event.source.rootContainer
    windowId = rootContainer.windowId
    db = getDatabase()
    
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


def okActionPerformed(event):
    print "Processing OK action"
    rootContainer = event.source.parent
    windowId = rootContainer.windowId
    db = getDatabase()

    # Updating the database communicates with the running step in the gateway which may or may not be waiting for an acknowledgement and
    # it communicates with other clients that are displaying the same notification.  One ACK dismisses all of them.
    SQL = "update SfcDialogMessage set acknowledged = 1 where windowId = '%s'" % (windowId)
    system.db.runUpdateQuery(SQL, database=db)
    
    # This will unregister the window from the control panel
    SQL = "delete from SfcWindow where windowId = '%s'" % (windowId)
    rows = system.db.runUpdateQuery(SQL, database=db)
    print "Deleted %i rows from the sfcWindow table..." % (rows)
    
    system.nav.closeParentWindow(event)

def checkWindowStatus(event):
    db = getDatabase()
    rootContainer = event.source.parent
    windowId = rootContainer.windowId
    SQL = "select acknowledged from sfcDialogMessage where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL, database=db)
    if len(pds) == 0:
        print "Closing the window because it no longer exists."
        system.nav.closeParentWindow(event)
        return
    
    record = pds[0]
    acknowledged = record["acknowledged"]
    if acknowledged:
        print "Closing the window because it has already been acknowledged."
        system.nav.closeParentWindow(event)