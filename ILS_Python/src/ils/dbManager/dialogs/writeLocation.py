'''
Created on Mar 2, 2021

@author: phass

Scripts in support of the "WriteLocation" dialog
'''

import system
from ils.common.util import getRootContainer
from ils.dbManager.sql import idForPost
from ils.common.error import notifyError
from ils.common.config import getDatabaseClient
from ils.log import getLogger
log = getLogger(__name__)

# Called only when the screen is first displayed
def internalFrameOpened(component):
    log.trace("InternalFrameOpened")

# Called whenever the screen is brought to the top
def internalFrameActivated(component):
    log.trace("InternalFrameActivated")
    requery(component)

# Re-query the database and update the screen accordingly.
def requery(component):
    db = getDatabaseClient()
    log.info("unit.requery ...")
    container = getRootContainer(component)
    table = container.getComponent("DatabaseTable")

    SQL = "SELECT WriteLocationId, Alias, ServerName, ScanClass "\
        " FROM TkWriteLocation "\
        " ORDER by Alias"
    try:
        pds = system.db.runQuery(SQL, database=db)
        table.data = pds
    except:
        notifyError(__name__, "Fetching families")

# Delete the selected row.  The family is a primary key for many of the other recipe tables.  This delete works using cascade deletes.
def deleteRow(button):
    log.info("recipeFamily.deleteRow ...")
    db = getDatabaseClient()
    container = getRootContainer(button)
    table = container.getComponent("DatabaseTable")

    rownum = table.selectedRow
    ds = table.data
    writeLocationId = ds.getValueAt(rownum,'WriteLocationId')
    if writeLocationId >= 0:
        alias = ds.getValueAt(rownum,'Alias')
        confirm = system.gui.confirm("Are you sure that you want to delete write location <%s>?" % (alias))
        if confirm:
            SQL = "DELETE FROM TkWriteLocation WHERE WriteLocationId="+str(writeLocationId)
            system.db.runUpdateQuery(SQL, database=db)
            ds = system.dataset.deleteRow(ds,rownum)
            table.data = ds
            table.selectedRow = -1
            button.setEnabled(False)

            
# Called from the client startup script: View menu
def showWindow():
    window = "DBManager/WriteLocation"
    system.nav.openWindow(window)
    system.nav.centerWindow(window)
    
# Update database for a cell edit
def update(table, row, colname, value):
    log.info("%s.update (%d:%s)=%s ..." % (__name__, row, colname, str(value)))
    db = getDatabaseClient()
    ds = table.data
    writeLocationId = ds.getValueAt(row,0)
    
    if writeLocationId < 0:
        alias = ds.getValueAt(row, "Alias")
        serverName = ds.getValueAt(row, "ServerName")
        scanClass = ds.getValueAt(row, "ScanClass")
        
        if alias <> "" and serverName <> "" and scanClass <> "":
            SQL = "insert into TkWriteLocation (Alias, ServerName, ScanClass) values ('%s', '%s', '%s') " % (alias, serverName, scanClass)
            log.info(SQL)
            writeLocationId = system.db.runUpdateQuery(SQL, database=db)
            ds = system.dataset.setValue(ds, row, "WriteLocationId", writeLocationId)

    else:
        SQL = "UPDATE TkWriteLocation SET "+colname+" = '"+value+"' WHERE WriteLocationId="+str(writeLocationId)
        log.info(SQL)
        system.db.runUpdateQuery(SQL, database=db)
    
def addCallback(event):
    rootContainer = event.source.parent
    table = rootContainer.getComponent("DatabaseTable")
    ds = table.data
    ds = system.dataset.addRow(ds, [-1,"", "", ""])
    table.data = ds
    
def exportCallback(event):
    db = getDatabaseClient()      
    SQL = "SELECT WriteLocationId, Alias, ServerName, ScanClass FROM TkWriteLocation ORDER by Alias"
    pds = system.db.runQuery(SQL, database=db)
    csv = system.dataset.toCSV(pds)
    filePath = system.file.saveFile("WriteLocation.csv", "csv", "Comma Separated Values")
    if filePath:
        system.file.writeFile(filePath, csv)