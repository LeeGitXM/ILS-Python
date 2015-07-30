'''
Created on Jul 24, 2015

@author: Joe
'''
import system
from ils.sfc.common.constants import SQL

#initialize view window when opened
def viewInternalFrameOpened(rootContainer):
    print "Opening view queues..."
    table = rootContainer.getComponent("Power Table")
    
    SQL = "SELECT QueueId, QueueKey, Title FROM QueueMaster "\
        "ORDER BY QueueKey "
    print SQL
    pds = system.db.runQuery(SQL)
    table.data = pds
    
#open transaction when manage window is opened and initialize the window
def manageInternalFrameOpened(rootContainer):
    # Keep the transaction open for one hour...
    print "Opening manage queues..."
    
    txId = system.db.beginTransaction(timeout=3600000)
    rootContainer.txId = txId
    refreshScreen(rootContainer)
    
#close transaction when manage window is closed
def internalFrameClosing(rootContainer):
    try:
        txId=rootContainer.txId
        system.db.rollbackTransaction(txId)
        print "Closing the transaction..."
        system.db.closeTransaction(txId)
    except:
        print "Caught an error trying to close the transaction"


def update(rootContainer):
    print "updating..."
    table = rootContainer.getComponent("Power Table")
    ds = table.data
    row = table.selectedRow
    if row >= 0:
        rootContainer.queueKey = ds.getValueAt(row, "QueueKey")
    
#insert a blank row
def insertRow(event):
    rootContainer = event.source.parent
    table = rootContainer.getComponent("Power Table")
    table.selectedRow = -1
    ds = table.data
    newRow = [-1, "", ""]
    ds = system.dataset.addRow(ds, 0, newRow)
    table.data = ds
    
def cellEdited(table, rowIndex, colName, newValue):
    print "A cell has been edited so update the database..."
    rootContainer = table.parent
    txId = rootContainer.txId
    ds = table.data
    queueId = ds.getValueAt(rowIndex, 0)
    
    if colName == 'Title':
        SQL = "UPDATE QueueMaster SET Title = '%s' "\
            "WHERE QueueId = %i " % (newValue, queueId)
        print SQL
        system.db.runUpdateQuery(SQL, tx=txId)
    elif colName == 'QueueKey':
        SQL = "UPDATE QueueMaster SET QueueKey = '%s' "\
            "WHERE QueueId = %i " % (newValue, queueId)
        print SQL
        system.db.runUpdateQuery(SQL, tx=txId)
        
def newQueue(rootContainer):
    txId = rootContainer.txId
    table = rootContainer.getComponent("Power Table")
    ds = table.data
    row = table.selectedRow
    
    queueKey = ds.getValueAt(row, "QueueKey")
    title = ds.getValueAt(row, "Title")
    print "queueKey = ",queueKey
    print "title = ",title
    
    if queueKey!= "" and title != "": 
        print "Sufficient data provided. Entering new queue to the database..."
        SQL = "INSERT INTO QueueMaster (QueueKey, Title) "\
            " VALUES ('%s', '%s')" % (queueKey, title)
        print SQL
        system.db.runUpdateQuery(SQL, tx=txId)
    else:
        print "Insufficient data to insert new queue."
        
def commitChanges(rootContainer):
    txId=rootContainer.txId
    system.db.commitTransaction(txId)

def removeRow(event):
    print "Running Remove Row..."
    rootContainer = event.source.parent
    txId = rootContainer.txId
    table = rootContainer.getComponent("Power Table")
    ds = table.data
    row = table.selectedRow
    queueId = ds.getValueAt(row,"QueueId")
    
    #check for references
    sql = "SELECT count(*) FROM QueueDetail WHERE QueueId = %i" % (queueId)
    print sql
    triggerRows = system.db.runScalarQuery(sql, tx=txId)
    sql = "SELECT count(*) FROM DtApplication WHERE MessageQueueId = %i" % (queueId)
    relatedRows = system.db.runScalarQuery(sql, tx=txId)
    numReferences = relatedRows + triggerRows
    print "numReferences = ",numReferences
    
    if numReferences > 0:
        print "References found cannot delete"
        return
    
    #no references found: delete as normal
    SQL = "DELETE FROM QueueMaster "\
        " WHERE QueueId = %i " % (queueId)
    print SQL
    system.db.runUpdateQuery(SQL, tx=txId)
     
#refresh the table to update immediately after deletion
def refreshScreen(rootContainer):
    print "In refreshScreen..."
    txId = rootContainer.txId
    table = rootContainer.getComponent("Power Table")
    SQL = "SELECT QueueId, QueueKey, Title FROM QueueMaster "\
        " ORDER BY QueueKey "
    print SQL
    pds = system.db.runQuery(SQL, tx=txId)
    table.data = pds     