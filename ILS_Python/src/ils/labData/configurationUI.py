'''
Created on Jun 15, 2015

@author: Pete
'''
import system, string
from ils.config.client import getTagProvider, getDatabase
from ils.common.constants import CR
from ils.common.cast import toBit
from ils.io.util import readTag, writeTag
from ils.labData.limits import calcSQCLimits
from ils.labData.synchronize import createLabValue, deleteLabValue, createLabLimit, deleteLabLimit, createDcsTag, deleteDcsLabValue, updateLabValueUdt
from ils.log import getLogger
log = getLogger(__name__)

def internalFrameOpened(rootContainer):
    log.infof("In %s.internalFrameOpened(), reserving a cursor...", __name__)
    
    db = getDatabase()
    unitDropdown = rootContainer.getComponent("UnitName")
    unitDropdown.selectedValue = -1
    unitDropdown.selectedStringValue = "<Select One>"
    
    rootContainer.selectedValueId = 0
    rootContainer.selectedValueName = ""
    
    # Reset the tab that is selected
    rootContainer.getComponent("Tab Strip").selectedTab = "PHD"
    
    # Configure the static datasets that drive some combo boxes
    SQL = "select InterfaceName from LtHDAInterface order by InterfaceName"
    pds = system.db.runQuery(SQL, database=db)
    rootContainer.hdaInterfaceDataset = pds
    
    SQL = "select InterfaceId, InterfaceName from LtOPCInterface order by InterfaceName"
    pds = system.db.runQuery(SQL, database=db)
    rootContainer.opcInterfaceDataset = pds
    
    # Update the datasets used by the combo boxes in the power tables
    SQL = "Select LookupName LimitType from Lookup where LookupTypeCode = 'RtLimitType' order by LookupName"
    pds = system.db.runQuery(SQL, database=db)
    log.tracef("Fetched %d SQC Limit Type values...", len(pds))
    rootContainer.getComponent("Lab Limit Table").limitTypeDataset = pds
    
    SQL = "Select LookupName LimitType from Lookup where LookupTypeCode = 'RtLimitSource' order by LookupName"
    pds = system.db.runQuery(SQL, database=db)
    log.tracef("Fetched %d SQC Limit Source values...", len(pds))
    rootContainer.getComponent("Lab Limit Table").limitSourceDataset = pds


#refresh when window is activated
def internalFrameActivated(rootContainer):
    log.infof("In %s.internaFrameActived()...", __name__)
    db = getDatabase()
    
    log.tracef("Calling update() from internalFrameActivated()")
    update(rootContainer, db)
    
    log.tracef("Calling updateLimit() from internalFrameActivated()")
    updateLimit(rootContainer, db)


def internalFrameClosing(rootContainer):
    log.infof("In %s.internalFrameClosing()", __name__)

def removeDataRow(event):
    ''' Delete the selected row and the associated UDTs '''
    log.infof("In %s.removeDataRow()", __name__)
    table = event.source
    rootContainer = event.source.parent.parent.parent
    tab = rootContainer.getComponent("Tab Strip").selectedTab
    unitName = rootContainer.getComponent("UnitName").selectedStringValue
    db = getDatabase()
    
    #get valueId of the data to be deleted
    valueId = rootContainer.selectedValueId
    valueName = rootContainer.selectedValueName
        
    #check for derived lab data references
    sql = "SELECT count(*) FROM LtDerivedValue WHERE TriggerValueId = %i" %(valueId)
    triggerRows = system.db.runScalarQuery(sql, database=db)
    sql = "SELECT count(*) FROM LtRelatedData WHERE RelatedValueId = %i" %(valueId)
    relatedRows = system.db.runScalarQuery(sql, database=db)
    
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
            pds = system.db.runQuery(SQL, database=db)

            for record in pds:
                derivedValueId=record["ValueId"]
                SQL = "delete from LtRelatedData where DerivedValueId in "\
                    "(select DerivedValueId from LtDerivedValue where ValueId = %s)" % (str(derivedValueId))
                print SQL
                rows = system.db.runUpdateQuery(SQL, database=db)
                print "Deleted %i rows from LtRelatedData" % (rows)
                
                SQL = "DELETE FROM LtDerivedValue WHERE ValueId = %s " % (str(derivedValueId))
                print SQL
                rows = system.db.runUpdateQuery(SQL, database=db)
                print "Deleted %i rows from LtDerivedValue" % (rows)
                                
                SQL = "DELETE FROM LtValue WHERE ValueId = %s " % (str(derivedValueId))
                print SQL
                rows = system.db.runUpdateQuery(SQL, database=db)
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

        system.db.runUpdateQuery(sql, database=db)

        ''' Delete the UDT, if it exists '''
        deleteLabValue(unitName, valueName)
            
        ''' LtHistory clean up '''
        SQL = "DELETE FROM LtHistory WHERE ValueId = '%s' " % (valueId)
        system.db.runUpdateQuery(SQL, database=db)
        
        ''' LtValueViewed clean up'''
        SQL = "DELETE FROM LtValueViewed WHERE ValueId = '%s' " % (valueId)
        system.db.runUpdateQuery(SQL, database=db)
        
        ''' LtDisplayTableDetails clean up'''
        SQL = "DELETE FROM LtDisplayTableDetails WHERE ValueId = '%s' " % (valueId)
        system.db.runUpdateQuery(SQL, database=db)
        
        ''' Clean up the limits, first from the database, then the UDTs '''
        limitTable = rootContainer.getComponent("Lab Limit Table")
        ds = limitTable.data
        pds = system.dataset.toPyDataSet(ds)
        
        sql = "DELETE FROM LtLimit WHERE ValueId = '%s' " % (valueId)
        system.db.runUpdateQuery(sql, database=db)
        
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
        system.db.runUpdateQuery(sql, database=db)
    
        table.selectedRow = -1
    
#add a row to the data table
def insertDataRow(rootContainer):
    log.infof("In %s.insertDataRow", __name__)
    labDataType = rootContainer.labDataType
    db = getDatabase()
            
    newName = rootContainer.getComponent("name").text
    if newName == "":
        system.gui.messageBox("You must specify a name for the lab value!", "Warning")
        return False
    
    description = rootContainer.getComponent("description").text
    decimals = rootContainer.getComponent("decimals").intValue
    stringValue = rootContainer.getComponent("stringValue").selected
    stringValueBit = toBit(stringValue)
    unitId = rootContainer.unitId
    unitName = rootContainer.unitName
    if unitId == -1 or unitName == "":
        system.gui.messageBox("You must select a unit for the lab value!", "Warning")
        return False

    validationProcedure = rootContainer.getComponent("validationProcedure").text

    '''  Do some validation of everything before we insert anything. '''
    
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
        sampleTimeOffset = rootContainer.getComponent("sampleTimeOffset").intValue  
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
        SQL = "INSERT INTO LtValue (ValueName, Description, UnitId, DisplayDecimals, StringValue)"\
            "VALUES ('%s', '%s', %d, %d, %d)" %(newName, description, unitId, decimals, stringValueBit)
    else:   
        SQL = "INSERT INTO LtValue (ValueName, Description, UnitId, DisplayDecimals, StringValue, ValidationProcedure)"\
            "VALUES ('%s', '%s', %d, %d, %d, '%s')" %(newName, description, unitId, decimals, stringValueBit, validationProcedure)
    print SQL
    valueId = system.db.runUpdateQuery(SQL, getKey=True, database=db)
    
    if labDataType == "PHD":
        sql = "INSERT INTO LtPHDValue (ValueId, ItemId, InterfaceId)"\
            "VALUES (%s, '%s', %s)" %(str(valueId), str(itemId), str(interfaceId))
        system.db.runUpdateQuery(sql, database=db)
        
    elif labDataType == "DCS":
        sql = "INSERT INTO LtDCSValue (ValueId, InterfaceId, ItemId, MinimumSampleIntervalSeconds, SampleTimeConstantMinutes)"\
            "VALUES (%s, %s, '%s', %s, %s)" %(str(valueId), str(interfaceId), str(itemId), str(minimumTimeBetweenSamples), str(sampleTimeOffset))
        system.db.runUpdateQuery(sql, database=db)
        createDcsTag(unitName, newName, interfaceName, itemId, stringValue)
        
    elif labDataType == "Local":
        interfaceId = rootContainer.getComponent("hdaInterfaceDropdown").selectedValue
        itemId = rootContainer.getComponent("itemId").text
        
        if interfaceId == -1 or itemId == "": 
            sql = "INSERT INTO LtLocalValue (ValueId)"\
                "VALUES (%s)" %(str(valueId))    
        else:
            sql = "INSERT INTO LtLocalValue (ValueId, InterfaceId, ItemId)"\
                "VALUES (%s, %s, '%s')" %(str(valueId), str(interfaceId), str(itemId))

        system.db.runUpdateQuery(sql, database=db)
    else:
        print "Unexpected lab data type: ", labDataType
        return False
    
    # Create the UDT
    createLabValue(unitName, newName, stringValue)
    return True
    

def update(rootContainer, db):
    '''
    This is called on startup when they open the window.
    It is also called 
    '''
    log.infof("In %s.update()", __name__)
    unitId = rootContainer.getComponent("UnitName").selectedValue
    dataType = rootContainer.dataType
    log.tracef("...updating %s...", dataType)
    
    if dataType == "PHD":
        SQL = "SELECT V.ValueId, V.ValueName, V.Description, V.DisplayDecimals, V.StringValue, V.UnitId, PV.AllowManualEntry, I.InterfaceName, PV.ItemId, V.ValidationProcedure "\
            "FROM LtValue V, LtPHDValue PV,  LtHDAInterface I "\
            "WHERE V.ValueId = PV.ValueId "\
            "AND PV.InterfaceID = I.InterfaceId "\
            "AND V.UnitId = %i "\
            "ORDER BY ValueName" % (unitId)
        log.tracef(SQL)
        pds = system.db.runQuery(SQL, database=db)
        table = rootContainer.getComponent("PHD").getComponent("PHD_Value")
        table.updateInProgress = True
        table.data = pds
        table.updateInProgress = False
    elif dataType == "DCS":
        SQL = "SELECT V.ValueId, V.ValueName, V.Description, V.DisplayDecimals, V.StringValue, DS.MinimumSampleIntervalSeconds, DS.SampleTimeConstantMinutes, V.UnitId, DS.AllowManualEntry, "\
            " OPC.InterfaceName, DS.ItemId, V.ValidationProcedure "\
            " FROM LtValue V, LtDCSValue DS, LtOpcInterface OPC "\
            " WHERE V.ValueId = DS.ValueId "\
            " AND V.UnitId = %i "\
            " and OPC.InterfaceId = DS.InterfaceId "\
            " ORDER BY ValueName" % (unitId)
        log.tracef(SQL)
        pds = system.db.runQuery(SQL, database=db)
        ds = system.dataset.toDataSet(pds)
        
        ''' At one point I was going to add a status column to indicate if the lab value was OK, but didn't work out '''
        #status = ["ok"] * ds.getRowCount()
        #ds = system.dataset.addColumn(ds, 0, status, "Status", str)
        
        table = rootContainer.getComponent("DCS").getComponent("DCS_Value")
        table.updateInProgress = True
        table.data = ds
        table.updateInProgress = False
    elif dataType == "Local":
        SQL = "SELECT V.ValueId, V.ValueName, V.Description, V.DisplayDecimals, V.StringValue, V.UnitId, HDA.InterfaceName, LV.ItemId, V.ValidationProcedure "\
            " FROM LtValue V INNER JOIN LtLocalValue LV ON V.ValueId = LV.ValueId LEFT OUTER JOIN "\
            " LtHDAInterface HDA ON LV.InterfaceId = HDA.InterfaceId "\
            " WHERE V.UnitId = %i "\
            " ORDER BY ValueName" %(unitId)
        log.tracef(SQL)
        pds = system.db.runQuery(SQL, database=db)
        table = rootContainer.getComponent("Local").getComponent("Local_Value")
        table.updateInProgress = True
        table.data = pds
        table.updateInProgress = False
    else:
        print "Unexpected tab: %s" % (rootContainer.dataType)
        

def validate(rootContainer):
    '''
    This is called on when the user presses the validate button. 
    It is sort of open when "validate" means.  For starters, I want to validate the table vs the tags
    Since we are coming at this from the databases point of view, validate tags for now.
    '''
    
    def validateTags(unitName, valueName, dataType, stringValue, tagProvider, txt):
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
            createLabValue(unitName, valueName, stringValue)
            txt = "%s%sCreated lab value UDT for %s" % (txt, CR, valueName)
            
        return txt

    def validateDcsTag(unitName, valueName, interfaceName, itemId, tagProvider, stringValue, txt):
        log.tracef("   ...validating DCS lab data: %s - %s - %s", valueName, interfaceName, itemId)
        
        path = "LabData/%s/DCS-Lab-Values" % (unitName)
        parentPath = "[%s]%s" % (tagProvider, path)  
        tagPath = parentPath + "/" + valueName
        tagExists = system.tag.exists(tagPath)
        if tagExists:
            log.tracef("      ... OPC tag exists")
        else:
            log.infof("      --- Creating OPC Tag ---")
            createDcsTag(unitName, valueName, interfaceName, itemId, stringValue)
            txt = "%s%sCreated OPC tag for %s - %s" % (txt, CR, valueName, itemId)
        return txt
            
    def validateLimits(unitName, valueName, dataType, db, tagProvider, txt):
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
        pds = system.db.runQuery(SQL, database=db)
        
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
                tag = {
                       "name": valueName + suffix,
                       "tagType": "UdtInstance",
                       "typeId": udtType
                    }
                system.tag.configure(parentPath, tags=[tag])
                txt = "%s%sCreated Lab Limit UDT for %s - %s" % (txt, CR, valueName + suffix, udtType)
                
        return txt
    #--------------------------------------------------------------------------------------
        
    log.infof("In %s.validate()", __name__)
    db = getDatabase()
    tagProvider = getTagProvider()
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
            txt = validateLimits(unitName, valueName, dataType, db, tagProvider, txt)

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
            stringValue = ds.getValueAt(row, "StringValue")
            txt = validateTags(unitName, valueName, dataType, stringValue, tagProvider, txt)
            txt = validateDcsTag(unitName, valueName, interfaceName, itemId, tagProvider, stringValue, txt)
            txt = validateLimits(unitName, valueName, dataType, db, tagProvider, txt)
        
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
            txt = validateLimits(unitName, valueName, dataType, db, tagProvider, txt)
        
        if txt == "":
            txt = "Local Lab data configuration validated, no problems were detected!"
        else:
            txt = "Validating Local Lab data...%s%s" % (CR, txt)
        
    else:
        txt = "Unexpected lab data type: %s" % (rootContainer.dataType)
        print "Unexpected tab: %s" % (rootContainer.dataType)
        
    system.gui.messageBox(txt)

# Refresh the limit table    
def updateLimit(rootContainer, db):
    log.infof("In %s.updateLimit()...", __name__)
    selectedValueId = rootContainer.selectedValueId
    log.tracef("...using valueId: %s...", str(selectedValueId))
    sql = "SELECT LimitId, ValueId, LimitType, LimitSource, "\
        " UpperReleaseLimit, LowerReleaseLimit, "\
        " UpperValidityLimit, LowerValidityLimit, "\
        " UpperSQCLimit, LowerSQCLimit, Target, StandardDeviation, "\
        " RecipeParameterName, InterfaceName, OPCUpperItemId, OPCLowerItemId"\
        " FROM LtLimitView "\
        " WHERE ValueId = %i " % (selectedValueId)
    pds = system.db.runQuery(sql, database=db)
    log.tracef("...fetched %d rows...", len(pds))
    
    limitTable = rootContainer.getComponent("Lab Limit Table")
    limitTable.data = pds
    
''' Update the database when user directly changes the limit table ''' 
def dataCellEdited(table, rowIndex, colName, oldValue, newValue):
    log.infof("In %s.dataCellEdited() - A cell has been edited so update the database (and the tag)...", __name__)
    log.tracef("Row: %s, Column: %s, Value: %s (was %s)", str(rowIndex), colName, str(newValue), str(oldValue))
    rootContainer = table.parent.parent
    db = getDatabase()
    ds = table.data
    valueId =  ds.getValueAt(rowIndex, "ValueId")
    dataType = rootContainer.dataType
    unitName = rootContainer.getComponent("UnitName").selectedStringValue
    SQL = ""
    
    if colName == "ValueName":
        SQL = "UPDATE LtValue SET ValueName = '%s' WHERE ValueId = %i " % (newValue, valueId)
        
        ''' Rename the rootContainer property that records the selected valueName when a row is selected '''
        rootContainer.selectedValueName = newValue
        
        ''' Rename the existing Lab data UDT '''
        labValueName = oldValue
        updateLabValueUdt(unitName, dataType, labValueName, colName, newValue)
    elif colName == "Description":
        SQL = "UPDATE LtValue SET Description = '%s' WHERE ValueId = %i " % (newValue, valueId)
    elif colName == "DisplayDecimals":
        SQL = "UPDATE LtValue SET DisplayDecimals = %i WHERE ValueId = %i " % (newValue, valueId)
    elif colName == "StringValue":
        newBitValue = toBit(newValue)
        SQL = "UPDATE LtValue SET StringValue = %d WHERE ValueId = %i " % (newBitValue, valueId)
    elif colName == "ItemId":
        if dataType == "PHD":
            SQL = "UPDATE LtPHDValue SET ItemId = '%s' WHERE ValueId = %i " % (newValue, valueId)
        elif dataType == "DCS":
            SQL = "UPDATE LtDCSValue SET ItemId = '%s' WHERE ValueId = %i " % (newValue, valueId)
            labValueName = ds.getValueAt(rowIndex, "ValueName")
            updateLabValueUdt(unitName, dataType, labValueName, colName, newValue)
        elif dataType == "Local":
            SQL = "UPDATE LtLocalValue SET ItemId = '%s' WHERE ValueId = %i " % (newValue, valueId)
    elif colName == "InterfaceName":
        SQL = "select InterfaceId from LtOPCInterface where InterfaceName = '%s'" % (newValue)
        interfaceId = system.db.runScalarQuery(SQL)
        if dataType == "PHD":
            print "Error: InterfaceName is not a valid column for a PHD lab value!"
        elif dataType == "DCS":
            SQL = "UPDATE LtDCSValue SET InterfaceId = %i WHERE ValueId = %i " % (interfaceId, valueId)
            labValueName = ds.getValueAt(rowIndex, "ValueName")
            updateLabValueUdt(unitName, dataType, labValueName, colName, newValue)

    elif colName == "ValidationProcedure":
        if newValue == "":
            SQL = "UPDATE LtValue SET ValidationProcedure = NULL WHERE ValueId = %i " % (valueId)
        else:
            SQL = "UPDATE LtValue SET ValidationProcedure = '%s' WHERE ValueId = %i " % (newValue, valueId)
    
    elif colName == "MinimumSampleIntervalSeconds":
        SQL = "UPDATE LtDCSValue SET MinimumSampleIntervalSeconds = %d WHERE ValueId = %d " % (newValue, valueId)
        
    elif colName == "SampleTimeConstantMinutes":
        SQL = "UPDATE LtDCSValue SET SampleTimeConstantMinutes = %d WHERE ValueId = %d " % (newValue, valueId)

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
        log.tracef(SQL)
        system.db.runUpdateQuery(SQL, database=db)

'''
Delete the selected row in the limit table.
This is called from a button alongside the bottom limit table when a row is selected.
'''
def removeLimitRow(event):
    log.infof("In %s.removeLimitRow()...", __name__)
    db = getDatabase()
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
    rows=system.db.runUpdateQuery(SQL, database=db)
    print "   ...deleted %i limits from database" % rows
    
    # Delete the UDT
    deleteLabLimit(unitName, valueName, limitType)
        
'''
Called from an onCellEdited handler on the limit table.  By the time this is called, the UDT should already exist.  They can only change the limits and some 
of the attributes of the limit - they can't change the type or the source of of the limit becvause that would require a different UDT class. 
'''
def saveLimitRow(table, row, colName, oldValue, newValue):
    log.infof("In %s.saveLimitRow(), updating %s from %s to %s..", __name__, colName, str(oldValue), str(newValue))
    db = getDatabase()
    
    rootContainer = table.parent
    unitName = rootContainer.getComponent("UnitName").selectedStringValue
    valueName = rootContainer.selectedValueName
    
    ds = table.data
    limitId = ds.getValueAt(row,"LimitId")
    limitType = string.upper(ds.getValueAt(row,"LimitType"))
    
    if limitId == -1:
        system.gui.errorBox("Error updating the limit! The limit Id is -1 which indicates that the row was not successfully inserted when you pressed '+'")
    else:
        ''' Update the limit in the database (this updates the value in LtLimit, the permanent value may have come from the DCS or recipe) '''
        SQL = "UPDATE LtLimit set %s = ? where LimitId = ?" % (colName)
        print SQL, newValue, limitId
        rows = system.db.runPrepUpdate(SQL, [newValue, limitId], database=db)
        print "Updated %i rows" % (rows)
        
    updateLimitTag(unitName, valueName, limitType, colName, newValue)

def updateLimitTag(unitName, valueName, limitType, colName, newValue):
        '''
        Now update the UDT - This should be called when they edit a cell in the table, AND when a new limit is created.
        '''
        tagProvider = getTagProvider()
    
        if limitType == 'SQC':
            suffix='-SQC'
        elif limitType == 'RELEASE':
            suffix='-RELEASE'
        elif limitType == 'VALIDITY':
            suffix='-VALIDITY'

        parentPath = "[%s]LabData/%s" % (tagProvider, unitName)
        labDataName=valueName+suffix
        tagPath = parentPath + "/" + labDataName

        if colName == 'UpperReleaseLimit' and limitType == "RELEASE":
            tagPath = tagPath + '/upperReleaseLimit'
            writeTag(tagPath, newValue)
        elif colName == 'LowerReleaseLimit' and limitType == "RELEASE":
            tagPath = tagPath + '/lowerReleaseLimit'
            writeTag(tagPath, newValue)
            
        elif colName == 'UpperValidityLimit' and limitType in ["SQC", "VALIDITY"]:
            tagPath = tagPath + '/upperValidityLimit'
            writeTag(tagPath, newValue)
        elif colName == 'LowerValidityLimit' and limitType in ["SQC", "VALIDITY"]:
            tagPath = tagPath + '/lowerValidityLimit'
            writeTag(tagPath, newValue)
            
        elif colName == 'UpperSQCLimit' and limitType == "SQC":
            tagPath = tagPath + '/upperSQCLimit'
            writeTag(tagPath, newValue)
        elif colName == 'LowerSQCLimit' and limitType == "SQC":
            tagPath = tagPath + '/lowerSQCLimit'
            writeTag(tagPath, newValue)
        elif colName == 'Target' and limitType == "SQC":
            tagPath = tagPath + '/target'
            writeTag(tagPath, newValue)
        elif colName == 'StandardDeviation' and limitType == "SQC":
            tagPath = tagPath + '/standardDeviation'
            writeTag(tagPath, newValue)

        else:
            print "Change was to a property (%s) that does not exist in the UDT for a %s limit" % (colName, limitType)

'''---------------------------------------------------------------------
Everything below here has to do with the New Limit Popup window
---------------------------------------------------------------------
'''

def labLimitPopupInternalFrameOpened(rootContainer):
    log.infof("In %s.labLimitPopupInternalFrameOpened()...", __name__)
    rootContainer.getComponent("Limit Type Dropdown").selectedValue = -1
    rootContainer.getComponent("Limit Source Dropdown").selectedValue = -1
    
def validateLimitTypeChoice(event):
    log.infof("In %s.validateLimitTypeChoice(), validating %s...", __name__, event.newValue)
    

'''
Create a new limit - this is called from a button on the Lab Limit Popup window. 
'''
def createLimit(event):
    
    ''' You can't have two limits of the same type for the same parameter '''
    def checkIfLimitAlreadyExists(valueId, limitType, db):
        SQL = "select count(*) from LtLimitView where ValueId = %d and LimitType = '%s' " % (valueId, limitType)
        cnt = system.db.runScalarQuery(SQL, database=db)
        if cnt > 0:
            return True
        return False
    
    log.infof("In %s.createLimit()...", __name__)
    db = getDatabase()
    rootContainer = event.source.parent
    unitId = rootContainer.unitId
    unitName = rootContainer.unitName
    valueId = rootContainer.valueId
    valueName = rootContainer.valueName

    from ils.common.database import lookup
    limitType = string.upper(rootContainer.getComponent("Limit Type Dropdown").selectedStringValue)
    limitTypeId = lookup("RtLimitType", limitType)
    limitSource = rootContainer.getComponent("Limit Source Dropdown").selectedStringValue    
    limitSourceId = lookup("RtLimitSource", limitSource)
    
    if (checkIfLimitAlreadyExists(valueId, limitType, db)):
        system.gui.warningBox("A %s limit already exists for %s" % (limitType, valueName))
        return False
    
    # Insert a mostly empty row into the database, the reason to do this is to get a legit limitId into the database so now as they
    # edit each cell we can just do real simple updates...
    cols = ["ValueId", "LimitTypeId", "LimitSourceId"]
    args = [valueId, limitTypeId, limitSourceId]
    if limitType == "SQC":
        
        if limitSource == "Recipe":
            recipeKey = rootContainer.getComponent("Recipe Key Dropdown").selectedStringValue
            if recipeKey == "":
                system.gui.warningBox("Please configure the Recipe Key")
                return False
            cols.append("RecipeParameterName")
            args.append(recipeKey)
        elif limitSource == "DCS":
            opcServerId = rootContainer.getComponent("OPC Server Dropdown").selectedValue
            if opcServerId == -1:
                system.gui.warningBox("Please select an OPC Server")
                return False
            cols.append("OPCInterfaceId")
            args.append(opcServerId)
            
            upperLimitItemId = rootContainer.getComponent("Upper Limit Item Id Field").text
            if upperLimitItemId == "":
                system.gui.warningBox("Please configure the Upper Limit Item Id")
                return False
            cols.append("OPCUpperItemId")
            args.append(upperLimitItemId)
            
            lowerLimitItemId = rootContainer.getComponent("Lower Limit Item Id Field").text
            if lowerLimitItemId == "":
                system.gui.warningBox("Please configure the Lower Limit Item Id")
                return False
            cols.append("OPCLowerItemId")
            args.append(lowerLimitItemId)
            
        elif limitSource == "Constant":
            print "Adding a constant limit"
        
    elif limitType == "VALIDITY":
        if limitSource == "DCS":
            opcServerId = rootContainer.getComponent("OPC Server Dropdown").selectedValue
            if opcServerId == -1:
                system.gui.warningBox("Please select an OPC Server")
                return False
            cols.append("OPCInterfaceId")
            args.append(opcServerId)
            
            upperLimitItemId = rootContainer.getComponent("Upper Limit Item Id Field").text
            if upperLimitItemId == "":
                system.gui.warningBox("Please configure the Upper Limit Item Id")
                return False
            cols.append("OPCUpperItemId")
            args.append(upperLimitItemId)
            
            lowerLimitItemId = rootContainer.getComponent("Lower Limit Item Id Field").text
            if lowerLimitItemId == "":
                system.gui.warningBox("Please configure the Lower Limit Item Id")
                return False
            cols.append("OPCLowerItemId")
            args.append(lowerLimitItemId)
            
        elif limitSource == "Constant":
            print "Adding a constant limit"
        
        else:
            system.gui.warningBox("<HTML>Validity limits require a source of <b>DCS</b> or <b>Constant</b>.  Please make a selection from the Source dropdown.")
            return False
    
    elif limitType == "RELEASE":
        if limitSource != "Constant":
            system.gui.warningBox("<HTML>The only valid source for release limits is <b>Constant</b>.  Please select <b>Constant</b> from the Source dropdown.")
            return False

    else:
        system.gui.errorBox("Illegal limit type: %s" % (limitType))
        return False
    
    ''' Get the limits entered into the GUI '''
    upperReleaseLimit = rootContainer.getComponent("Upper Release Limit Field").floatValue
    upperValidityLimit = rootContainer.getComponent("Upper Validity Limit Field").floatValue
    upperSQCLimit = rootContainer.getComponent("Upper SQC Limit Field").floatValue
    target = rootContainer.getComponent("Target Field").floatValue
    standardDeviation = rootContainer.getComponent("Standard Deviation Field").floatValue
    lowerSQCLimit = rootContainer.getComponent("Lower SQC Limit Field").floatValue
    lowerValidityLimit = rootContainer.getComponent("Lower Validity Limit Field").floatValue 
    lowerReleaseLimit = rootContainer.getComponent("Lower Release Limit Field").floatValue
    
    if limitType in ["VALIDITY", "SQC"]:
        cols.append("UpperValidityLimit")
        args.append(upperValidityLimit)
        cols.append("LowerValidityLimit")
        args.append(lowerValidityLimit)
    
    if limitType in ["SQC"]:
        cols.append("UpperSQCLimit")
        args.append(upperSQCLimit)
        cols.append("LowerSQCLimit")
        args.append(lowerSQCLimit)
        cols.append("Target")
        args.append(target)
        cols.append("StandardDeviation")
        args.append(standardDeviation)
        
    if limitType in ["RELEASE"]:
        cols.append("UpperReleaseLimit")
        args.append(upperReleaseLimit)
        cols.append("LowerReleaseLimit")
        args.append(lowerReleaseLimit)
    
    vals = ["?"] * len(cols)
    SQL = "Insert into LtLimit (%s) values (%s)" % (",".join(cols), ",".join(vals))
    print SQL
    system.db.runPrepUpdate(SQL, args, getKey=1, database=db)
    
    ''' Create the UDT '''
    createLabLimit(unitName, valueName, limitType)
    
    ''' Now that the UDT exists, update the tags '''
    #TODO - Update the tags for other limit types
    if limitType in ["RELEASE"]:
        updateLimitTag(unitName, valueName, limitType, "UpperReleaseLimit", upperReleaseLimit)
        updateLimitTag(unitName, valueName, limitType, "LowerReleaseLimit", lowerReleaseLimit)
    elif limitType in ["VALIDITY"]:
        updateLimitTag(unitName, valueName, limitType, "UpperValidityLimit", upperValidityLimit)
        updateLimitTag(unitName, valueName, limitType, "LowerValidityLimit", lowerValidityLimit)
    elif limitType in ["SQC"]:
        updateLimitTag(unitName, valueName, limitType, "UpperSQCLimit", upperSQCLimit)
        updateLimitTag(unitName, valueName, limitType, "LowerSQCLimit", lowerSQCLimit)
        updateLimitTag(unitName, valueName, limitType, "Target", target)
        updateLimitTag(unitName, valueName, limitType, "StandardDeviation", standardDeviation)
        updateLimitTag(unitName, valueName, limitType, "UpperValidityLimit", upperValidityLimit)
        updateLimitTag(unitName, valueName, limitType, "LowerValidityLimit", lowerValidityLimit)
    
    return True


def readLimitsFromRecipe(event):
    ''' This is called from the Create Limit Popup.  It is used for SQC limits when the source is recipe. '''
    rootContainer = event.source.parent
    
    limitType = rootContainer.getComponent("Limit Type Dropdown").selectedStringValue    
    if limitType != "SQC":
        system.gui.warningBox("<HTML>SQC Limits are the only type of limits that can be loaded from the database.")
        return
    
    limitSource = rootContainer.getComponent("Limit Source Dropdown").selectedStringValue            
    if limitSource != "Recipe":
        system.gui.warningBox("<HTML>Limits can only be loaded from the database is the source is <b>RECIPE</b>")
        return

    recipeKey = rootContainer.getComponent("Recipe Key Dropdown").selectedStringValue
    if recipeKey == "":
        system.gui.warningBox("Please configure the Recipe Key")
        return
    
    unitName = rootContainer.unitName
    db = rootContainer.db
    provider = rootContainer.provider
    grade = readTag("[%s]Site/%s/Grade/grade" % (provider, unitName)).value
    
    SQL = "select UpperLimit, LowerLimit from RtSQCLimitView "\
        "where RecipeFamilyName = '%s' "\
        "and Parameter = '%s' "\
        " and Grade = '%s' " % (unitName, recipeKey, grade)
    print SQL
    pds = system.db.runQuery(SQL, database=db)
    if len(pds) == 0:
        system.gui.warningBox("No SQC limits were found in the %s database for grade %s and key %s" % (unitName, grade, recipeKey))
        return
    
    if len(pds) > 1:
        system.gui.warningBox("Multiple SQC limits were found in the %s database for grade %s and key %s, only one record was expected" % (unitName, grade, recipeKey))
        return
    
    record = pds[0]
    upperSQCLimit = record["UpperLimit"]
    lowerSQCLimit = record["LowerLimit"]
    standardDeviationsToSQCLimits = readTag("[%s]Configuration/LabData/standardDeviationsToSQCLimits" % (provider)).value
    standardDeviationsToValidityLimits = readTag("[%s]Configuration/LabData/standardDeviationsToValidityLimits" % (provider)).value
    
    target, standardDeviation, lowerValidityLimit, upperValidityLimit = calcSQCLimits(lowerSQCLimit, upperSQCLimit, standardDeviationsToSQCLimits, standardDeviationsToValidityLimits)

    rootContainer.getComponent("Upper Validity Limit Field").floatValue = upperValidityLimit
    rootContainer.getComponent("Lower Validity Limit Field").floatValue = lowerValidityLimit
    rootContainer.getComponent("Upper SQC Limit Field").floatValue = upperSQCLimit
    rootContainer.getComponent("Lower SQC Limit Field").floatValue = lowerSQCLimit
    rootContainer.getComponent("Target Field").floatValue = target
    rootContainer.getComponent("Standard Deviation Field").floatValue = standardDeviation
    
def calculateConstantLimits(event):
    ''' This is called from the Create Limit Popup.  It is used for SQC limits when the source is constant. '''
    rootContainer = event.source.parent
    provider = rootContainer.provider
    
    limitType = rootContainer.getComponent("Limit Type Dropdown").selectedStringValue    
    if limitType != "SQC":
        system.gui.warningBox("<HTML>SQC Limits are the only type of limits that can be loaded from the database.")
        return
    
    limitSource = rootContainer.getComponent("Limit Source Dropdown").selectedStringValue            
    if limitSource != "Constant":
        system.gui.warningBox("<HTML>Limits can only be calculated if the source is <b>CONSTANT</b>")
        return

    upperSQCLimit = rootContainer.getComponent("Upper SQC Limit Field").floatValue
    lowerSQCLimit = rootContainer.getComponent("Lower SQC Limit Field").floatValue
    standardDeviationsToSQCLimits = readTag("[%s]Configuration/LabData/standardDeviationsToSQCLimits" % (provider)).value
    standardDeviationsToValidityLimits = readTag("[%s]Configuration/LabData/standardDeviationsToValidityLimits" % (provider)).value
    
    target, standardDeviation, lowerValidityLimit, upperValidityLimit = calcSQCLimits(lowerSQCLimit, upperSQCLimit, standardDeviationsToSQCLimits, standardDeviationsToValidityLimits)

    rootContainer.getComponent("Upper Validity Limit Field").floatValue = upperValidityLimit
    rootContainer.getComponent("Lower Validity Limit Field").floatValue = lowerValidityLimit
    rootContainer.getComponent("Target Field").floatValue = target
    rootContainer.getComponent("Standard Deviation Field").floatValue = standardDeviation
