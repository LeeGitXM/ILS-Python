'''
Created on Jun 15, 2015

@author: Pete
'''
import system, string
from ils.common.config import getTagProviderClient
from ils.common.constants import CR
from ils.labData.synchronize import createLabValue, deleteLabValue, createLabLimit, deleteLabLimit, createDcsTag, deleteDcsLabValue
log = system.util.getLogger("com.ils.labData.ui.configuration")


def internalFrameOpened(rootContainer):
    log.infof("In %s.internalFrameOpened(), reserving a cursor...", __name__)
    
    unitDropdown = rootContainer.getComponent("UnitName")
    unitDropdown.selectedValue = -1
    unitDropdown.selectedStringValue = "<Select One>"
    
    # Reset the tab that is selected
    rootContainer.getComponent("Tab Strip").selectedTab = "PHD"
    
    # Configure the static datasets that drive some combo boxes
    SQL = "select InterfaceName from LtHDAInterface order by InterfaceName"
    pds = system.db.runQuery(SQL)
    rootContainer.hdaInterfaceDataset = pds
    
    SQL = "select InterfaceName from LtOPCInterface order by InterfaceName"
    pds = system.db.runQuery(SQL)
    rootContainer.opcInterfaceDataset = pds


#refresh when window is activated
def internalFrameActivated(rootContainer):
    log.infof("In %s.internaFrameActived()...", __name__)
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
    log.infof("In %s.internalFrameClosing()", __name__)
            
#remove the selected row
def removeDataRow(event):
    log.infof("In %s.removeDataRow()", __name__)
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
            
            ''' Delete the DCS lab value OPC tag, if it exists '''
            deleteDcsLabValue(unitName, valueName)
        else:
            table = rootContainer.getComponent("Local").getComponent("Local_Value")
            sql = "DELETE FROM LtLocalValue WHERE ValueId = '%s' " % (valueId)

        system.db.runUpdateQuery(sql)

        ''' Delete the UDT, if it exists '''
        deleteLabValue(unitName, valueName)
            
        ''' LtHistory clean up '''
        SQL = "DELETE FROM LtHistory WHERE ValueId = '%s' " % (valueId)
        system.db.runUpdateQuery(SQL)
        
        ''' LtValueViewed clean up'''
        SQL = "DELETE FROM LtValueViewed WHERE ValueId = '%s' " % (valueId)
        system.db.runUpdateQuery(SQL)
        
        ''' LtDisplayTableDetails clean up'''
        SQL = "DELETE FROM LtDisplayTableDetails WHERE ValueId = '%s' " % (valueId)
        system.db.runUpdateQuery(SQL)
        
        ''' Clean up the limits, first from the database, then the UDTs '''
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
    log.infof("In %s.insertDataRow", __name__)
    labDataType = rootContainer.labDataType
            
    newName = rootContainer.getComponent("name").text
    if newName == "":
        system.gui.messageBox("You must specify a name for the lab value!", "Warning")
        return False
    
    description = rootContainer.getComponent("description").text
    decimals = rootContainer.getComponent("decimals").intValue
    unitId = rootContainer.unitId
    unitName = rootContainer.unitName
    if unitId == -1 or unitName == "":
        system.gui.messageBox("You must select a unit for the lab value!", "Warning")
        return False

    validationProcedure = rootContainer.getComponent("validationProcedure").text

    '''
    Do some validation of everything before we insert anything.
    '''
    
    if labDataType == "PHD":
        interfaceId = rootContainer.getComponent("opcServerDropdown").selectedValue
        interfaceName = rootContainer.getComponent("opcServerDropdown").selectedStringValue
        if interfaceId == -1 or interfaceName == "":
            system.gui.messageBox("You must select an OPC HDA Server!", "Warning")
            return False
    
        itemId = rootContainer.getComponent("itemId").text
        if itemId == "":
            system.gui.messageBox("You must specify an Item-Id for the lab value!", "Warning")
            return False
        
    elif labDataType == "DCS":
        interfaceId = rootContainer.getComponent("opcServerDropdown").selectedValue
        interfaceName = rootContainer.getComponent("opcServerDropdown").selectedStringValue
        if interfaceId == -1 or interfaceName == "":
            system.gui.messageBox("You must select an OPC Server!", "Warning")
            return False
        
        minimumTimeBetweenSamples = rootContainer.getComponent("minimumTimeBetweenSamples").intValue
        itemId = rootContainer.getComponent("itemId").text
        if itemId == "":
            system.gui.messageBox("You must specify an Item-Id for the lab value!", "Warning")
            return False
    
    elif labDataType == "Local":
        '''
        For local lab data, the PHD interface and item-id are optional if we don't want to write the local value to PHD.
        But if they specify one or the other then they need both
        '''
        interfaceId = rootContainer.getComponent("hdaInterfaceDropdown").selectedValue
        interfaceName = rootContainer.getComponent("hdaInterfaceDropdown").selectedStringValue
        itemId = rootContainer.getComponent("itemId").text
        if interfaceId <> -1 or interfaceName <> "" or itemId <> "":
            if interfaceId == -1 or interfaceName == "":
                system.gui.messageBox("You must select an HDA Server!", "Warning")
                return False
            
            if itemId == "":
                system.gui.messageBox("You must specify an Item-Id for the lab value!", "Warning")
                return False
    
    '''
    Now we are ready to insert into the database and create the tags.
    Insert the base record and then the matching PHD, DCS, or local record
    '''
    if validationProcedure == "":
        SQL = "INSERT INTO LtValue (ValueName, Description, UnitId, DisplayDecimals)"\
            "VALUES ('%s', '%s', %i, %i)" %(newName, description, unitId, decimals)
    else:   
        SQL = "INSERT INTO LtValue (ValueName, Description, UnitId, DisplayDecimals, ValidationProcedure)"\
            "VALUES ('%s', '%s', %i, %i, '%s')" %(newName, description, unitId, decimals, validationProcedure)
    print SQL
    valueId = system.db.runUpdateQuery(SQL, getKey=True)
    
    if labDataType == "PHD":
        sql = "INSERT INTO LtPHDValue (ValueId, ItemId, InterfaceId)"\
            "VALUES (%s, '%s', %s)" %(str(valueId), str(itemId), str(interfaceId))
        system.db.runUpdateQuery(sql)
        
    elif labDataType == "DCS":
        sql = "INSERT INTO LtDCSValue (ValueId, InterfaceId, ItemId, MinimumSampleIntervalSeconds)"\
            "VALUES (%s, %s, '%s', %s)" %(str(valueId), str(interfaceId), str(itemId), str(minimumTimeBetweenSamples))
        system.db.runUpdateQuery(sql)
        createDcsTag(unitName, newName, interfaceName, itemId)
        
    elif labDataType == "Local":
        interfaceId = rootContainer.getComponent("hdaInterfaceDropdown").selectedValue
        itemId = rootContainer.getComponent("itemId").text
        
        if interfaceId == -1 or itemId == "": 
            sql = "INSERT INTO LtLocalValue (ValueId)"\
                "VALUES (%s)" %(str(valueId))    
        else:
            sql = "INSERT INTO LtLocalValue (ValueId, InterfaceId, ItemId)"\
                "VALUES (%s, %s, '%s')" %(str(valueId), str(interfaceId), str(itemId))

        system.db.runUpdateQuery(sql)
    else:
        print "Unexpected lab data type: ", labDataType
        return False
    
    # Create the UDT
    createLabValue(unitName, newName)
    return True
    

def update(rootContainer):
    '''
    This is called on startup when they open the window.
    It is also called 
    '''
    log.infof("In %s.update()", __name__)
    unitId = rootContainer.getComponent("UnitName").selectedValue
    dataType = rootContainer.dataType
    log.tracef("...updating %s...", dataType)
    
    if dataType == "PHD":
        SQL = "SELECT V.ValueId, V.ValueName, V.Description, V.DisplayDecimals, V.UnitId, PV.AllowManualEntry, I.InterfaceName, PV.ItemId, V.ValidationProcedure "\
            "FROM LtValue V, LtPHDValue PV,  LtHDAInterface I "\
            "WHERE V.ValueId = PV.ValueId "\
            "AND PV.InterfaceID = I.InterfaceId "\
            "AND V.UnitId = %i "\
            "ORDER BY ValueName" % (unitId)
        log.tracef(SQL)
        pds = system.db.runQuery(SQL)
        table = rootContainer.getComponent("PHD").getComponent("PHD_Value")
        table.updateInProgress = True
        table.data = pds
        table.updateInProgress = False
    elif dataType == "DCS":
        SQL = "SELECT V.ValueId, V.ValueName, V.Description, V.DisplayDecimals, DS.MinimumSampleIntervalSeconds, V.UnitId, DS.AllowManualEntry, OPC.InterfaceName, DS.ItemId, V.ValidationProcedure "\
            " FROM LtValue V, LtDCSValue DS, LtOpcInterface OPC "\
            " WHERE V.ValueId = DS.ValueId "\
            " AND V.UnitId = %i "\
            " and OPC.InterfaceId = DS.InterfaceId "\
            " ORDER BY ValueName" % (unitId)
        log.tracef(SQL)
        pds = system.db.runQuery(SQL)
        ds = system.dataset.toDataSet(pds)
        
        ''' At one point I was going to add a status column to indicate if the lab value was OK, but didn't work out '''
        #status = ["ok"] * ds.getRowCount()
        #ds = system.dataset.addColumn(ds, 0, status, "Status", str)
        
        table = rootContainer.getComponent("DCS").getComponent("DCS_Value")
        table.updateInProgress = True
        table.data = ds
        table.updateInProgress = False
    elif dataType == "Local":
        SQL = "SELECT V.ValueId, V.ValueName, V.Description, V.DisplayDecimals, V.UnitId, HDA.InterfaceName, LV.ItemId, V.ValidationProcedure "\
            " FROM LtValue V INNER JOIN LtLocalValue LV ON V.ValueId = LV.ValueId LEFT OUTER JOIN "\
            " LtHDAInterface HDA ON LV.InterfaceId = HDA.InterfaceId "\
            " WHERE V.UnitId = %i "\
            " ORDER BY ValueName" %(unitId)
        log.tracef(SQL)
        pds = system.db.runQuery(SQL)
        table = rootContainer.getComponent("Local").getComponent("Local_Value")
        table.updateInProgress = True
        table.data = pds
        table.updateInProgress = False
    else:
        print "Unexpected tab: %s" % (rootContainer.dataType)
        

def validate(rootContainer):
    '''
    This is called on when the user presses the validate button. 
    It is sort of open when "vallidate" means.  For starters, I want to validate the table vs the tags
    Since we are coming at this from the databases point of view, validate tags for now.
    '''
    
    def validateTags(unitName, valueName, dataType, tagProvider, txt):
        ''' Now check the lab value tag '''
        
        log.tracef("    ...validating lab data UDT: %s", valueName)
        path = "LabData/%s" % (unitName)
        parentPath = "[%s]%s" % (tagProvider, path)  
        tagPath = parentPath + "/" + valueName
        tagExists = system.tag.exists(tagPath)
        if tagExists:
            log.tracef("      ... Lab value UDT exists")
        else:
            log.infof("      --- Creating lab value UDT ---")
            createLabValue(unitName, valueName)
            txt = "%s%sCreated lab value UDT for %s" % (txt, CR, valueName)
            
        return txt


    def validateDcsTag(unitName, valueName, interfaceName, itemId, tagProvider, txt):
        log.tracef("   ...validating DCS lab data: %s - %s - %s", valueName, interfaceName, itemId)
        
        path = "LabData/%s/DCS-Lab-Values" % (unitName)
        parentPath = "[%s]%s" % (tagProvider, path)  
        tagPath = parentPath + "/" + valueName
        tagExists = system.tag.exists(tagPath)
        if tagExists:
            log.tracef("      ... OPC tag exists")
        else:
            log.infof("      --- Creating OPC Tag ---")
            createDcsTag(unitName, valueName, interfaceName, itemId)
            txt = "%s%sCreated OPC tag for %s - %s" % (txt, CR, valueName, itemId)
        return txt
            
    def validateLimits(unitName, valueName, dataType, tagProvider, txt):
        ''' 
        Now check the lab limits - This makes sure that all of the required limit UDTs exist.  
        It doesn't clean up extra UDTs.
        It also write values to the UDTs, eventually the lab data handling will update them, but maybe we should do that here - IDK?
        '''
        log.tracef("    ...validating lab limits for: %s", valueName)
        
        parentPath=tagProvider+'LabData/'+unitName
        
        SQL = "select ValueId, ValueName, LimitType "\
            " from LtLimitView "\
            " where UnitName = '%s' and ValueName = '%s' order by ValueName" % (unitName, valueName)
        pds = system.db.runQuery(SQL)
        
        for record in pds:
            limitType = record["LimitType"]    
            if string.upper(limitType) == 'SQC':
                udtType='Lab Data/Lab Limit SQC'
                suffix='-SQC'
            elif string.upper(limitType) == 'RELEASE':
                udtType='Lab Data/Lab Limit Release'
                suffix='-RELEASE'
            elif string.upper(limitType) == 'VALIDITY':
                udtType='Lab Data/Lab Limit Validity'
                suffix='-VALIDITY'

            path = "LabData/%s" % (unitName)
            parentPath = "[%s]%s" % (tagProvider, path)  
            tagPath = parentPath + "/" + valueName + suffix
            log.tracef("      ...checking %s", tagPath)
            tagExists = system.tag.exists(tagPath)
            if tagExists:
                log.tracef("         ... Lab limit UDT exists")
            else:
                log.infof("         --- Creating lab limit UDT ---")
                system.tag.addTag(parentPath=parentPath, name=valueName + suffix, tagType="UDT_INST", 
                      attributes={"UDTParentType":udtType})
                txt = "%s%sCreated Lab Limit UDT for %s - %s" % (txt, CR, valueName + suffix, udtType)
                
        return txt
    #--------------------------------------------------------------------------------------
        
    log.infof("In %s.validate()", __name__)
    tagProvider = getTagProviderClient()
    unitName = rootContainer.getComponent("UnitName").selectedStringValue
    dataType = rootContainer.dataType
    log.infof("...validating %s...", dataType)
    txt = ""
    
    if dataType == "PHD":
        table = rootContainer.getComponent("PHD").getComponent("PHD_Value")
        ds = table.data
        for row in range(ds.getRowCount()):
            valueName = ds. getValueAt(row, "ValueName")
            txt = validateTags(unitName, valueName, dataType, tagProvider, txt)
            txt = validateLimits(unitName, valueName, dataType, tagProvider, txt)

        if txt == "":
            txt = "PHD Lab data configuration validated, no problems were detected!"
        else:
            txt = "Validating PHD Lab data...%s%s" % (CR, txt)
        
    elif dataType == "DCS":
        table = rootContainer.getComponent("DCS").getComponent("DCS_Value")
        ds = table.data
        
        for row in range(ds.getRowCount()):
            valueName = ds. getValueAt(row, "ValueName")
            interfaceName = ds.getValueAt(row, "InterfaceName")
            itemId =  ds.getValueAt(row, "ItemId")
            txt = validateTags(unitName, valueName, dataType, tagProvider, txt)
            txt = validateDcsTag(unitName, valueName, interfaceName, itemId, tagProvider, txt)
            txt = validateLimits(unitName, valueName, dataType, tagProvider, txt)
        
        if txt == "":
            txt = "DCS Lab data configuration validated, no problems were detected!"
        else:
            txt = "Validating DCS Lab data...%s%s" % (CR, txt)
                        
    elif dataType == "Local":
        table = rootContainer.getComponent("Local").getComponent("Local_Value")
        ds = table.data
        for row in range(ds.getRowCount()):
            valueName = ds. getValueAt(row, "ValueName")
            txt = validateTags(unitName, valueName, dataType, tagProvider, txt)
            txt = validateLimits(unitName, valueName, dataType, tagProvider, txt)
        
        if txt == "":
            txt = "Local Lab data configuration validated, no problems were detected!"
        else:
            txt = "Validating Local Lab data...%s%s" % (CR, txt)
        
    else:
        txt = "Unexpected lab data type: %s" % (rootContainer.dataType)
        print "Unexpected tab: %s" % (rootContainer.dataType)
        
    system.gui.messageBox(txt)

# Refresh the limit table    
def updateLimit(rootContainer):
    log.infof("In %s.updateLimit()...", __name__)
    selectedValueId = rootContainer.selectedValueId
    sql = "SELECT LimitId, ValueId, LimitType, LimitSource, "\
        " UpperReleaseLimit, LowerReleaseLimit, "\
        " UpperValidityLimit, LowerValidityLimit, "\
        " UpperSQCLimit, LowerSQCLimit, Target, StandardDeviation, "\
        " RecipeParameterName, InterfaceName, OPCUpperItemId, OPCLowerItemId"\
        " FROM LtLimitView "\
        " WHERE ValueId = %i " % (selectedValueId)
    pds = system.db.runQuery(sql)
    
    limitTable = rootContainer.getComponent("Lab Limit Table")
    limitTable.data = pds
    
#update the database when user directly changes table 
def dataCellEdited(table, rowIndex, colName, newValue):
    log.infof("In %s.dataCellEdited() - A cell has been edited so update the database...", __name__)
    print "Row: %s, Column: %s, Value: %s" % (str(rowIndex), colName, str(newValue))
    rootContainer = table.parent.parent

    ds = table.data
    valueId =  ds.getValueAt(rowIndex, "ValueId")
    dataType = rootContainer.dataType
    SQL = ""
    
    if colName == "ValueName":
        SQL = "UPDATE LtValue SET ValueName = '%s' WHERE ValueId = %i " % (newValue, valueId)
    elif colName == "Description":
        SQL = "UPDATE LtValue SET Description = '%s' WHERE ValueId = %i " % (newValue, valueId)
    elif colName == "DisplayDecimals":
        SQL = "UPDATE LtValue SET DisplayDecimals = %i WHERE ValueId = %i " % (newValue, valueId)
    elif colName == "ItemId":
        if dataType == "PHD":
            SQL = "UPDATE LtPHDValue SET ItemId = '%s' WHERE ValueId = %i " % (newValue, valueId)
        elif dataType == "DCS":
            SQL = "UPDATE LtDCSValue SET ItemId = '%s' WHERE ValueId = %i " % (newValue, valueId)
        elif dataType == "Local":
            SQL = "UPDATE LtLocalValue SET ItemId = '%s' WHERE ValueId = %i " % (newValue, valueId)
    elif colName == "InterfaceName":
        SQL = "select InterfaceId from LtOPCInterface where InterfaceName = '%s'" % (newValue)
        interfaceId = system.db.runScalarQuery(SQL)
        if dataType == "PHD":
            print "Error: InterfaceName is not a valid column for a PHD lab value!"
        elif dataType == "DCS":
            SQL = "UPDATE LtDCSValue SET InterfaceId = %i WHERE ValueId = %i " % (interfaceId, valueId)

    elif colName == "ValidationProcedure":
        if newValue == "":
            SQL = "UPDATE LtValue SET ValidationProcedure = NULL WHERE ValueId = %i " % (valueId)
        else:
            SQL = "UPDATE LtValue SET ValidationProcedure = '%s' WHERE ValueId = %i " % (newValue, valueId)
    
    elif colName == "MinimumSampleIntervalSeconds":
        SQL = "UPDATE LtDCSValue SET MinimumSampleIntervalSeconds = %d WHERE ValueId = %d " % (newValue, valueId)
        
    elif colName == "AllowManualEntry":
        if dataType == "PHD":
            SQL = "UPDATE LtPHDValue SET AllowManualEntry = %d WHERE ValueId = %d " % (newValue, valueId)
        elif dataType == "DCS":
            SQL = "UPDATE LtDCSValue SET AllowManualEntry = %d WHERE ValueId = %d " % (newValue, valueId)
        else:
            print "Unknown data type for AllowedManualEntry"
    
    else:
        print "Unsupported column name: ", colName
            
    if SQL != "":
        print SQL
        system.db.runUpdateQuery(SQL)

'''
Add a row to the limit table - the window here is one of the popups, not the big configuration window
'''
def insertLimitRow(event):
    log.infof("In %s.insertLimitRow()...", __name__)
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
    log.infof("In %s.removeLimitRow()...", __name__)
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
    log.infof("In %s.saveLimitRow()...", __name__)
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