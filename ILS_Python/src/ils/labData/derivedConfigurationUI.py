'''
Created on Jul 1, 2015

@author: Pete
'''
import system
from ils.common.config import getTagProviderClient, getDatabaseClient
from ils.labData.configurationUI import updateLimit

#open transaction when window is opened
def internalFrameOpened(rootContainer):    
    # initialize datasets
    db = getDatabaseClient()
    SQL = "SELECT ValueId, ValueName FROM LtValue ORDER BY ValueName"
    pds = system.db.runQuery(SQL, database=db)
    rootContainer.triggerValueNameDataset = pds
    
    SQL = "SELECT ServerName FROM TkWriteLocation ORDER BY ServerName"
    pds = system.db.runQuery(SQL, database=db)
    rootContainer.serverNameDataset = pds
    
    SQL = "SELECT ValueName FROM LtValue ORDER BY ValueName"
    pds = system.db.runQuery(SQL, database=db)
    rootContainer.valueNameDataset = pds
    
    SQL = "select InterfaceName from LtHDAInterface order by InterfaceName"
    pds = system.db.runQuery(SQL, database=db)
    rootContainer.hdaInterfaceDataset = pds
    
#refresh when window is activated
def internalFrameActivated(rootContainer):
    db = getDatabaseClient()
    print "Calling update() from internalFrameActivated()..."
    update(rootContainer, db)
    print "Calling updateRelatedTable() from internalFrameActivated()..."
    updateRelatedTable(rootContainer, db)
    print "Calling updateDerivedLimitsTable() from internalFrameActivated()..."
    updateDerivedLimitsTable(rootContainer, db)

#close transaction when window is closed
def internalFrameClosing(rootContainer):
    print "In %s.internalFrameClosing()" % (__name__)


#update the window
def update(rootContainer, db):
    print "...updating display table..."
    table = rootContainer.getComponent("Power Table")
    dropDown= rootContainer.getComponent("UnitName")
    unitId = dropDown.selectedValue
    ds = table.data
    
    #update display table
    SQL = "SELECT LtValue.ValueId, LtValue.ValueName, LtValue.Description, LtValue_1.ValueName AS TriggerValueName,  "\
        " LtValue.DisplayDecimals, LtDerivedValue.DerivedValueId, LtDerivedValue.TriggerValueId, "\
        " LtDerivedValue.Callback, LtDerivedValue.SampleTimeTolerance, LtDerivedValue.NewSampleWaitTime, "\
        " LtHdaInterface.InterfaceName, LtDerivedValue.ResultItemId "\
        " FROM LtValue INNER JOIN LtDerivedValue ON LtValue.ValueId = LtDerivedValue.ValueId INNER JOIN "\
        " LtValue AS LtValue_1 ON LtDerivedValue.TriggerValueId = LtValue_1.ValueId LEFT OUTER JOIN "\
        " LtHdaInterface ON LtDerivedValue.ResultInterfaceId = LtHdaInterface.InterfaceId "\
        " WHERE LtValue.UnitId = %i ORDER BY LtValue.ValueName " % (unitId)
        
    print SQL
    pds = system.db.runQuery(SQL, database=db)
    table.updateInProgress = True
    table.data = pds
    table.updateInProgress = False
    if table.selectedRow >= 0:
        valueId = ds.getValueAt(table.selectedRow, "ValueId")
        print "ValueId on next line:"
        print valueId
        
def updateRelatedTable(rootContainer, db):
    print "...updating related table..."
    table = rootContainer.getComponent("Power Table")
    ds = table.data  
    relatedTable = rootContainer.getComponent("relatedLabDataTable")
    
    #update related table
    if table.selectedRow >= 0:
        row = table.selectedRow
        derivedValueId = ds.getValueAt(row, "DerivedValueId")
        relatedTable.derivedValueId = derivedValueId
        print "derivedValueId = ",derivedValueId
        sql = "SELECT V.ValueId, V.ValueName, V.Description "\
            " FROM LtValue V, LtRelatedData R "\
            " WHERE R.DerivedValueId = %i AND R.RelatedValueId = V.ValueId"\
            " ORDER BY V.ValueName" % (derivedValueId) 
        print sql
        pds = system.db.runQuery(sql, database=db)
        relatedTable.data = pds
    else:
        print "no selected row: clear related table"
        derivedValueId = -1
        sql = "SELECT V.ValueId, V.ValueName, V.Description "\
            " FROM LtValue V, LtRelatedData R "\
            " WHERE R.DerivedValueId = %i AND R.RelatedValueId = V.ValueId"\
            " ORDER BY V.ValueName" % (derivedValueId) 
        print sql
        pds = system.db.runQuery(sql, database=db)
        relatedTable.data = pds
        
def updateDerivedLimitsTable(rootContainer, db):
    print "...updating derived limits table..."
    updateLimit(rootContainer, db)
   
#update the database when user completes the newly added row 
def updateDatabaseXXX(rootContainer):
    print "Updating the database..."
    table = rootContainer.getComponent("Power Table")
    ds = table.data
    row = table.selectedRow
    
    name = ds.getValueAt(row, "ValueName")
    description = ds.getValueAt(row, "Description")
    decimals = ds.getValueAt(row, "DisplayDecimals")
    triggerValueName = ds.getValueAt(row, "TriggerValueName")
    callback = ds.getValueAt(row, "Callback")
    resultItemId = ds.getValueAt(row, "ResultItemId")
    sampleTimeTolerance = ds.getValueAt(row, "SampleTimeTolerance")
    newSampleWaitTime = ds.getValueAt(row, "NewSampleWaitTime")
    unitId = rootContainer.getComponent("UnitName").selectedValue
    
    print "%s - %s - %s - %s" % (name, str(decimals), triggerValueName, callback)
    if name != "" and decimals >= 0 and triggerValueName != "" and callback != "":
        triggerValueId = system.db.runScalarQuery("select valueId from LtValue where ValueName = '%s'" % (triggerValueName))
        SQL = "INSERT INTO LtValue (ValueName, Description, DisplayDecimals, UnitId) "\
            " VALUES ('%s', '%s', %i, %i)" % (name, description, decimals, unitId)
        print SQL
        valueId = system.db.runUpdateQuery(SQL, getKey=1)
        print "Inserted a new lab value with id: ", valueId
        sql = "INSERT INTO LtDerivedValue (ValueId, TriggerValueId, Callback, ResultItemId, SampleTimeTolerance, NewSampleWaitTime) "\
            " VALUES (%i, %i, '%s', '%s', %i, %i)" % (valueId, triggerValueId, callback, resultItemId, sampleTimeTolerance, newSampleWaitTime)
        print sql
        system.db.runUpdateQuery(sql)
    else:
        print "Insufficient data to update the database..."
               
#update the database when user directly changes table 
def cellEdited(table, rowIndex, colName, newValue):
    print "A cell has been edited (%s) so update the database..." % (colName)
    ds = table.data
    valueId =  ds.getValueAt(rowIndex, "ValueId")
    
    if colName == "ValueName":
        SQL = "UPDATE LtValue SET ValueName = '%s' "\
            "WHERE ValueId = %i " % (newValue, valueId)
        print SQL
        system.db.runUpdateQuery(SQL)
    elif colName == "Description":
        SQL = "UPDATE LtValue SET Description = '%s' "\
            "WHERE ValueId = %i " % (newValue, valueId)
        print SQL
        system.db.runUpdateQuery(SQL)
    elif colName == "DisplayDecimals":
        SQL = "UPDATE LtValue SET DisplayDecimals = %i "\
            "WHERE ValueId = %i " % (newValue, valueId)
        print SQL
        system.db.runUpdateQuery(SQL)
    elif colName == "TiggerValueId":
        SQL = "UPDATE LtDerivedValue SET TriggerValueId = %i "\
            "WHERE ValueId = %i " % (newValue, valueId)
        print SQL
        system.db.runUpdateQuery(SQL)
    elif colName == "Callback":
        SQL = "UPDATE LtDerivedValue SET Callback = '%s' "\
            "WHERE ValueId = %i " % (newValue, valueId)
        print SQL
        system.db.runUpdateQuery(SQL)
    elif colName == "SampleTimeTolerance":
        SQL = "UPDATE LtDerivedValue SET SampleTimeTolerance = %i "\
            "WHERE ValueId = %i " % (newValue, valueId)
        print SQL
        system.db.runUpdateQuery(SQL)
    elif colName == "NewSampleWaitTime":
        SQL = "UPDATE LtDerivedValue SET NewSampleWaitTime = %i "\
            "WHERE ValueId = %i " % (newValue, valueId)
        print SQL
        system.db.runUpdateQuery(SQL)
    elif colName == "ResultItemId":
        SQL = "UPDATE LtDerivedValue SET ResultItemId = '%s' "\
            "WHERE ValueId = %i " % (newValue, valueId)
        print SQL
        system.db.runUpdateQuery(SQL)
    elif colName == "TriggerValueName":
        SQL = "SELECT ValueId FROM LtValue V "\
            " WHERE ValueName = '%s' " % (newValue)
        triggerValueId = system.db.runScalarQuery(SQL)
        print "triggerValueId = ", triggerValueId
        SQL = "UPDATE LtDerivedValue SET TriggerValueId = '%s' "\
            "WHERE ValueId = %i " % (triggerValueId, valueId)
        print SQL
        system.db.runUpdateQuery(SQL)
    elif colName == "InterfaceName":
        SQL = "SELECT InterfaceId FROM LtHdaInterface "\
            " WHERE InterfaceName = '%s' " % (newValue)
        interfaceId = system.db.runScalarQuery(SQL)
        print "interfaceId = ", interfaceId
        SQL = "UPDATE LtDerivedValue SET ResultInterfaceId = %i "\
            "WHERE ValueId = %i " % (interfaceId, valueId)
        print SQL
        system.db.runUpdateQuery(SQL)
    else:
        print "Found a column that I don't know how to update!"
                 
#remove the selected row
def removeRow(event):
    rootContainer = event.source.parent
    table = rootContainer.getComponent("Power Table")
    ds = table.data
    
    row = table.selectedRow
    valueId = ds.getValueAt(row, "ValueId")
    
    #remove row from LtRelatedData first
    derivedValueId = ds.getValueAt(row, "DerivedValueId")
    sql = "DELETE FROM LtRelatedData "\
        " WHERE DerivedValueId = %i " % (derivedValueId)
    system.db.runUpdateQuery(sql)
    
    #remove the selected row
    SQL = "DELETE FROM LtDerivedValue "\
        " WHERE ValueId = %i "\
        % (valueId)
    system.db.runUpdateQuery(SQL)
    
    #refresh table
    print "Calling update() from removeRow()..." 
    update(rootContainer)
    
#add a row
def insertDataRow(event):
    rootContainer = event.source.parent
    db = getDatabaseClient()

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
    
    ''' The following are required for the record into LtDerivedValue '''
    resultInterfaceId = rootContainer.getComponent("opcServerDropdown").selectedValue
    resultInterfaceName = rootContainer.getComponent("opcServerDropdown").selectedStringValue
    resultItemId = rootContainer.getComponent("itemId").text
    if resultItemId <> "" and resultInterfaceName == "":
        system.gui.messageBox("You must specify an Interface for the item-id!", "Warning")
        return False
    
    triggerValueId = rootContainer.getComponent("triggerDropdown").selectedValue
    triggerName = rootContainer.getComponent("triggerDropdown").selectedStringValue
    if triggerName == "":
        system.gui.messageBox("You must select a trigger value!", "Warning")
        return False
    
    print "Trigger: ", triggerName
    print "Trigger Id: ", triggerValueId
    
    callback = rootContainer.getComponent("callbackProcedure").text
    if callback == "":
        system.gui.messageBox("You must specify a callback!", "Warning")
        return False
    
    sampleTimeTolerance = rootContainer.getComponent("sampleTimeToleranceSpinner").intValue
    newSampleWaitTime = rootContainer.getComponent("newSampleWaitTimeSpinner").intValue

    SQL = "INSERT INTO LtValue (ValueName, Description, UnitId, DisplayDecimals)"\
        "VALUES ('%s', '%s', %i, %i)" %(newName, description, unitId, decimals)
    print SQL
    valueId = system.db.runUpdateQuery(SQL, getKey=True, database=db)
    
    if resultItemId == "":
        SQL = "INSERT INTO LtDerivedValue (ValueId, TriggerValueId, Callback, SampleTimeTolerance, NewSampleWaitTime)"\
            "VALUES (%s, %s, '%s', %s, %s)" %(str(valueId), str(triggerValueId), callback, sampleTimeTolerance, newSampleWaitTime)
    else:
        SQL = "INSERT INTO LtDerivedValue (ValueId, TriggerValueId, Callback, SampleTimeTolerance, NewSampleWaitTime, ResultItemId, ResultInterfaceId)"\
            "VALUES (%s, %s, '%s', %s, %s, %s, %s)" %(str(valueId), str(triggerValueId), callback, sampleTimeTolerance, newSampleWaitTime, str(resultItemId), str(resultInterfaceId))
    
    print SQL
    system.db.runUpdateQuery(SQL, database=db)
    return True
    
#add a row of related lab data
def insertRelatedDataRow(event):
    rootContainer = event.source.parent
    
    #insert blank row to be edited in place
    relatedTable = rootContainer.getComponent("relatedLabDataTable")
    ds = relatedTable.data
    newRow = [-1, "", ""]
    ds = system.dataset.addRow(ds, 0, newRow)
    relatedTable.data = ds
    
#remove the selected row
def removeRelatedDataRow(event):
    rootContainer = event.source.parent
    relatedTable = rootContainer.getComponent("relatedLabDataTable")
    row = relatedTable.selectedRow
    ds = relatedTable.data
    valueId = ds.getValueAt(row, "ValueId")
        
    #remove the selected row
    SQL = "DELETE FROM LtRelatedData "\
        "WHERE RelatedValueId = %i " % (valueId)
    system.db.runUpdateQuery(SQL)
    
    #refresh table
    print "Calling updateRelatedTable() from removeRelatedDataRow()..." 
    updateRelatedTable(rootContainer)
    
#update the database when user directly changes table 
def relatedDataCellEdited(table, rowIndex, colName, newValue):
    print "A related data cell has been edited so update the database..."
    rootContainer = table.parent
    ds = table.data
    valueId = ds.getValueAt(rowIndex, "ValueId")
    derivedValueId =  table.derivedValueId
    print "derivedValueId = ", derivedValueId
    
    #existing row is being edited
    if valueId != -1:
        print "editing an existing row"
        #get RelatedDataId (location to insert)
        SQL = "SELECT RelatedDataId FROM LtRelatedData "\
            "WHERE DerivedValueId = %i " % (derivedValueId)
        relatedDataId = system.db.runScalarQuery(SQL)
        print "relatedDataId = ", relatedDataId
    
        #get RelatedValueId (Value to insert)
        SQL = "SELECT ValueId FROM LtValue "\
            " WHERE ValueName = '%s' " % (newValue)
        relatedValueId = system.db.runScalarQuery(SQL)
        print "relatedValueId = ", relatedValueId
    
        #update the database
        SQL = "UPDATE LtRelatedData SET RelatedValueId = %i "\
            "WHERE RelatedDataId = %i " % (relatedValueId, relatedDataId)
        print SQL
        system.db.runUpdateQuery(SQL)
    else:
        print "inserting new row"
        SQL = "SELECT ValueId FROM LtValue WHERE ValueName = '%s' " % (newValue)
        relatedValueId = system.db.runScalarQuery(SQL)
        SQL = "INSERT INTO LtRelatedData (DerivedValueId, RelatedValueId) "\
            " VALUES (%i, %i) " % (derivedValueId, relatedValueId)
        print SQL
        system.db.runUpdateQuery(SQL, getKey=1)
        updateRelatedTable(rootContainer)