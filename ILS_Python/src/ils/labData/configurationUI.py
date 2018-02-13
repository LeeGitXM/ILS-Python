'''
Created on Jun 15, 2015

@author: Pete
'''
import system, string
from ils.common.config import getTagProviderClient
from ils.labData.synchronize import createLabValue, deleteLabValue, createLabLimit, deleteLabLimit


def internalFrameOpened(rootContainer):
    print "In internalFrameOpened(), reserving a cursor..."
    
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


def internalFrameClosing(rootContainer):
    print "In %s.internalFrameClosing()" % (__name__)
            
#remove the selected row
def removeDataRow(event):
    table = event.source
    rootContainer = event.source.parent.parent.parent
    tab = rootContainer.getComponent("Tab Strip").selectedTab
    unitName = rootContainer.getComponent("UnitName").selectedStringValue
    
    #get valueId of the data to be deleted
    valueId = rootContainer.selectedValueId
    valueName = rootContainer.selectedValueName
        
    #check for derived lab data references
    sql = "SELECT count(*) FROM LtDerivedValue WHERE TriggerValueId = %i" %(valueId)
    triggerRows = system.db.runScalarQuery(sql)
    sql = "SELECT count(*) FROM LtRelatedData WHERE RelatedValueId = %i" %(valueId)
    relatedRows = system.db.runScalarQuery(sql)
    
    
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
            pds = system.db.runQuery(SQL)

            for record in pds:
                derivedValueId=record["ValueId"]
                SQL = "delete from LtRelatedData where DerivedValueId in "\
                    "(select DerivedValueId from LtDerivedValue where ValueId = %s)" % (str(derivedValueId))
                print SQL
                rows = system.db.runUpdateQuery(SQL)
                print "Deleted %i rows from LtRelatedData" % (rows)
                
                SQL = "DELETE FROM LtDerivedValue WHERE ValueId = %s " % (str(derivedValueId))
                print SQL
                rows = system.db.runUpdateQuery(SQL)
                print "Deleted %i rows from LtDerivedValue" % (rows)
                                
                SQL = "DELETE FROM LtValue WHERE ValueId = %s " % (str(derivedValueId))
                print SQL
                rows = system.db.runUpdateQuery(SQL)
                print "Deleted %i rows from LtValue" % (rows)
                
    else:          
        #remove the selected row from either PHD, DCS, or Local
        if tab == "PHD":
            table = rootContainer.getComponent("PHD").getComponent("PHD_Value")
            sql = "DELETE FROM LtPHDValue WHERE ValueId = '%s' " % (valueId)
        elif tab == "DCS":
            table = rootContainer.getComponent("DCS").getComponent("DCS_Value")
            sql = "DELETE FROM LtDCSValue WHERE ValueId = '%s' " % (valueId)
        else:
            table = rootContainer.getComponent("Local").getComponent("Local_Value")
            sql = "DELETE FROM LtLocalValue WHERE ValueId = '%s' " % (valueId)

        system.db.runUpdateQuery(sql)

        # Delete the UDT, if it exists
        deleteLabValue(unitName, valueName)
            
        #delete from LtHistory
        SQL = "DELETE FROM LtHistory "\
            " WHERE ValueId = '%s' "\
            % (valueId)
        system.db.runUpdateQuery(SQL)
        
        '''
        Clean up the limits, first from the database, then the UDTs
        '''
        limitTable = rootContainer.getComponent("Lab Limit Table")
        ds = limitTable.data
        pds = system.dataset.toPyDataSet(ds)
        
        sql = "DELETE FROM LtLimit WHERE ValueId = '%s' " % (valueId)
        system.db.runUpdateQuery(sql)
        
        '''
        delete the limit UDTs using the info from the table
        '''
        for record in pds:
            limitType = record["LimitType"]
            deleteLabLimit(unitName, valueName, limitType)
        
        #delete from LtValue
        sql = "DELETE FROM LtValue "\
                " WHERE ValueId = '%s' "\
                %(valueId)
        system.db.runUpdateQuery(sql)
    
        table.selectedRow = -1
    
#add a row to the data table
def insertDataRow(rootContainer):
    print "In %s.insertDataRow" % (__name__)
    labDataType = rootContainer.labDataType
            
    newName = rootContainer.getComponent("name").text
    description = rootContainer.getComponent("description").text
    decimals = rootContainer.getComponent("decimals").intValue
    unitId = rootContainer.unitId
    unitName = rootContainer.unitName
    validationProcedure = rootContainer.getComponent("validationProcedure").text
    
    #insert the user's data as a new row
    if validationProcedure == "":
        SQL = "INSERT INTO LtValue (ValueName, Description, UnitId, DisplayDecimals)"\
            "VALUES ('%s', '%s', %i, %i)" %(newName, description, unitId, decimals)
    else:   
        SQL = "INSERT INTO LtValue (ValueName, Description, UnitId, DisplayDecimals, ValidationProcedure)"\
            "VALUES ('%s', '%s', %i, %i, '%s')" %(newName, description, unitId, decimals, validationProcedure)
    print SQL
    valueId = system.db.runUpdateQuery(SQL, getKey=True)
    
    if labDataType == "PHD":
        interfaceId = rootContainer.getComponent("opcServerDropdown").selectedValue
        itemId = rootContainer.getComponent("itemId").text
        sql = "INSERT INTO LtPHDValue (ValueId, ItemId, InterfaceId)"\
            "VALUES (%s, '%s', %s)" %(str(valueId), str(itemId), str(interfaceId))
        print sql
        system.db.runUpdateQuery(sql)
    elif labDataType == "DCS":
        writeLocationId = rootContainer.getComponent("opcServerDropdown").selectedValue
        minimumTimeBetweenSamples = rootContainer.getComponent("minimumTimeBetweenSamples").intValue
        itemId = rootContainer.getComponent("itemId").text
        sql = "INSERT INTO LtDCSValue (ValueId, WriteLocationId, ItemId, MinimumSampleIntervalSeconds)"\
            "VALUES (%s, %s, '%s', %s)" %(str(valueId), str(writeLocationId), str(itemId), str(minimumTimeBetweenSamples))
        system.db.runUpdateQuery(sql)
    elif labDataType == "Local":
        writeLocationId = rootContainer.getComponent("opcServerDropdown").selectedValue
        itemId = rootContainer.getComponent("itemId").text
        
        if writeLocationId == -1 or itemId == "": 
            sql = "INSERT INTO LtLocalValue (ValueId)"\
                "VALUES (%s)" %(str(valueId))    
        else:
            sql = "INSERT INTO LtLocalValue (ValueId, WriteLocationId, ItemId)"\
                "VALUES (%s, %s, '%s')" %(str(valueId), str(writeLocationId), str(itemId))
        print sql
        system.db.runUpdateQuery(sql)
    else:
        print "Unexpected lab data type: ", labDataType
        return
    
    # Create the UDT
    createLabValue(unitName, newName)
    
# Refresh the main table
def update(rootContainer):
    unitId = rootContainer.getComponent("UnitName").selectedValue
    
    if rootContainer.dataType == "PHD":
        SQL = "SELECT V.ValueId, V.ValueName, V.Description, V.DisplayDecimals, V.UnitId, I.InterfaceName, PV.ItemId, V.ValidationProcedure "\
            "FROM LtValue V, LtPHDValue PV,  LtHDAInterface I "\
            "WHERE V.ValueId = PV.ValueId "\
            "AND PV.InterfaceID = I.InterfaceId "\
            "AND V.UnitId = %i "\
            "ORDER BY ValueName" % (unitId)
        print SQL
        pds = system.db.runQuery(SQL)
        table = rootContainer.getComponent("PHD").getComponent("PHD_Value")
        table.updateInProgress = True
        table.data = pds
        table.updateInProgress = False
    elif rootContainer.dataType == "DCS":
        SQL = "SELECT V.ValueId, V.ValueName, V.Description, V.DisplayDecimals, DS.MinimumSampleIntervalSeconds, V.UnitId, WL.ServerName, DS.ItemId, V.ValidationProcedure "\
            " FROM LtValue V, LtDCSValue DS, TkWriteLocation WL "\
            " WHERE V.ValueId = DS.ValueId "\
            " AND V.UnitId = %i "\
            " and WL.WriteLocationId = DS.WriteLocationId "\
            " ORDER BY ValueName" % (unitId)
        print SQL
        pds = system.db.runQuery(SQL)
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
        pds = system.db.runQuery(SQL)
        table = rootContainer.getComponent("Local").getComponent("Local_Value")
        table.updateInProgress = True
        table.data = pds
        table.updateInProgress = False
    else:
        print "Unexpected tab: %s" % (rootContainer.dataType)

# Refresh the limit table    
def updateLimit(rootContainer):
    selectedValueId = rootContainer.selectedValueId
    sql = "SELECT LimitId, ValueId, LimitType, LimitSource, "\
        " UpperReleaseLimit, LowerReleaseLimit, "\
        " UpperValidityLimit, LowerValidityLimit, "\
        " UpperSQCLimit, LowerSQCLimit, Target, StandardDeviation, "\
        " RecipeParameterName, WriteLocation, OPCUpperItemId, OPCLowerItemId"\
        " FROM LtLimitView "\
        " WHERE ValueId = %i " % (selectedValueId)
    pds = system.db.runQuery(sql)
    
    limitTable = rootContainer.getComponent("Lab Limit Table")
    limitTable.data = pds
    
#update the database when user directly changes table 
def dataCellEdited(table, rowIndex, colName, newValue):
    print "A cell has been edited so update the database..."
    rootContainer = table.parent.parent

    ds = table.data
    valueId =  ds.getValueAt(rowIndex, "ValueId")
    dataType = rootContainer.dataType
    SQL = ""
    
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
    
    elif colName == "MinimumSampleIntervalSeconds":
        SQL = "UPDATE LtDCSValue SET MinimumSampleIntervalSeconds = %d WHERE ValueId = %d " % (newValue, valueId)
    
    else:
        print "Unsupported column name: ", colName
            
    if SQL != "":
        print SQL
        system.db.runUpdateQuery(SQL)

'''
Add a row to the limit table - the window here is one of the popups, not the big configuration window
'''
def insertLimitRow(event):
    rootContainer = event.source.parent.parent.parent
    unitName = rootContainer.getComponent("UnitName").selectedStringValue
    valueId = rootContainer.selectedValueId
    valueName = rootContainer.selectedValueName

    from ils.common.database import lookup
    limitType = "SQC"    
    limitTypeId = lookup("RtLimitType", limitType)
    limitSource = "Recipe"
    limitSourceId = lookup("RtLimitSource", limitSource)
    
    # Insert a mostly empty row into the database, the reason to do this is to get a legit limitId into the database so now as they
    # edit each cell we can just do real simple updates...
    SQL = "Insert into LtLimit (ValueId, LimitTypeId, LimitSourceId) "\
        "values (%s, %s, %s)" % (str(valueId), str(limitTypeId), str(limitSourceId))
    limitId = system.db.runUpdateQuery(SQL, getKey=1)
    
    # Create the UDT
    createLabLimit(unitName, valueName, limitType)
    
    #insert blank row into the table
    limitTable = rootContainer.getComponent("Lab Limit Table")
    ds = limitTable.data
    newRow = [limitId, valueId, limitType, limitSource, None, None, None, None, None, None, None, None, None, None, None, None]
    ds = system.dataset.addRow(ds, 0, newRow)
    limitTable.data = ds


# Delete the selected row in the limit table
def removeLimitRow(event):
    rootContainer = event.source.parent.parent.parent
    
    unitName = rootContainer.getComponent("UnitName").selectedStringValue
    valueName = rootContainer.selectedValueName
    
    table = rootContainer.getComponent("Lab Limit Table")
    ds = table.data
                
    row = table.selectedRow
    limitType = ds.getValueAt(row,"LimitType")
    limitId = ds.getValueAt(row, "LimitId")
    print "Deleting limit id %i ..." % (limitId)
                        
    # Remove the selected row
    SQL = "DELETE FROM LtLimit WHERE LimitId = %i " % (limitId)
    rows=system.db.runUpdateQuery(SQL)
    print "   ...deleted %i limits from database" % rows
    
    deleteLabLimit(unitName, valueName, limitType)
        

'''
Called from an onCellEdited handler on the limit table.  By the time this is called, the UDT should already exist.  If they are changing the type of the limit 
(SQC, Validity, Release) then we have to delete the old and create a new UDT
'''
def saveLimitRow(table, row, colName, oldValue, newValue):
    #--------------------------------------------------
    def updateRow(table, row, colName, limitId, newValue):
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
        rows = system.db.runPrepUpdate(SQL, [newValue, limitId])
        print "Updated %i rows" % (rows)
    #--------------------------------------------------

    print "Saving the limit row %s - from %s to %s..." % (colName, str(oldValue), str(newValue))
    rootContainer = table.parent
    unitName = rootContainer.getComponent("UnitName").selectedStringValue
    valueName = rootContainer.selectedValueName
    
    ds = table.data
    limitId = ds.getValueAt(row,"LimitId")
    limitType = string.upper(ds.getValueAt(row,"LimitType"))
    
    if limitId == -1:
        system.gui.errorBox("Error updating the limit! The limit Id is -1 which indicates that the row was not successfully inserted when you pressed '+'")
    else:
        updateRow(table, row, colName, limitId, newValue)
        
        '''
        Now update the UDT
        '''
        tagProvider = getTagProviderClient()
    
        if limitType == 'SQC':
            suffix='-SQC'
        elif limitType == 'RELEASE':
            suffix='-RELEASE'
        elif limitType == 'VALIDITY':
            suffix='-VALIDITY'

        parentPath = "[%s]LabData/%s" % (tagProvider, unitName)
        labDataName=valueName+suffix
        tagPath = parentPath + "/" + labDataName

        if colName == "LimitType":
            print "Deleting and creating..."
            deleteLabLimit(unitName, valueName, oldValue)
            createLabLimit(unitName, valueName, newValue)
        else:
            if colName == 'UpperReleaseLimit' and limitType == "RELEASE":
                tagPath = tagPath + '/upperReleaseLimit'
                system.tag.write(tagPath, newValue)
            elif colName == 'LowerReleaseLimit' and limitType == "RELEASE":
                tagPath = tagPath + '/lowerReleaseLimit'
                system.tag.write(tagPath, newValue)
                
            elif colName == 'UpperValidityLimit' and limitType in ["SQC", "VALIDITY"]:
                tagPath = tagPath + '/upperValidityLimit'
                system.tag.write(tagPath, newValue)
            elif colName == 'LowerValidityLimit' and limitType in ["SQC", "VALIDITY"]:
                tagPath = tagPath + '/lowerValidityLimit'
                system.tag.write(tagPath, newValue)
                
            elif colName == 'UpperSQCLimit' and limitType == "SQC":
                tagPath = tagPath + '/upperSQCLimit'
                system.tag.write(tagPath, newValue)
            elif colName == 'LowerSQCLimit' and limitType == "SQC":
                tagPath = tagPath + '/lowerSQCLimit'
                system.tag.write(tagPath, newValue)
            elif colName == 'Target' and limitType == "SQC":
                tagPath = tagPath + '/target'
                system.tag.write(tagPath, newValue)
            elif colName == 'StandardDeviation' and limitType == "SQC":
                tagPath = tagPath + '/standardDeviation'
                system.tag.write(tagPath, newValue)

            else:
                print "Change was to a property (%s) that does not exist in the UDT for a %s limit" % (colName, limitType)