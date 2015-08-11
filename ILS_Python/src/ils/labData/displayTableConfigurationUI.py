'''
Created on Jun 15, 2015

@author: Pete
'''
import system

#open transaction when window is opened
def internalFrameOpened(rootContainer):
    # Open the transaction for one hour
    print "Reserving a transaction id..."
    txId = system.db.beginTransaction(timeout=3600000)
    rootContainer.txId = txId
    rootContainer.getComponent("Dropdown").selectedValue = -1
    
#refresh when window is activated
def internalFrameActivated(rootContainer):
    print "In internalFrameActivated, calling update..."
    update(rootContainer)

#open transaction when window is opened
def internalFrameClosing(rootContainer):
    try:
        txId=rootContainer.txId
        system.db.rollbackTransaction(txId)
        print "Closing the transaction..."
        system.db.closeTransaction(txId)
    except:
        print "Caught an error trying to close the transaction"

#move selected row up
def moveUp(event):
    rootContainer = event.source.parent
    txId = rootContainer.txId
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
    system.db.runUpdateQuery(sql, tx = txId)
    sql = "update LtDisplayTable set displayOrder = %i where displayTableId = %i" % (displayOrderValue, displayAboveTableId)
    system.db.runUpdateQuery(sql, tx = txId)
    
    #refresh table
    print "Calling update() from moveDown()..."
    update(rootContainer)
    
#move selected row down
def moveDown(event):
    rootContainer = event.source.parent
    txId = rootContainer.txId
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
    system.db.runUpdateQuery(sql, tx = txId)
    sql = "update LtDisplayTable set displayOrder = %i where displayTableId = %i" % (displayOrderValue, displayBelowTableId)
    system.db.runUpdateQuery(sql, tx = txId)

    #refresh table
    print "Calling update() from moveDown()..."
    update(rootContainer)


#update the window
def update(rootContainer):
    print "...updating..."
    txId = rootContainer.txId
    table = rootContainer.getComponent("Power Table")
    
    dropDown= rootContainer.getComponent("Dropdown")
    postId = dropDown.selectedValue
    
    #update display table
    SQL = "SELECT * FROM LtDisplayTable "\
        " WHERE PostId = %i "\
        " ORDER BY DisplayPage, DisplayOrder " % (postId)
    print SQL
    pds = system.db.runQuery(SQL, tx=txId)
    table.updateInProgress = True
    table.data = pds
    updateValues(rootContainer)
    table.updateInProgress = False

def updateValues(rootContainer):
    txId = rootContainer.txId
    valueTable = rootContainer.getComponent("ValueTable")
    
    #update value table
    displayTableId = rootContainer.displayTableId
    sql = "SELECT ValueName, Description, DisplayTableId "\
        "FROM LtValue "\
        "WHERE DisplayTableId = %i " % (displayTableId)
    print sql
    pds = system.db.runQuery(sql, tx=txId)
    valueTable.data = pds
   
#update the database when user directly changes table 
def updateDatabase(table, rowIndex, colName, newValue):
    rootContainer = table.parent
    txId = rootContainer.txId
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
    system.db.runUpdateQuery(SQL, tx=txId)
    
#remove the selected row
def removeRow(event):
    rootContainer = event.source.parent
    txId = rootContainer.txId
    table = rootContainer.getComponent("Power Table")
    ds = table.data
    
    row = table.selectedRow
    displayTableId = ds.getValueAt(row, "DisplayTableId")
    
    #check for references
    sql = "SELECT count(*) FROM LtValue WHERE DisplayTableId = %i" %(displayTableId)
    rows = system.db.runScalarQuery(sql, tx=txId)

    if rows > 0:
        ans = system.gui.confirm("This table is in use. Do you want to remove this table?", "Confirm")
        if ans == False:
            return
        else:
            sql = "update LtValue SET DisplayTableId = NULL WHERE DisplayTableId = %i" %(displayTableId)
            system.db.runUpdateQuery(sql, tx=txId)

    #remove the selected row
    SQL = "DELETE FROM LtDisplayTable "\
        " WHERE DisplayTableId = %i "\
        % (displayTableId)
    system.db.runUpdateQuery(SQL, tx=txId)
    
    #refresh table
    print "Calling update() from removeRow()..."
    update(rootContainer)
    
#add a row
def insertRow(event):
    rootContainer = event.source.parent
    txId = rootContainer.txId
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
        system.db.runUpdateQuery(SQL, tx=txId)
        
        #refresh table
        print "Calling update() from insertRow()..."
        update(rootContainer)

def addValueRowCallback(event):
    rootContainer = event.source.parent
    txId = rootContainer.txId
    displayTableId = rootContainer.displayTableId
    postId = rootContainer.getComponent("Dropdown").selectedValue
    
    SQL = "select ValueName "\
        " from LtValue V, TkUnit U "\
        " where V.UnitId = U.UnitId "\
        " and U.PostId = %s "\
        " and (V.DisplayTableId is null or V.DisplayTableId <> %s) "\
        " order by ValueName" % (str(postId), str(displayTableId))

    # For display table purposes, I think engineers want to be able to configure lab data on a screen regardless
    # of what unit it is assigned to.
    SQL = "select ValueName "\
        " from LtValue V "\
        " where V.DisplayTableId is null or V.DisplayTableId <> %s "\
        " order by ValueName" % (str(displayTableId))

    print SQL
    pds = system.db.runQuery(SQL, tx=txId)
    print "Selected %i lab values" % (len(pds))
    
    payload = {"txId": txId, "displayTableId": displayTableId, "postId": postId, "data":pds}
    window = system.nav.openWindow("Lab Data/New Lab Data Display Table Row", payload)
    system.nav.centerWindow(window)
    
# 
# When we "add" or "delete" from the bottom table we are not inserting or deleting rows, instead we are updating the reference 
# in the LtValue table 
#

#add a row of values
def insertValueRow(event):
    rootContainer = event.source.parent
    txId = rootContainer.txId
    
    displayTableId = rootContainer.displayTableId
    newName = rootContainer.getComponent("Dropdown").selectedStringValue
    
    #insert the user's data as a new row
    SQL = "UPDATE LtValue SET DisplayTableId = %i "\
        "WHERE ValueName = '%s' " %(displayTableId, newName)
    print SQL
    system.db.runUpdateQuery(SQL, tx=txId)
    
#remove the selected row
def removeValueRow(event):
    rootContainer = event.source.parent
    txId = rootContainer.txId
    valueTable = rootContainer.getComponent("ValueTable")
    row = valueTable.selectedRow
    ds = valueTable.data
    valueName = ds.getValueAt(row, "ValueName")
        
    #remove the selected row
    SQL = "UPDATE LtValue "\
        " SET DisplayTableId = NULL "\
        "WHERE ValueName = '%s' " % (valueName)
    system.db.runUpdateQuery(SQL, tx=txId)
    
    #refresh table
    print "Calling update() from removeValueRow()..."
    update(rootContainer)
    