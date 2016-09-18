'''
Created on Sep 16, 2016

@author: Pete
'''

import system

def internalFrameOpened(rootContainer):
    print "Initializing..."
    db = system.tag.read("[Client]Database").value
    print "The database is: ", db
    txId = system.db.beginTransaction(database=db, timeout=60000)
    rootContainer.txId = txId
    refreshTable(rootContainer)

# Update the Power table with data from the database.  This is only run when the window is opened.
def refreshTable(rootContainer):
    print "Refreshing..."
    table = rootContainer.getComponent("Power Table")
    txId = rootContainer.txId
    SQL = "select logbookId, logbookName from TkLogbook order by logbookName"
    ds = system.db.runQuery(SQL, tx=txId)
    table.data = ds

# This is called from a timer on the window and it just executes a really fast query to 
# keep the transaction from timing out.
def keepAlive(rootContainer):
    txId = rootContainer.txId
    SQL = "select count(*) from TkLogbook"
    cnt = system.db.runScalarPrepQuery(SQL, tx=txId)

# Add a new row to the table.  We don't add a row to the database because the row is empty.
def add(rootContainer):
    txId = rootContainer.txId
    table = rootContainer.getComponent("Power Table")
    ds = table.data
    ds = system.dataset.addRow(ds,[-1,""])
    table.data = ds

# Delete a row from the table and the database if it was in the database
def delete(rootContainer):
    txId = rootContainer.txId
    table = rootContainer.getComponent("Power Table")
    row = table.selectedRow
    ds = table.data
    logbookId = ds.getValueAt(row,0)
    if logbookId > 0:
        SQL = "delete from TkLogbook where LogbookId = %i" % (logbookId)
        rows = system.db.runUpdateQuery(SQL,tx=txId)
        print "Deleted %i rows" % (rows)
    ds = system.dataset.deleteRow(ds, row)
    table.data = ds

# This is not called when a row id added or deleted.
def cellEdited(table, row, col, colName, oldValue, newValue):
    print "In cellEdited(), edited row: %i, col: %i" % (row, col)
    rootContainer = table.parent
    txId = rootContainer.txId
    ds = table.data
    logbookId = ds.getValueAt(row,0)
    if logbookId >= 0:
        print "Updating..."
        SQL = "Update TkLogbook set LogbookName = '%s' where LogbookId = %s" % (newValue, logbookId)
        print SQL
        system.db.runUpdateQuery(SQL, tx=txId)
    else:
        print "Adding..."
        SQL = "insert into TkLogbook (LogbookName) values ('%s')" % (newValue)
        print SQL
        logbookId=system.db.runUpdateQuery(SQL, getKey=True, tx=txId)
        ds=system.dataset.setValue(ds, row, 0, logbookId)
        table.data=ds

def save(rootContainer):
    txId = rootContainer.txId
    system.db.commitTransaction(txId)
    system.db.closeTransaction(txId)
    
def apply(rootContainer):
    txId = rootContainer.txId
    system.db.commitTransaction(txId)

def rollback(rootContainer):
    txId = rootContainer.txId
    system.db.rollbackTransaction(txId)
    system.db.closeTransaction(txId)
    