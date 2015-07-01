'''
Created on Jun 15, 2015

@author: Pete
'''
import system

#
#move selected row up
def moveUp(event):
    rootContainer = event.source.parent
    txID = rootContainer.txID
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
    system.db.runUpdateQuery(sql, tx = txID)
    sql = "update LtDisplayTable set displayOrder = %i where displayTableId = %i" % (displayOrderValue, displayAboveTableId)
    system.db.runUpdateQuery(sql, tx = txID)
    
    #refresh table
    update(rootContainer)

#open transaction when window is opened
def internalFrameOpened(rootContainer):
    txID = system.db.beginTransaction(timeout=300000)
    rootContainer.txID = txID
    update(rootContainer)
    
#refresh when window is activated
def internalFrameActivated(rootContainer):
    update(rootContainer)

#update the window
def update(rootContainer):
    txID = rootContainer.txID
    table = rootContainer.getComponent("Power Table")
    valueTable = rootContainer.getComponent("ValueTable")
    dropDown= rootContainer.getComponent("Dropdown")
    postId = dropDown.selectedValue
    
    #update display table
    SQL = "SELECT * FROM LtDisplayTable "\
        " WHERE PostId = %i "\
        " ORDER BY DisplayPage, DisplayOrder " % (postId)
    print SQL
    pds = system.db.runQuery(SQL, tx=txID)
    table.updateInProgress = True
    table.data = pds
    table.updateInProgress = False
    
    #update value table
    displayTableId = rootContainer.DisplayTableId
    sql = "SELECT ValueName, Description, DisplayTableId "\
        "FROM LtValue "\
        "WHERE DisplayTableId = %i " % (displayTableId)
    pds = system.db.runQuery(sql, tx=txID)
    valueTable.data = pds
    
#move selected row down
def moveDown(event):
    rootContainer = event.source.parent
    txID = rootContainer.txID
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
    system.db.runUpdateQuery(sql, tx = txID)
    sql = "update LtDisplayTable set displayOrder = %i where displayTableId = %i" % (displayOrderValue, displayBelowTableId)
    system.db.runUpdateQuery(sql, tx = txID)

    #refresh table
    update(rootContainer)
    
#remove the selected row
def removeRow(event):
    rootContainer = event.source.parent
    txID = rootContainer.txID
    table = rootContainer.getComponent("Power Table")
    ds = table.data
    
    row = table.selectedRow
    displayTableId = ds.getValueAt(row, "DisplayTableId")
    
    #check for references
    sql = "SELECT count(*) FROM LtValue WHERE DisplayTableId = %i" %(displayTableId)
    rows = system.db.runScalarQuery(sql, tx=txID)
    
    if rows > 0:
        ans = system.gui.confirm("This table is in use. Do you want to remove this table?", "Confirm")
        if ans == False:
            return
        else:
            sql = "update LtValue SET DisplayTableId = NULL WHERE DisplayTableId = %i" %(displayTableId)
            system.db.runUpdateQuery(sql, tx=txID)
            
    #remove the selected row
    SQL = "DELETE FROM LtDisplayTable "\
        " WHERE DisplayTableId = %i "\
        % (displayTableId)
    system.db.runUpdateQuery(SQL, tx=txID)
    
    #refresh table
    update(rootContainer)
    
#add a row
def insertRow(event):
    rootContainer = event.source.parent
    txID = rootContainer.txID
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
        system.db.runUpdateQuery(SQL, tx=txID)
        
        #refresh table
        update(rootContainer)
    
#add a row of values
def insertValueRow(event):
    rootContainer = event.source.parent
    txID = rootContainer.txID
    
    displayTableId = rootContainer.DisplayTableId
    newName = rootContainer.getComponent("Dropdown").selectedStringValue
    
    #insert the user's data as a new row
    SQL = "UPDATE LtValue SET DisplayTableId = %i "\
        "WHERE ValueName = '%s' " %(displayTableId, newName)
    print SQL
    system.db.runUpdateQuery(SQL, tx=txID)
    
#remove the selected row
def removeValueRow(event):
    rootContainer = event.source.parent
    txID = rootContainer.txID
    valueTable = rootContainer.getComponent("ValueTable")
    row = valueTable.selectedRow
    ds = valueTable.data
    valueName = ds.getValueAt(row, "ValueName")
        
    #remove the selected row
    SQL = "UPDATE LtValue "\
        " SET DisplayTableId = NULL "\
        "WHERE ValueName = '%s' " % (valueName)
    system.db.runUpdateQuery(SQL, tx=txID)
    
    #refresh table
    update(rootContainer)
    