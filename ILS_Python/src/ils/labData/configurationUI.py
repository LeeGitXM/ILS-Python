'''
Created on Jun 15, 2015

@author: Pete
'''
import system, string
from formatter import NullFormatter

#open transaction when window is opened
def internalFrameOpened(rootContainer):
    print "In internalFrameOpened(), reserving a cursor..."
    txId = system.db.beginTransaction(timeout=3600000)
    rootContainer.txId = txId
    
    # Reset the tab that is selected
    rootContainer.getComponent("Tab Strip").selectedTab = "PHD"
    
    # Configure the static datasets that drive some combo boxes
    SQL = "select InterfaceName from LtHDAInterface order by InterfaceId"
    pds = system.db.runQuery(SQL)
    rootContainer.hdaInterfaceDataset = pds
    
    SQL = "select ServerName from TkWriteLocation order by ServerName"
    pds = system.db.runQuery(SQL)
    rootContainer.opcInterfaceDataset = pds


#refresh when window is activated
def internalFrameActivated(rootContainer):
    print "In internaFrameActived()..."
    rootContainer.selectedValueId = 0
    
    # Update the datasets used by the combo boxes in the power tables
    SQL = "Select LookupName LimitType from Lookup where LookupTypeCode = 'RtLimitType' order by LookupName"
    pds = system.db.runQuery(SQL)
    print "Fetched %i SQC Limit Type values..." % (len(pds))
    rootContainer.getComponent("Lab Limit Table").limitTypeDataset = pds
    
    SQL = "Select LookupName LimitType from Lookup where LookupTypeCode = 'RtLimitSource' order by LookupName"
    pds = system.db.runQuery(SQL)
    print "Fetched %i SQC Limit Source values..." % (len(pds))
    rootContainer.getComponent("Lab Limit Table").limitSourceDataset = pds
    
    print "Calling update() from internalFrameActivated()"
    update(rootContainer)
    
    print "Calling updateLimit() from internalFrameActivated()"
    updateLimit(rootContainer)

def commitChanges(rootContainer):
    txId=rootContainer.txId
    system.db.commitTransaction(txId)
    
    provider = "[XOM]"
    unitName = rootContainer.getComponent("UnitName").selectedStringValue
    #from ils.labData.synchronize import synchronize
    #synchronize(provider, unitName, txId)

  
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
        
    #check for derived lab data references
    sql = "SELECT count(*) FROM LtDerivedValue WHERE TriggerValueId = %i" %(valueId)
    triggerRows = system.db.runScalarQuery(sql, tx=txId)
    sql = "SELECT count(*) FROM LtRelatedData WHERE RelatedValueId = %i" %(valueId)
    relatedRows = system.db.runScalarQuery(sql, tx=txId)
    
    
    # If there is derived lab data based on this lab data, then inform the operator and make sure they want to delete  the
    # derived data along with this data
    if triggerRows > 0 or relatedRows > 0:
        ans = system.gui.confirm("This value has derived values. Do you want to remove this data and all of its derived data?", "Confirm")
        #don't delete anything
        if ans == False:
            return
        #delete everything... not finished as of 6/30
        else:
            print "Deleting lab data that is derived from this lab datum..."
            SQL = "select V.ValueName, V.ValueId "\
                "from LtValue V, LtDerivedValue DV "\
                " where V.ValueId = DV.ValueId "\
                " and TriggerValueId = %s" % (str(valueId))
            print SQL
            pds = system.db.runQuery(SQL, tx=txId)
            
            for record in pds:
                derivedValueId=record["ValueId"]
                SQL = "delete from LtRelatedData where DerivedValueId in "\
                    "(select DerivedValueId from LtDerivedValue where ValueId = %s)" % (str(derivedValueId))
                print SQL
                rows = system.db.runUpdateQuery(SQL, tx=txId)
                print "Deleted %i rows from LtRelatedData" % (rows)
                
                SQL = "DELETE FROM LtDerivedValue WHERE ValueId = %s " % (str(derivedValueId))
                print SQL
                rows = system.db.runUpdateQuery(SQL, tx=txId)
                print "Deleted %i rows from LtDerivedValue" % (rows)
                                
                SQL = "DELETE FROM LtValue WHERE ValueId = %s " % (str(derivedValueId))
                print SQL
                rows = system.db.runUpdateQuery(SQL, tx=txId)
                print "Deleted %i rows from LtValue" % (rows)
                
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
    validationProcedure = rootContainer.getComponent("validationProcedure").text
    
    #insert the user's data as a new row
    if validationProcedure == "":
        SQL = "INSERT INTO LtValue (ValueName, Description, UnitId, DisplayDecimals)"\
            "VALUES ('%s', '%s', %i, %i)" %(newName, description, unitId, decimals)
    else:   
        SQL = "INSERT INTO LtValue (ValueName, Description, UnitId, DisplayDecimals, ValidationProcedure)"\
            "VALUES ('%s', '%s', %i, %i, '%s')" %(newName, description, unitId, decimals, validationProcedure)
    print SQL
    valueId = system.db.runUpdateQuery(SQL, tx=txId, getKey = True)
    
    if labDataType == "PHD":
        interfaceId = rootContainer.getComponent("Dropdown").selectedValue
        itemId = rootContainer.getComponent("itemId").text
        sql = "INSERT INTO LtPHDValue (ValueId, ItemId, InterfaceId)"\
            "VALUES (%s, '%s', %s)" %(str(valueId), str(itemId), str(interfaceId))
        print sql
        system.db.runUpdateQuery(sql, tx = txId)
    elif labDataType == "DCS":
        writeLocationId = rootContainer.getComponent("Dropdown").selectedValue
        itemId = rootContainer.getComponent("itemId").text
        sql = "INSERT INTO LtDCSValue (ValueId, WriteLocationId, ItemId)"\
            "VALUES (%s, %s, '%s')" %(str(valueId), str(writeLocationId), str(itemId))
        system.db.runUpdateQuery(sql, tx = txId)
    elif labDataType == "Local":
        writeLocationId = rootContainer.getComponent("Dropdown").selectedValue
        itemId = rootContainer.getComponent("itemId").text
        
        if writeLocationId == -1 or itemId == "": 
            sql = "INSERT INTO LtLocalValue (ValueId)"\
                "VALUES (%s)" %(str(valueId))    
        else:
            sql = "INSERT INTO LtLocalValue (ValueId, WriteLocationId, ItemId)"\
                "VALUES (%s, %s, '%s')" %(str(valueId), str(writeLocationId), str(itemId))
        print sql
        system.db.runUpdateQuery(sql, tx = txId)

    
# Refresh the main table
def update(rootContainer):
    txId = rootContainer.txId
    unitId = rootContainer.getComponent("UnitName").selectedValue
    
    if rootContainer.dataType == "PHD":
        SQL = "SELECT V.ValueId, V.ValueName, V.Description, V.DisplayDecimals, V.UnitId, I.InterfaceName, PV.ItemId, V.ValidationProcedure "\
            "FROM LtValue V, LtPHDValue PV,  LtHDAInterface I "\
            "WHERE V.ValueId = PV.ValueId "\
            "AND PV.InterfaceID = I.InterfaceId "\
            "AND V.UnitId = %i "\
            "ORDER BY ValueName" % (unitId)
        print SQL
        pds = system.db.runQuery(SQL, tx=txId)
        table = rootContainer.getComponent("PHD").getComponent("PHD_Value")
        table.updateInProgress = True
        table.data = pds
        table.updateInProgress = False
    elif rootContainer.dataType == "DCS":
        SQL = "SELECT V.ValueId, V.ValueName, V.Description, V.DisplayDecimals, V.UnitId, WL.ServerName, DS.ItemId, V.ValidationProcedure "\
            " FROM LtValue V, LtDCSValue DS, TkWriteLocation WL "\
            " WHERE V.ValueId = DS.ValueId "\
            " AND V.UnitId = %i "\
            " and WL.WriteLocationId = DS.WriteLocationId "\
            " ORDER BY ValueName" % (unitId)
        print SQL
        pds = system.db.runQuery(SQL, tx=txId)
        table = rootContainer.getComponent("DCS").getComponent("DCS_Value")
        table.updateInProgress = True
        table.data = pds
        table.updateInProgress = False
    elif rootContainer.dataType == "Local":
        #SQL = "SELECT V.ValueId, V.ValueName, V.Description, V.DisplayDecimals, V.UnitId, WL.ServerName, LV.ItemId, V.ValidationProcedure "\
        #    " FROM LtValue V, LtLocalValue LV, TkWriteLocation WL "\
        #    " WHERE V.ValueId = LV.ValueId "\
        #    " AND V.UnitId = %i "\
        #    " AND WL.WriteLocationId = LV.WriteLocationId "\
        #    " ORDER BY ValueName" % (unitId)
        SQL = "SELECT V.ValueId, V.ValueName, V.Description, V.DisplayDecimals, V.UnitId, WL.ServerName, LV.ItemId, V.ValidationProcedure "\
            " FROM LtValue V INNER JOIN LtLocalValue LV ON V.ValueId = LV.ValueId LEFT OUTER JOIN "\
            " TkWriteLocation WL ON LV.WriteLocationId = WL.WriteLocationId "\
            " WHERE V.UnitId = %i "\
            " ORDER BY ValueName" %(unitId)
        print SQL
        pds = system.db.runQuery(SQL, tx=txId)
        table = rootContainer.getComponent("Local").getComponent("Local_Value")
        table.updateInProgress = True
        table.data = pds
        table.updateInProgress = False
    else:
        print "Unexpected tab: %s" % (rootContainer.dataType)

# Refresh the limit table    
def updateLimit(rootContainer):
    txId = rootContainer.txId
    selectedValueId = rootContainer.selectedValueId
    sql = "SELECT LimitId, ValueId, LimitType, LimitSource, "\
        " UpperReleaseLimit, LowerReleaseLimit, "\
        " UpperValidityLimit, LowerValidityLimit, "\
        " UpperSQCLimit, LowerSQCLimit, Target, StandardDeviation, "\
        " RecipeParameterName, WriteLocation, OPCUpperItemId, OPCLowerItemId"\
        " FROM LtLimitView "\
        " WHERE ValueId = %i " % (selectedValueId)
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
    elif colName == "ValidationProcedure":
        if newValue == "":
            SQL = "UPDATE LtValue SET ValidationProcedure = NULL "\
                "WHERE ValueId = %i " % (valueId)
        else:
            SQL = "UPDATE LtValue SET ValidationProcedure = '%s' "\
                "WHERE ValueId = %i " % (newValue, valueId)
            
    print SQL
    system.db.runUpdateQuery(SQL, tx=txId)

# Add a row to the limit table
def insertLimitRow(event):
    rootContainer = event.source.parent
    txId = rootContainer.txId
    valueId = rootContainer.selectedValueId

    from ils.common.database import lookup
    limitType = "SQC"    
    limitTypeId = lookup("RtLimitType", limitType)
    limitSource = "Recipe"
    limitSourceId = lookup("RtLimitSource", limitSource)
    
    # Insert a mostly empty row into the database, the reason to do this is to get a legit limitId into the database so now as they
    # edit each cell we can just do real simple updates...
    SQL = "Insert into LtLimit (ValueId, LimitTypeId, LimitSourceId) "\
        "values (%s, %s, %s)" % (str(valueId), str(limitTypeId), str(limitSourceId))
    limitId = system.db.runUpdateQuery(SQL, tx=txId, getKey=1)
    
    #insert blank row into the table
    limitTable = rootContainer.getComponent("Lab Limit Table")
    ds = limitTable.data
    newRow = [limitId, valueId, limitType, limitSource, None, None, None, None, None, None, None, None, None, None, None, None]
    ds = system.dataset.addRow(ds, 0, newRow)
    limitTable.data = ds


# Delete the selected row in the limit table
def removeLimitRow(event):
    rootContainer = event.source.parent
    txId = rootContainer.txId
    table = rootContainer.getComponent("Lab Limit Table")
    ds = table.data
                
    row = table.selectedRow
    limitId = ds.getValueAt(row, "LimitId")
    print "Deleting limit id %i ..." % (limitId)
                        
    # Remove the selected row
    SQL = "DELETE FROM LtLimit WHERE LimitId = %i " % (limitId)
    rows=system.db.runUpdateQuery(SQL, tx=txId)
    print "   ...deleted %i limits" % rows
        
   
def saveLimitRow(table, row, colName, oldValue, newValue):
    #--------------------------------------------------
    def updateRow(table, row, colName, limitId, newValue, txId):
        from ils.common.database import lookup
        if colName == "LimitType":
            colName = "LimitTypeId"
            print "Translating: ", newValue
            newValue = lookup("RtLimitType", newValue)
            print "  ... to ", newValue 
        elif colName == "LimitSource":
            colName = "LimitSourceId"
            print "Translating: ", newValue
            newValue = lookup("RtLimitSource", newValue) 
            print " ... to ", newValue
        
        SQL = "UPDATE LtLimit set %s = ? where LimitId = ?" % (colName)
        print SQL, newValue, limitId
        rows = system.db.runPrepUpdate(SQL, [newValue, limitId], tx=txId)
        print "Updated %i rows" % (rows)
    #--------------------------------------------------

    print "Saving the limit row..."
    rootContainer = table.parent
    txId = rootContainer.txId
    ds = table.data
    limitId = ds.getValueAt(row,"LimitId")
    
    if limitId == -1:
        system.gui.errorBox("Error updating the limit! The limit Id is -1 which indicates that the row was not successfully inserted when you pressed '+'")
    else:
        updateRow(table, row, colName, limitId, newValue, txId)
