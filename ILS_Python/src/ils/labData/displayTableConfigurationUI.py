'''
Created on Jun 15, 2015

@author: Pete
'''
import system

def internalFrameOpened(rootContainer):
    print "In internalFrameOpened, resetting dropdown..."
    rootContainer.getComponent("Dropdown").selectedValue = -1

def internalFrameActivated(rootContainer):
    print "In internalFrameActivated, calling update..."
    update(rootContainer)

def internalFrameClosing(rootContainer):
    print "In internalFrameClosing, doing nothing..."

'''
The list of lab data tables is ordered.
'''
def moveUp(event):
    rootContainer = event.source.parent
    table = rootContainer.getComponent("Power Table")
    ds = table.data
    
    row = table.selectedRow
    aboveRow = row - 1
    
    #get the TableIds and Orders to swap
    displayTableId = ds.getValueAt(row, "DisplayTableId")
    displayAboveTableId = ds.getValueAt(aboveRow, "DisplayTableId")
    displayOrderValue = ds.getValueAt(row, "DisplayOrder")
    displayAboveOrderValue = ds.getValueAt(aboveRow, "DisplayOrder")
    
    #update selected row so that highlighting changes with the move
    table.selectedRow = row - 1
    
    #update database swapping orders
    sql = "update LtDisplayTable set displayOrder = %i where displayTableId = %i" % (displayAboveOrderValue, displayTableId)
    system.db.runUpdateQuery(sql)
    sql = "update LtDisplayTable set displayOrder = %i where displayTableId = %i" % (displayOrderValue, displayAboveTableId)
    system.db.runUpdateQuery(sql)
    
    #refresh table
    print "Calling update() from moveDown()..."
    update(rootContainer)
    
'''
The list of lab data tables is ordered.
'''
def moveDown(event):
    rootContainer = event.source.parent
    table = rootContainer.getComponent("Power Table")
    ds = table.data

    row = table.selectedRow
    belowRow = row + 1

    #get the TableIds and Orders to swap
    displayTableId = ds.getValueAt(row, "DisplayTableId")
    displayBelowTableId = ds.getValueAt(belowRow, "DisplayTableId")
    displayOrderValue = ds.getValueAt(row, "DisplayOrder")
    displayBelowOrderValue = ds.getValueAt(belowRow, "DisplayOrder")

    #update selected row so that highlighting changes with the move
    table.selectedRow = row + 1
    
    #update database swapping orders
    sql = "update LtDisplayTable set displayOrder = %i where displayTableId = %i" % (displayBelowOrderValue, displayTableId)
    system.db.runUpdateQuery(sql)
    sql = "update LtDisplayTable set displayOrder = %i where displayTableId = %i" % (displayOrderValue, displayBelowTableId)
    system.db.runUpdateQuery(sql)

    #refresh table
    print "Calling update() from moveDown()..."
    update(rootContainer)


'''
The list of lab data tables is ordered.
'''
def moveLabValueUp(event):
    rootContainer = event.source.parent
    table = rootContainer.getComponent("ValueTable")
    ds = table.data

    row = table.selectedRow
    aboveRow = row - 1

    #get the TableIds and Orders to swap
    displayTableId = ds.getValueAt(row, "DisplayTableId")

    valueName = ds.getValueAt(row, "valueName")
    valueId = system.db.runScalarQuery("select ValueId from LtValue where ValueName = '%s'" % (valueName))

    valueAboveName = ds.getValueAt(aboveRow, "valueName")
    valueAboveId = system.db.runScalarQuery("select ValueId from LtValue where ValueName = '%s'" % (valueAboveName))

    #update selected row so that highlighting changes with the move
    table.selectedRow = row - 1

    #update database swapping orders
    sql = "update LtDisplayTableDetails set displayOrder = %i where displayTableId = %i and ValueId = %i" % (aboveRow, displayTableId, valueId)
    system.db.runUpdateQuery(sql)

    sql = "update LtDisplayTableDetails set displayOrder = %i where displayTableId = %i and ValueId = %i" % (row, displayTableId, valueAboveId)
    system.db.runUpdateQuery(sql)

    #refresh table
    print "Calling update() from moveLabValueUp()..."
    updateValues(rootContainer)


'''
The list of lab data tables is ordered.
'''
def moveLabValueDown(event):
    rootContainer = event.source.parent
    table = rootContainer.getComponent("ValueTable")
    ds = table.data

    row = table.selectedRow
    belowRow = row + 1

    #get the TableIds and Orders to swap
    displayTableId = ds.getValueAt(row, "DisplayTableId")
    
    valueName = ds.getValueAt(row, "valueName")
    valueId = system.db.runScalarQuery("select ValueId from LtValue where ValueName = '%s'" % (valueName))

    valueBelowName = ds.getValueAt(belowRow, "valueName")
    valueBelowId = system.db.runScalarQuery("select ValueId from LtValue where ValueName = '%s'" % (valueBelowName))

    #update selected row so that highlighting changes with the move
    table.selectedRow = row + 1
    
    #update database swapping orders
    sql = "update LtDisplayTableDetails set displayOrder = %i where displayTableId = %i and ValueId = %i" % (belowRow, displayTableId, valueId)
    system.db.runUpdateQuery(sql)

    sql = "update LtDisplayTableDetails set displayOrder = %i where displayTableId = %i and ValueId = %i" % (row, displayTableId, valueBelowId)
    system.db.runUpdateQuery(sql)

    #refresh table
    print "Calling update() from moveLabValueDown()..."
    updateValues(rootContainer)


'''
Update both tables, first the top table of display table names and te bottom table of values in the table
'''
def update(rootContainer):
    print "...updating..."
    table = rootContainer.getComponent("Power Table")
    
    dropDown= rootContainer.getComponent("Dropdown")
    postId = dropDown.selectedValue
    
    #update display table
    SQL = "SELECT * FROM LtDisplayTable "\
        " WHERE PostId = %i "\
        " ORDER BY DisplayPage, DisplayOrder " % (postId)
    print SQL
    pds = system.db.runQuery(SQL)
    table.updateInProgress = True
    table.data = pds
    updateValues(rootContainer)
    table.updateInProgress = False

'''
Update the bottom table which has the lab value names in the selected display table
'''
def updateValues(rootContainer):
    valueTable = rootContainer.getComponent("ValueTable")
    
    #update value table
    displayTableId = rootContainer.displayTableId
    sql = "SELECT V.ValueName, V.Description, DTD.DisplayTableId "\
        "FROM LtValue V, LtDisplayTableDetails DTD "\
        "WHERE DTD.DisplayTableId = %i "\
        "and DTD.ValueId = V.ValueId "\
        "order by DTD.DisplayOrder" % (displayTableId)
    print sql
    pds = system.db.runQuery(sql)
    valueTable.data = pds
   
#update the database when user directly changes table 
def updateDatabase(table, rowIndex, colName, newValue):
    ds = table.data
    displayTableId =  ds.getValueAt(rowIndex, "DisplayTableId")
    
    if colName == "DisplayTableTitle":
        SQL = "UPDATE LtDisplayTable SET DisplayTableTitle = '%s' "\
            "WHERE DisplayTableId = %i " % (newValue, displayTableId)
    elif colName == "DisplayPage":
        SQL = "UPDATE LtDisplayTable SET DisplayPage = %i "\
            "WHERE DisplayTableId = %i " % (newValue, displayTableId)
    else:
        if newValue == False:
            val = 0
        else:
            val = 1
        SQL = "UPDATE LtDisplayTable SET DisplayFlag = %i "\
            "WHERE DisplayTableId = %i " % (val, displayTableId)
            
    print SQL
    system.db.runUpdateQuery(SQL)

'''
Delete a display table
'''
def removeRow(event):
    rootContainer = event.source.parent
    table = rootContainer.getComponent("Power Table")
    ds = table.data
    
    row = table.selectedRow
    displayTableId = ds.getValueAt(row, "DisplayTableId")
    
    #check for references
    sql = "SELECT count(*) FROM LtDisplayTableDetails WHERE DisplayTableId = %i" %(displayTableId)
    rows = system.db.runScalarQuery(sql)

    if rows > 0:
        ans = system.gui.confirm("This table is in use. Do you want to remove this table?", "Confirm")
        if ans == False:
            return

    #remove the selected row
    SQL = "DELETE FROM LtDisplayTable "\
        " WHERE DisplayTableId = %i "\
        % (displayTableId)
    system.db.runUpdateQuery(SQL)
    
    #refresh table
    print "Calling update() from removeRow()..."
    update(rootContainer)
    
#add a row
def insertRow(event):
    rootContainer = event.source.parent
    table = rootContainer.getComponent("Power Table")
    ds = table.data
    
    numRows = ds.rowCount
    if numRows > 0:
        order = ds.getValueAt(numRows - 1, "DisplayOrder") 
    else:
        order = 0
    
    newName = system.gui.inputBox("Insert New Table Name:", "")
    if newName != None:
        DisplayPage = 1 #default DisplayPage = 1
        DisplayOrder = order + 10
        DisplayFlag = 0 #default DisplayFlag = 0, false
        PostId = rootContainer.getComponent("Dropdown").selectedValue 
        
        #insert the user's data as a new row
        SQL = "INSERT INTO LtDisplayTable (DisplayTableTitle, DisplayPage, DisplayOrder, DisplayFlag, PostId)"\
            "VALUES ('%s', %i, %d, %i, %i)" %(newName, DisplayPage, DisplayOrder, DisplayFlag, PostId)
        system.db.runUpdateQuery(SQL)
        
        #refresh table
        print "Calling update() from insertRow()..."
        update(rootContainer)

def addValueRowCallback(event):
    rootContainer = event.source.parent
    displayTableId = rootContainer.displayTableId
    postId = rootContainer.getComponent("Dropdown").selectedValue
    
    SQL = "select ValueName "\
        " from LtValue V, TkUnit U "\
        " where V.UnitId = U.UnitId "\
        " and U.PostId = %s "\
        " order by ValueName" % (str(postId))

    # For display table purposes, I think engineers want to be able to configure lab data on a screen regardless
    # of what unit it is assigned to.
    SQL = "select valueId, ValueName "\
        " from LtValue"\
        " order by ValueName"

    print SQL
    pds = system.db.runQuery(SQL)
    print "Selected %i lab values" % (len(pds))
    
    payload = {"displayTableId": displayTableId, "postId": postId, "data":pds}
    window = system.nav.openWindow("Lab Data/New Lab Data Display Table Row", payload)
    system.nav.centerWindow(window)
    
#remove the selected row
def removeValueRow(event):
    rootContainer = event.source.parent
    displayTableId = rootContainer.displayTableId
    valueTable = rootContainer.getComponent("ValueTable")
    row = valueTable.selectedRow
    ds = valueTable.data
    valueName = ds.getValueAt(row, "ValueName")
    
    SQL = "select ValueId from LtValue where ValueName = '%s'" % (valueName)  
    valueId = system.db.runScalarQuery(SQL)
        
    #remove the selected row
    SQL = "Delete from LtDisplayTableDetails "\
        "where displayTableId = %d "\
        "and valueId = %d" % (displayTableId, valueId)
    system.db.runUpdateQuery(SQL)
    
    #refresh table
    print "Calling update() from removeValueRow()..."
    update(rootContainer)

'''
Add a new lab value to the display table.  This is called from the OK button on the "New Lab Data Display Table Row" window.
'''
def insertValueRow(event):
    rootContainer = event.source.parent
    
    displayTableId = rootContainer.displayTableId
    valueId = rootContainer.getComponent("Dropdown").selectedValue
  
    SQL = "select count(*) from LtDisplayTableDetails where DisplayTableId = %d" % (displayTableId)  
    displayOrder = system.db.runScalarQuery(SQL)
    displayOrder = displayOrder + 1

    SQL = "insert into LtDisplayTableDetails (DisplayTableId, ValueId, DisplayOrder) values (%d, %d, %d) " % (displayTableId, valueId, displayOrder)
    print SQL
    system.db.runUpdateQuery(SQL)