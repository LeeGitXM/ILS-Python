'''
Created on Mar 21, 2017

@author: phass
'''

import system, string
log = system.util.getLogger("com.ils.recipe.ui")
from ils.common.error import notifyError

# Called from the client startup script: View menu
# Note: No attempt is made at this point to reconcile with any tab strip
def showWindow():
    window = "DBManager/Adhoc"
    system.nav.openWindow(window)
    system.nav.centerWindow(window)

# This is the first handler that is called when the window is displayed once.  It is not 
# called when the window is brought to the top.
def internalFrameOpened(rootContainer):
    log.trace("InternalFrameOpened")

# This is the second handler that is called when the windo is displayed.
def internalFrameActivated(rootContainer):
    log.trace("InternalFrameActivated")
    requery(rootContainer)

# Re-query the database and update the screen accordingly.
# If we get an exception, then rollback the transaction.
def requery(rootContainer):
    log.info("adhoc.requery ...")
    dropdown = rootContainer.getComponent("TableNameDropdown")
    tableName = dropdown.selectedStringValue
    table = rootContainer.getComponent("DatabaseTable")
    SQL = "SELECT * FROM %s " % (tableName)
    log.trace(SQL)

    try:
        pds = system.db.runQuery(SQL)
        table.data = pds
    except:
        notifyError(__name__, "Error initializing table")

    else:
        # Technically, we only need to do this when the user changes tables, but 
        # this is pretty lightweight so it doesn't hurt to run it too often.
        configTable(rootContainer)

# To add a row we need to supply values for each cell in the row.
# Since a power table does not explicitly have an addRow() function, I'll get the dataset,
# add a row to it and then put it back into the table.
def addRow(event):
    log.trace("Adding a row...")
    rootContainer = event.source.parent
    table = rootContainer.getComponent("DatabaseTable")
    row=table.selectedRow
    if row == -1: row = 0
    ds = table.data
    headers = system.dataset.getColumnHeaders(ds)
    vals = []
    for column in headers:
        print column
        if column == 'Id':
            vals.append(-1)
        else:
            vals.append("")
    ds=system.dataset.addRow(ds,row,vals)
    table.data=ds

# By deleting a row, we are deleting the parameter for every grade for the unit.
def deleteRow(event):
    button = event.source
    log.trace("adhoc.deleteRow ...")
    rootContainer = button.parent
    table = rootContainer.getComponent("DatabaseTable")
    rownum = table.selectedRow
    dropdown = rootContainer.getComponent("TableNameDropdown")
    tableName = dropdown.selectedStringValue
    ds = table.data
    theId = ds.getValueAt(rownum,'Id')
    
    # The row being deleted may or may not be in the database, they could have 
    # started to add a row and then deleted it before it was added to the database
    if id > 0:
        SQL = "DELETE FROM %s WHERE Id = %i" % (tableName, theId)
        log.trace(SQL)
        rows = system.db.runUpdateQuery(SQL)
        log.info("Deleted %i rows from %s" % (rows, tableName))

    ds = system.dataset.deleteRow(ds,rownum)
    table.data = ds
    table.selectedRow = -1
    
# Update database for a cell edit. We only allow edits of parameter name or 
# limits.
def update(table,row,colname,value):
    log.info("adhoc.update (%d:%s)=%s ..." %(row,colname,str(value)))
    rootContainer = table.parent
    ds = table.data
    recordId=ds.getValueAt(row,"Id")
    dropdown = rootContainer.getComponent("TableNameDropdown")
    tableName = dropdown.selectedStringValue

    # The user is entering a new row if the id = -1 or is empty.  
    # By definition, all of the columns of an adhoc table must allow nulls.  This allows me to insert 
    # a row when they enter the first value, fetch the id, and use it for subsequent updates      
    if recordId < 0 or recordId == "":
        try:
            x = float(value)
            SQL = "insert into %s (%s) values (%s)" % (tableName, colname, str(value))
        except:
            SQL = "insert into %s (%s) values ('%s')" % (tableName, colname, str(value))
            
        log.trace(SQL)
        recordId=system.db.runUpdateQuery(SQL, getKey=True)
        log.info("Inserted a new row with id = %i" % (recordId))
        ds = system.dataset.setValue(ds, row, "Id", recordId)
        table.data = ds
    else:
        # Need to handle numbers different than text strings.  This assumes that the column 
        # datatype in the database is float or int
        try:
            x = float(value)
            SQL = "UPDATE %s SET %s = %s WHERE Id = %i" % (tableName, colname, str(value), recordId)
        except:
            SQL = "UPDATE %s SET %s = '%s' WHERE Id = %i" % (tableName, colname, str(value), recordId)
        
        log.trace(SQL)
        rows=system.db.runUpdateQuery(SQL)
        log.info("Updated %i rows" % (rows))
    
    requery(rootContainer)  
    
# Make the columns of the table editable
def configTable(rootContainer):
    print "In configTable..."
    table = rootContainer.getComponent("DatabaseTable")
    ds = table.data
    columns=system.dataset.getColumnHeaders(ds)

    header=['name','dateFormat','editable','filterable','hidden','horizontalAlignment','label','numberFormat','prefix','sortable','suffix','treatAsBoolean','verticalAlignment']
    data=[]
    for col in columns:
        if string.upper(col) == 'ID':
            hidden = True
        else:
            hidden = False

        record = [col,'MMM d,yyyy h:mm a',True,False,hidden,-9,'','#,##0.##','',True,'',False,0]
        data.append(record)
        print record
    ds = system.dataset.toDataSet(header,data)
    table.columnAttributesData=ds