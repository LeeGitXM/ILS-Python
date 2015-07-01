'''
Created on Jun 15, 2015

@author: Pete
'''
import system

#open transaction when window is opened
def internalFrameOpened(rootContainer):
    txID = system.db.beginTransaction(timeout=600000)
    rootContainer.txID = txID
    
#refresh when window is activated
def internalFrameActivated(rootContainer):
    rootContainer.selectedValueId = 0
    txID = rootContainer.txID
    update(rootContainer)
            
#remove the selected row
def removeDataRow(event):
    rootContainer = event.source.parent
    txID = rootContainer.txID
    tab = rootContainer.getComponent("Tab Strip").selectedTab
        
    #get valueId of the data to be deleted
    valueId = rootContainer.selectedValueId
        
    #check for references
    sql = "SELECT count(*) FROM LtDerivedValue WHERE ValueId = %i" %(valueId)
    rows = system.db.runScalarQuery(sql, tx=txID)
    
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
            system.db.runUpdateQuery(SQL, tx=txID)
    else:          
        #remove the selected row from either PHD, DCS, or Local
        if tab == "PHD":
            sql = "DELETE FROM LtPHDValue "\
                " WHERE ValueId = '%s' "\
                %(valueId)
            system.db.runUpdateQuery(sql, tx=txID)
        elif tab == "DCS":
            sql = "DELETE FROM LtDCSValue "\
                " WHERE ValueId = '%s' "\
                %(valueId)
            system.db.runUpdateQuery(sql, tx=txID)
        else:
            sql = "DELETE FROM LtLocalValue "\
                " WHERE ValueId = '%s' "\
                %(valueId)
            system.db.runUpdateQuery(sql, tx=txID)
            
        #delete from LtHistory
        SQL = "DELETE FROM LtHistory "\
            " WHERE ValueId = '%s' "\
            % (valueId)
        system.db.runUpdateQuery(SQL, tx=txID)
        
        #delete from LtLimit
        sql = "DELETE FROM LtLimit "\
                " WHERE ValueId = '%s' "\
                %(valueId)
        system.db.runUpdateQuery(sql, tx=txID)
        
        #delete from LtValue
        sql = "DELETE FROM LtValue "\
                " WHERE ValueId = '%s' "\
                %(valueId)
        system.db.runUpdateQuery(sql, tx=txID)
        
#add a row to the data table
def insertDataRow(event):
    rootContainer = event.source.parent
    txID = rootContainer.txID
    labDataType = rootContainer.labDataType
            
    newName = rootContainer.getComponent("name").text
    description = rootContainer.getComponent("description").text
    decimals = rootContainer.getComponent("Spinner").intValue
    itemId = rootContainer.getComponent("itemId").text
    unitId = rootContainer.unitId
        
    #insert the user's data as a new row
    SQL = "INSERT INTO LtValue (ValueName, Description, UnitId, DisplayDecimals)"\
        "VALUES ('%s', '%s', %i, %i)" %(newName, description, unitId, decimals)
    valueId = system.db.runUpdateQuery(SQL, tx=txID, getKey = True)
    
    if labDataType == "PHD":
        interfaceId = rootContainer.getComponent("Dropdown").selectedValue
        
        sql = "INSERT INTO LtPHDValue (ValueId, ItemId, InterfaceId)"\
            "VALUES (%s, %s, %s)" %(str(valueId), str(itemId), str(interfaceId))
        print sql
        system.db.runUpdateQuery(sql, tx = txID)
    elif labDataType == "DCS":
        writeLocationId = rootContainer.getComponent("Dropdown").selectedStringValue
        sql = "INSERT INTO LtDCSValue (ValueId, WriteLocationId, ItemId)"\
            "VALUES (%s, %s, %s)" %(str(valueId), str(writeLocationId), str(itemId))
        system.db.runUpdateQuery(sql, tx = txID)
    else:
        writeLocationId = rootContainer.getComponent("Dropdown").selectedStringValue
        sql = "INSERT INTO LtLocalValue (ValueId, WriteLocationId, ItemId)"\
            "VALUES (%s, %s, %s)" %(str(valueId), str(writeLocationId), str(itemId))
        system.db.runUpdateQuery(sql, tx = txID)
    
#add a row to the limit table for the selected row of data
def insertLimitRow(event):
    rootContainer = event.source.parent
    txID = rootContainer.txID
    table = rootContainer.getComponent("Power Table")
                
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
    table = rootContainer.getComponent("Lab Limit Table")
    ds = table.data
                
    row = table.selectedRow
    limitId = ds.getValueAt(row, "LimitId")
    print limitId
                        
    #remove the selected row
    SQL = "DELETE FROM LtLimit "\
        " WHERE LimitId = %i "\
        % (limitId)
    system.db.runUpdateQuery(SQL, tx=txID)
    
#update the window
def update(rootContainer):
    txID = rootContainer.txID
    unitId = rootContainer.getComponent("UnitName").selectedValue
    
    if rootContainer.dataType == "PHD":
        SQL = "SELECT V.ValueId, V.ValueName, V.Description, V.DisplayDecimals, V.UnitId, PV.ItemId, I.InterfaceName "\
            "FROM LtValue V, LtPHDValue PV,  LtHDAInterface I "\
            "WHERE V.ValueId = PV.ValueId "\
            "AND PV.InterfaceID = I.InterfaceId "\
            "AND V.UnitId = %i "\
            "ORDER BY ValueName" % (unitId)
        pds = system.db.runQuery(SQL, tx=txID)
        table = rootContainer.getComponent("PHD").getComponent("PHD_Value")
        table.data = pds
    elif rootContainer.dataType == "DCS":
        SQL = "SELECT V.ValueId, V.ValueName, V.Description, V.DisplayDecimals, V.UnitId, DS.ItemId "\
            "FROM LtValue V, LtDCSValue DS "\
            "WHERE V.ValueId = DS.ValueId "\
            "AND V.UnitId = %i "\
            "ORDER BY ValueName" % (unitId)
        pds = system.db.runQuery(SQL, tx=txID)
        table = rootContainer.getComponent("DCS").getComponent("DCS_Value")
        table.data = pds
    else:
        SQL = "SELECT V.ValueId, V.ValueName, V.Description, V.DisplayDecimals, V.UnitId, L.ItemId "\
            "FROM LtValue V, LtLocalValue L "\
            "WHERE V.ValueId = L.ValueId "\
            "AND V.UnitId = %i "\
            "ORDER BY ValueName" % (unitId)
        pds = system.db.runQuery(SQL, tx=txID)
        table = rootContainer.getComponent("Local").getComponent("Local_Value")
        table.data = pds
    
def updateLimit(rootContainer):
    txID = rootContainer.txID
    selectedValueId = rootContainer.selectedValueId
    if selectedValueId > -1:
        sql = "SELECT LimitId, ValueId, LimitTypeId, LU1.LookupName LimitType, UpperValidityLimit, "\
            " LowerValidityLimit, UpperSQCLimit, LowerSQCLimit, Target, StandardDeviation, UpperReleaseLimit, "\
            " LowerReleaseLimit, LimitSourceId, LU2.LookupName LimitSource "\
            " FROM LtLimit L, Lookup LU1, Lookup LU2 "\
            " WHERE ValueId = %i "\
            " and L.LimitTypeId = LU1.LookupId "\
            " and L.LimitSourceId = LU2.LookupId " % (selectedValueId)
        pds = system.db.runQuery(sql, tx=txID)
    
        limitTable = rootContainer.getComponent("Lab Limit Table")
        limitTable.data = pds
    
   
        
    
        