'''
Created on Jun 15, 2015

@author: Pete
'''
import system

#open transaction when window is opened
def internalFrameOpened(rootContainer):
    txID = system.db.beginTransaction(timeout=60000)
    rootContainer.txID = txID
    rootContainer.SelectedValueId = 0
    update(rootContainer)
            
#remove the selected row
def removeDataRow(event):
    rootContainer = event.source.parent
    txID = rootContainer.txID
    tab = rootContainer.getComponent("Tab Strip").tabData
    rootContainer.SelectedValueId = 0
    if tab == "PHD":
        table = rootContainer.getComponent("PHD").getComponent("PHD_Value")
    elif tab == "DCS":
        table = rootContainer.getComponent("DCS").getComponent("DCS_Value")
    else:
        table = rootContainer.getComponent("PHD").getComponent("PHD_Value")
    ds = table.data
        
    row = table.selectedRow
    ValueName = ds.getValueAt(row, "ValueName")
        
    #check for references
    #sql = "SELECT count(*) FROM LtValue WHERE DisplayTableId = %i" %(DisplayTableId)
    #rows = system.db.runScalarQuery(sql, tx=txID)
        
    #if rows > 0:
        #ans = system.gui.confirm("This table is in use. Do you want to remove this table?", "Confirm")
        #if ans == False:
            #return
        #else:
            #sql = "update LtValue SET ValueName = NULL WHERE ValueName = '%s'" %(DisplayTableId)
            #system.db.runUpdateQuery(sql, tx=txID)
                
    #remove the selected row
    SQL = "DELETE FROM LtValue "\
        " WHERE ValueName = '%s' "\
        % (ValueName)
    system.db.runUpdateQuery(SQL, tx=txID)
        
    #refresh table
    update(rootContainer)
        
#add a row to the data table
def insertDataRow(event):
    rootContainer = event.source.parent
    txID = rootContainer.txID
    tab = rootContainer.getComponent("Tab Strip").tabData
    
    if tab == "PHD":
        table = rootContainer.getComponent("PHD").getComponent("PHD_Value")
        InterfaceName = "PHD_HDA"
    elif tab == "DCS":
        table = rootContainer.getComponent("DCS").getComponent("DCS_Value")
        InterfaceName = "null"
    else:
        table = rootContainer.getComponent("Local").getComponent("Local_Value")
        InterfaceName = "null"
    ds = table.data
            
    newName = system.gui.inputBox("Insert New Value Name:", "")
    Description = system.gui.inputBox("Insert New Description:", "")
    ItemId = system.gui.inputBox("Insert New Item ID:", "")
        
    #insert the user's data as a new row
    SQL = "INSERT INTO LtValue (ValueName, Description, ItemId, InterfaceName)"\
        "VALUES ('%s', '%s', '%s', '%s')" %(newName, Description, ItemId, InterfaceName)
    system.db.runUpdateQuery(SQL, tx=txID)
    print "Go Hawks"    
    #refresh table
    update(rootContainer)
    rootContainer.selectedValueId = 0
    
#add a row to the limit table for the selected row of data
def insertLimitRow(event):
    rootContainer = event.source.parent
    txID = rootContainer.txID
    table = rootContainer.getComponent("Power Table")
    ds = table.data
                
    newUpperValidityLimit = system.gui.inputBox("Insert New Upper Validity Limit:", "")
    newLowerValidityLimit = system.gui.inputBox("Insert New Lower Validity Limit:", "")
            
    #insert the user's data as a new row
    SQL = "INSERT INTO LtLimit (UpperValidityLimit, LowerValidityLimit)"\
        "VALUES (%i, %i)" %(newUpperValidityLimit, newLowerValidityLimit)
    system.db.runUpdateQuery(SQL, tx=txID)
                
    #refresh table
    update(rootContainer)
        
#remove the selected row in the limit table for the selected row of data
def removeLimitRow(event):
    rootContainer = event.source.parent
    txID = rootContainer.txID
    table = rootContainer.getComponent("Power Table")
    ds = table.data
                
    row = table.selectedRow
    limitId = ds.getValueAt(row, "LimitId")
                        
    #remove the selected row
    SQL = "DELETE FROM LtLimit "\
        " WHERE LimitId = %i "\
        % (limitId)
    system.db.runUpdateQuery(SQL, tx=txID)
                
    #refresh table
    update(rootContainer)
    
#update the window
def update(rootContainer):
    txID = rootContainer.txID
    tab = rootContainer.getComponent("Tab Strip").tabData
    if tab == "PHD":
        table = rootContainer.getComponent("PHD").getComponent("PHD_Value")
    elif tab == "DCS":
        table = rootContainer.getComponent("DCS").getComponent("DCS_Value")
    else:
        table = rootContainer.getComponent("Local").getComponent("Local_Value")
    SQL = "SELECT * FROM LtValue "\
        " ORDER BY ValueName "
    print SQL
    pds = system.db.runQuery(SQL, tx=txID)
    table.data = pds
        