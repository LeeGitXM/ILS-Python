'''
Created on Mar 21, 2017

@author: phass

Scripts in support of the "Flying Switch" dialog
'''

import sys, system, traceback
from ils.dbManager.ui import populateRecipeFamilyDropdown
from ils.dbManager.sql import getRootContainer, getTransactionForComponent, rollbackTransactionForComponent, closeTransactionForComponent, commitTransactionForComponent, idForFamily
from ils.dbManager.userdefaults import get as getUserDefaults
log = system.util.getLogger("com.ils.recipe.flyingswitch")


# When the screen is first displayed, set widgets for user defaults
# The "active" dropdown is always initialized to "TRUE"
def internalFrameOpened(window):
    log.trace("InternalFrameOpened")
    container = window.rootContainer

    # Clear the current transaction.
    rollbackTransactionForComponent(container)


# When the screen is first displayed, set widgets for user defaults
# The "active" dropdown is always initialized to "TRUE"
def internalFrameActivated(window):
    log.trace("InternalFrameActivated")
    container = window.rootContainer
    requery(container)


# Re-query the database and update the screen accordingly.
# If we get an exception, then rollback the transaction.
def requery(component):
    log.info("flyingswitch.requery ...")
    container = getRootContainer(component)
    table = container.getComponent("DatabaseTable")
    
    SQL = "SELECT ' ' as Selector, Id, CurrentGrade, NextGrade " \
        "FROM RtAllowedFlyingSwitch " \
        "ORDER BY CurrentGrade, NextGrade"
    
    txn = getTransactionForComponent(table)
    try:
        pds = system.db.runQuery(SQL,tx=txn)
        table.data = pds
    except:
        # type,value,traceback
        type,value,trace = sys.exc_info()
        print "**************"
        print traceback.format_exception(type, value,trace,100)
        print "***************"
        log.info("flyingswitch.requery: SQL Exception ... %s" % (str(value))) 
        rollbackTransactionForComponent(table)
        system.gui.messageBox("Error querying RtAllowedFlyingSwitch table")

# Called from the client startup script: View menu
# Note: No attempt is made at this point to reconcile with any tab strip
def showWindow():
    window = "DBManager/FlyingSwitch"
    system.nav.openWindow(window)
    system.nav.centerWindow(window)

# By deleting a row, we are deleting a flying switch grade transition.
def deleteRow(button):
    log.info("flyingswitch.deleteRow ...")
    container = getRootContainer(button)
    table = container.getComponent("DatabaseTable")
    txn = getTransactionForComponent(button)
    rownum = table.selectedRow
    ds = table.data
    id = ds.getValueAt(rownum,'Id')
    if id > 0:
        SQL = "DELETE FROM RtAllowedFlyingSwitch WHERE id = %i" % (id)
        log.trace(SQL)
        rows = system.db.runUpdateQuery(SQL,tx=txn)
        log.trace("%i rows were deleted" % (rows))
        ds = system.dataset.deleteRow(ds,rownum)
        # update the table
        table.data = ds
        table.selectedRow = -1

# Add a new row to the table. The data element is a DataSet (not python)
def addRow(button):
    log.info("flyingswitch.addRow ...")
    container = getRootContainer(button)
    table = container.getComponent("DatabaseTable")
    ds = table.data
    if table.selectedRow >= 0:
        row = table.selectedRow
    else:
        row = 0
    ds = system.dataset.addRow(ds, row, ["", -1,"",""])
    table.data = ds

# Update database for a cell edit.  Can do an insert or update!
def update(table,row):
    log.info("flyingswitch.update (row %d)..." % (row))
    txn = getTransactionForComponent(table)
    ds = table.data
    #column is LowerLimit or UpperLimit. Others are not editable.
    id = ds.getValueAt(row,'Id')
    currentGrade = ds.getValueAt(row,'CurrentGrade')
    nextGrade = ds.getValueAt(row,'NextGrade')
    
    if id < 0:
        # Insert a new record
        try:
            SQL = "INSERT into RtAllowedFlyingSwitch (CurrentGrade, NextGrade) values ('%s', '%s')" % (str(currentGrade), str(nextGrade))
            log.trace(SQL)
            id = system.db.runUpdateQuery(SQL,tx=txn,getKey=True)
            log.trace("Inserted new id: %i" % (id))
            ds = system.dataset.setValue(ds,row,"Id",id)
            table.data = ds
        except:
            msg = "Error updating RtAllowedFlyingSwitch."
            system.gui.warningBox(msg)

    else:
        # Update an existing record
        try:
            SQL = "UPDATE RtAllowedFlyingSwitch SET CurrentGrade = '%s', NextGrade = '%s' " \
                " WHERE Id = %i " % (str(currentGrade), str(nextGrade), id)
            log.trace(SQL)
            rows = system.db.runUpdateQuery(SQL,tx=txn)
            log.trace("Updated %i rows" % (rows))
        except:
            msg = "Error updating RtAllowedFlyingSwitch."
            system.gui.warningBox(msg)