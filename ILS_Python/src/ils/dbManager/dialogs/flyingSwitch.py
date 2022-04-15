'''
Created on Mar 21, 2017

@author: phass

Scripts in support of the "Flying Switch" dialog
'''

import system
from ils.common.util import getRootContainer
from ils.common.error import notifyError
from ils.common.config import getDatabaseClient
from ils.log import getLogger
log = getLogger(__name__)

# Called from the client startup script: View menu
# Note: No attempt is made at this point to reconcile with any tab strip
def showWindow():
    window = "DBManager/FlyingSwitch"
    system.nav.openWindow(window)
    system.nav.centerWindow(window)

# When the screen is first displayed, set widgets for user defaults
# The "active" dropdown is always initialized to "TRUE"
def internalFrameOpened(window):
    log.trace("InternalFrameOpened")

# When the screen is first displayed, set widgets for user defaults
# The "active" dropdown is always initialized to "TRUE"
def internalFrameActivated(rootContainer):
    log.trace("InternalFrameActivated")
    requery(rootContainer)

# Re-query the database and update the screen accordingly.
# If we get an exception, then rollback the transaction.
def requery(component):
    log.info("flyingswitch.requery ...")
    db = getDatabaseClient()
    container = getRootContainer(component)
    table = container.getComponent("DatabaseTable")
    
    SQL = "SELECT ' ' as Selector, Id, CurrentGrade, NextGrade " \
        "FROM RtAllowedFlyingSwitch " \
        "ORDER BY CurrentGrade, NextGrade"
    
    try:
        pds = system.db.runQuery(SQL, database=db)
        table.data = pds
    except:
        notifyError(__name__, "Fetching Flying Switches")


# By deleting a row, we are deleting a flying switch grade transition.
def deleteRow(button):
    log.info("flyingswitch.deleteRow ...")
    db = getDatabaseClient()
    container = getRootContainer(button)
    table = container.getComponent("DatabaseTable")

    rownum = table.selectedRow
    ds = table.data
    rowId = ds.getValueAt(rownum,'Id')
    if id > 0:
        try:
            SQL = "DELETE FROM RtAllowedFlyingSwitch WHERE id = %i" % (rowId)
            log.trace(SQL)
            rows = system.db.runUpdateQuery(SQL, database=db)
            log.trace("%d rows were deleted" % (rows))
        except:
            notifyError(__name__, "Error deleting a Flying Switch")
        else:
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
    db = getDatabaseClient()
    ds = table.data
    #column is LowerLimit or UpperLimit. Others are not editable.
    rowId = ds.getValueAt(row,'Id')
    currentGrade = ds.getValueAt(row,'CurrentGrade')
    nextGrade = ds.getValueAt(row,'NextGrade')
    
    if rowId < 0:
        # Insert a new record
        try:
            SQL = "INSERT into RtAllowedFlyingSwitch (CurrentGrade, NextGrade) values ('%s', '%s')" % (str(currentGrade), str(nextGrade))
            log.trace(SQL)
            rowId = system.db.runUpdateQuery(SQL, getKey=True, database=db)
            log.trace("Inserted new id: %s" % (str(id)))

        except:
            notifyError(__name__, "Error updating RtAllowedFlyingSwitch.")
            
        else:
            ds = system.dataset.setValue(ds, row, "Id", rowId)
            table.data = ds

    else:
        # Update an existing record
        try:
            SQL = "UPDATE RtAllowedFlyingSwitch SET CurrentGrade = '%s', NextGrade = '%s' " \
                " WHERE Id = %s " % (str(currentGrade), str(nextGrade), str(rowId))
            log.trace(SQL)
            rows = system.db.runUpdateQuery(SQL, database=db)
            log.trace("Updated %d rows" % (rows))
        except:
            notifyError(__name__, "Error updating RtAllowedFlyingSwitch.")