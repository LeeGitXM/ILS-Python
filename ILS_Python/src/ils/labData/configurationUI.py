'''
Created on Jun 15, 2015

@author: Pete
'''
import system

#open transaction when window is opened
def internalFrameOpened(rootContainer):
    txId = system.db.beginTransaction(timeout=600000)
    rootContainer.txId = txId
    print "Calling updateLimit() from internalFrameOpened()"
    updateLimit(rootContainer)
    
#refresh when window is activated
def internalFrameActivated(rootContainer):
    rootContainer.selectedValueId = 0
    txId = rootContainer.txId
    print "Calling update() from internalFrameActivated()"
    update(rootContainer)
    
#close transaction when window is closed
def internalFrameClosing(rootContainer):
    try:
        txId=rootContainer.txId
        system.db.rollbackTransaction(txId)
        print "Closing the transaction..."
        system.db.closeTransaction(txId)
    except:
        print "Caught an error trying to close the transaction"
            
#remove the selected row
def removeDataRow(event):
    rootContainer = event.source.parent
    txId = rootContainer.txId
    tab = rootContainer.getComponent("Tab Strip").selectedTab
        
    #get valueId of the data to be deleted
    valueId = rootContainer.selectedValueId
        
    #check for references
    sql = "SELECT count(*) FROM LtDerivedValue WHERE ValueId = %i" %(valueId)
    rows = system.db.runScalarQuery(sql, tx=txId)
    
    #for now on 6/30 ignore the derived value case as we dont have any yet
    if rows > 0:
        ans = system.gui.confirm("This data has derived values. Do you want to remove this data and all of its derived data?", "Confirm")
        #don't delete anything
        if ans == False:
            return
        #delete everything... not finished as of 6/30
        else:
            SQL = "DELETE FROM LtDerivedValue "\
                " WHERE ValueId = '%s' "\
                %(valueId)
            system.db.runUpdateQuery(SQL, tx=txId)
    else:          
        #remove the selected row from either PHD, DCS, or Local
        if tab == "PHD":
            sql = "DELETE FROM LtPHDValue "\
                " WHERE ValueId = '%s' "\
                %(valueId)
            system.db.runUpdateQuery(sql, tx=txId)
        elif tab == "DCS":
            sql = "DELETE FROM LtDCSValue "\
                " WHERE ValueId = '%s' "\
                %(valueId)
            system.db.runUpdateQuery(sql, tx=txId)
        else:
            sql = "DELETE FROM LtLocalValue "\
                " WHERE ValueId = '%s' "\
                %(valueId)
            system.db.runUpdateQuery(sql, tx=txId)
            
        #delete from LtHistory
        SQL = "DELETE FROM LtHistory "\
            " WHERE ValueId = '%s' "\
            % (valueId)
        system.db.runUpdateQuery(SQL, tx=txId)
        
        #delete from LtLimit
        sql = "DELETE FROM LtLimit "\
                " WHERE ValueId = '%s' "\
                %(valueId)
        system.db.runUpdateQuery(sql, tx=txId)
        
        #delete from LtValue
        sql = "DELETE FROM LtValue "\
                " WHERE ValueId = '%s' "\
                %(valueId)
        system.db.runUpdateQuery(sql, tx=txId)
        
#add a row to the data table
def insertDataRow(event):
    rootContainer = event.source.parent
    txId = rootContainer.txId
    labDataType = rootContainer.labDataType
            
    newName = rootContainer.getComponent("name").text
    description = rootContainer.getComponent("description").text
    decimals = rootContainer.getComponent("Spinner").intValue
    unitId = rootContainer.unitId
    isSelector = 0
    
    if labDataType == "Selector":
        isSelector = 1
        
    #insert the user's data as a new row
    SQL = "INSERT INTO LtValue (ValueName, Description, UnitId, DisplayDecimals, IsSelector)"\
        "VALUES ('%s', '%s', %i, %i, %i)" %(newName, description, unitId, decimals, isSelector)
    print SQL
    valueId = system.db.runUpdateQuery(SQL, tx=txId, getKey = True)
    
    if labDataType == "PHD":
        interfaceId = rootContainer.getComponent("Dropdown").selectedValue
        itemId = rootContainer.getComponent("itemId").intValue
        
        sql = "INSERT INTO LtPHDValue (ValueId, ItemId, InterfaceId)"\
            "VALUES (%s, %s, %s)" %(str(valueId), str(itemId), str(interfaceId))
        print sql
        system.db.runUpdateQuery(sql, tx = txId)
    elif labDataType == "DCS":
        writeLocationId = rootContainer.getComponent("Dropdown").selectedValue
        itemId = rootContainer.getComponent("itemId").intValue
        sql = "INSERT INTO LtDCSValue (ValueId, WriteLocationId, ItemId)"\
            "VALUES (%s, %s, %s)" %(str(valueId), str(writeLocationId), str(itemId))
        system.db.runUpdateQuery(sql, tx = txId)
    elif labDataType == "Local":
        writeLocationId = rootContainer.getComponent("Dropdown").selectedStringValue
        itemId = rootContainer.getComponent("itemId").intValue
        sql = "INSERT INTO LtLocalValue (ValueId, WriteLocationId, ItemId)"\
            "VALUES (%s, %s, %s)" %(str(valueId), str(writeLocationId), str(itemId))
        system.db.runUpdateQuery(sql, tx = txId)
    
#add a row to the limit table for the selected row of data
def insertLimitRow(event):
    rootContainer = event.source.parent
    valueId = rootContainer.selectedValueId
    limitTable = rootContainer.getComponent("Lab Limit Table")
    ds = limitTable.data
    
    #insert blank row
    newRow = [-1, valueId, -1, "", None, None, None, None, None, None, None, None, None, ""]
    ds = system.dataset.addRow(ds, 0, newRow)
    limitTable.data = ds
    
        
#remove the selected row in the limit table for the selected row of data
def removeLimitRow(event):
    rootContainer = event.source.parent
    txId = rootContainer.txId
    table = rootContainer.getComponent("Lab Limit Table")
    ds = table.data
                
    row = table.selectedRow
    limitId = ds.getValueAt(row, "LimitId")
    print limitId
                        
    #remove the selected row
    SQL = "DELETE FROM LtLimit "\
        " WHERE LimitId = %i "\
        % (limitId)
    system.db.runUpdateQuery(SQL, tx=txId)
    
#update the window
def update(rootContainer):
    txId = rootContainer.txId
    unitId = rootContainer.getComponent("UnitName").selectedValue
    
    if rootContainer.dataType == "PHD":
        SQL = "SELECT V.ValueId, V.ValueName, V.Description, V.DisplayDecimals, V.UnitId, PV.ItemId, I.InterfaceName "\
            "FROM LtValue V, LtPHDValue PV,  LtHDAInterface I "\
            "WHERE V.ValueId = PV.ValueId "\
            "AND PV.InterfaceID = I.InterfaceId "\
            "AND V.UnitId = %i "\
            "ORDER BY ValueName" % (unitId)
        pds = system.db.runQuery(SQL, tx=txId)
        table = rootContainer.getComponent("PHD").getComponent("PHD_Value")
        table.updateInProgress = True
        table.data = pds
        table.updateInProgress = False
    elif rootContainer.dataType == "DCS":
        SQL = "SELECT V.ValueId, V.ValueName, V.Description, V.DisplayDecimals, V.UnitId, DS.ItemId "\
            "FROM LtValue V, LtDCSValue DS "\
            "WHERE V.ValueId = DS.ValueId "\
            "AND V.UnitId = %i "\
            "ORDER BY ValueName" % (unitId)
        pds = system.db.runQuery(SQL, tx=txId)
        table = rootContainer.getComponent("DCS").getComponent("DCS_Value")
        table.updateInProgress = True
        table.data = pds
        table.updateInProgress = False
    elif rootContainer.dataType == "Selector":
        SQL = "SELECT ValueId, ValueName, Description, DisplayDecimals, UnitId "\
            "FROM LtValue "\
            "WHERE UnitId = %i "\
            "AND IsSelector = 1 "\
            "ORDER BY ValueName" % (unitId)
        pds = system.db.runQuery(SQL, tx=txId)
        table = rootContainer.getComponent("Selector").getComponent("Selector_Value")
        table.updateInProgress = True
        table.data = pds
        table.updateInProgress = False
    else:
        SQL = "SELECT V.ValueId, V.ValueName, V.Description, V.DisplayDecimals, V.UnitId, L.ItemId "\
            "FROM LtValue V, LtLocalValue L "\
            "WHERE V.ValueId = L.ValueId "\
            "AND V.UnitId = %i "\
            "ORDER BY ValueName" % (unitId)
        pds = system.db.runQuery(SQL, tx=txId)
        table = rootContainer.getComponent("Local").getComponent("Local_Value")
        table.updateInProgress = True
        table.data = pds
        table.updateInProgress = False
    
def updateLimit(rootContainer):
    txId = rootContainer.txId
    selectedValueId = rootContainer.selectedValueId
    sql = "SELECT LimitId, ValueId, LimitTypeId, LU1.LookupName LimitType, UpperValidityLimit, "\
        " LowerValidityLimit, UpperSQCLimit, LowerSQCLimit, Target, StandardDeviation, UpperReleaseLimit, "\
        " LowerReleaseLimit, LimitSourceId, LU2.LookupName LimitSource "\
        " FROM LtLimit L, Lookup LU1, Lookup LU2 "\
        " WHERE ValueId = %i "\
        " and L.LimitTypeId = LU1.LookupId "\
        " and L.LimitSourceId = LU2.LookupId " % (selectedValueId)
    pds = system.db.runQuery(sql, tx=txId)
    
    limitTable = rootContainer.getComponent("Lab Limit Table")
    limitTable.data = pds
    
#update the database when user directly changes table 
def dataCellEdited(table, rowIndex, colName, newValue):
    print "A cell has been edited so update the database..."
    rootContainer = table.parent.parent
    txId = rootContainer.txId
    ds = table.data
    valueId =  ds.getValueAt(rowIndex, "ValueId")
    dataType = rootContainer.dataType
    
    if colName == "ValueName":
        SQL = "UPDATE LtValue SET ValueName = '%s' "\
            "WHERE ValueId = %i " % (newValue, valueId)
    elif colName == "Description":
        SQL = "UPDATE LtValue SET Description = '%s' "\
            "WHERE ValueId = %i " % (newValue, valueId)
    elif colName == "DisplayDecimals":
        SQL = "UPDATE LtValue SET DisplayDecimals = %i "\
            "WHERE ValueId = %i " % (newValue, valueId)
    elif colName == "ItemId":
        if dataType == "PHD":
            SQL = "UPDATE LtPHDValue SET ItemId = %i "\
                "WHERE ValueId = %i " % (newValue, valueId)
        elif dataType == "DCS":
            SQL = "UPDATE LtDCSValue SET ItemId = %i "\
                "WHERE ValueId = %i " % (newValue, valueId)
        elif dataType == "Local":
            SQL = "UPDATE LtLocalValue SET ItemId = %i "\
                "WHERE ValueId = %i " % (newValue, valueId)     
    elif colName == "InterfaceName":
        SQL = "UPDATE LtHDAInterface SET InterfaceName = %i "\
            "WHERE LtHDAInterface.InterfaceId = LtPHDValue.InterfaceId " % (newValue)
            
    print SQL
    system.db.runUpdateQuery(SQL, tx=txId)
    
   
        
    
        