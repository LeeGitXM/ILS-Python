'''
Created on Jul 1, 2015

@author: Pete
'''
import system
from ils.sfc.common.constants import SQL

#open transaction when window is opened
def internalFrameOpened(rootContainer):
    # Keep the transaction open for one hour...
    txId = system.db.beginTransaction(timeout=3600000)
    rootContainer.txId = txId
    
    #clear related Table
    print "Calling updateRelatedTable() from internalFrameOpened()..."
    updateRelatedTable(rootContainer)
    
    #initialize datasets
    SQL = "SELECT ValueName FROM LtValue ORDER BY ValueName"
    pds = system.db.runQuery(SQL)
    rootContainer.triggerValueNameDataset = pds
    
    SQL = "SELECT ServerName FROM TkWriteLocation ORDER BY ServerName"
    pds = system.db.runQuery(SQL)
    rootContainer.serverNameDataset = pds
    
    SQL = "SELECT ValueName FROM LtValue ORDER BY ValueName"
    pds = system.db.runQuery(SQL)
    rootContainer.valueNameDataset = pds
    
#refresh when window is activated
def internalFrameActivated(rootContainer):
    print "Calling update() from internalFrameActivated()..."
    update(rootContainer)
    print "Calling updateRelatedTable() from internalFrameActivated()..."
    updateRelatedTable(rootContainer)
    

#close transaction when window is closed
def internalFrameClosing(rootContainer):
    try:
        txId=rootContainer.txId
        system.db.rollbackTransaction(txId)
        print "Closing the transaction..."
        system.db.closeTransaction(txId)
    except:
        print "Caught an error trying to close the transaction"


#update the window
def update(rootContainer):
    print "...updating display table..."
    txId = rootContainer.txId
    table = rootContainer.getComponent("Power Table")
    dropDown= rootContainer.getComponent("Dropdown")
    unitId = dropDown.selectedValue
    ds = table.data
    
    #update display table
    SQL = "SELECT LtValue.ValueId, LtValue.ValueName, LtValue_1.ValueName AS TriggerValueName, LtValue.Description, LtValue.DisplayDecimals, "\
        " LtDerivedValue.DerivedValueId, LtDerivedValue.TriggerValueId, "\
        " LtDerivedValue.Callback, LtDerivedValue.SampleTimeTolerance, LtDerivedValue.NewSampleWaitTime, "\
        " TkWriteLocation.ServerName, LtDerivedValue.ResultItemId "\
        " FROM LtValue INNER JOIN LtDerivedValue ON LtValue.ValueId = LtDerivedValue.ValueId INNER JOIN "\
        " LtValue AS LtValue_1 ON LtDerivedValue.TriggerValueId = LtValue_1.ValueId LEFT OUTER JOIN TkWriteLocation ON LtDerivedValue.ResultWriteLocationId = TkWriteLocation.WriteLocationId "\
        " WHERE LtValue.UnitId = %i ORDER BY LtValue.ValueName " % (unitId)
        
    print SQL
    pds = system.db.runQuery(SQL, tx=txId)
    table.updateInProgress = True
    table.data = pds
    table.updateInProgress = False
    if table.selectedRow >= 0:
        valueId = ds.getValueAt(table.selectedRow, "ValueId")
        print "ValueId on next line:"
        print valueId
        
def updateRelatedTable(rootContainer):
    print "...updating related table..."
    txId = rootContainer.txId
    table = rootContainer.getComponent("Power Table")
    ds = table.data  
    relatedTable = rootContainer.getComponent("relatedLabDataTable")
    
    #update related table
    if table.selectedRow >= 0:
        row = table.selectedRow
        derivedValueId = ds.getValueAt(row, "DerivedValueId")
        relatedTable.derivedValueId = derivedValueId
        print "derivedValueId on next line:"
        print derivedValueId
        sql = "SELECT V.ValueId, V.ValueName, V.Description "\
            " FROM LtValue V, LtRelatedData R "\
            " WHERE R.DerivedValueId = %i AND R.RelatedValueId = V.ValueId"\
            " ORDER BY V.ValueName" % (derivedValueId) 
        print sql
        pds = system.db.runQuery(sql, tx=txId)
        relatedTable.data = pds
    else:
        print "no selected row: clear related table"
        derivedValueId = -1
        sql = "SELECT V.ValueId, V.ValueName, V.Description "\
            " FROM LtValue V, LtRelatedData R "\
            " WHERE R.DerivedValueId = %i AND R.RelatedValueId = V.ValueId"\
            " ORDER BY V.ValueName" % (derivedValueId) 
        print sql
        pds = system.db.runQuery(sql, tx=txId)
        relatedTable.data = pds
   
#update the database when user completes the newly added row 
def updateDatabase(rootContainer):
    print "Updating the database..."
    txId = rootContainer.txId
    table = rootContainer.getComponent("Power Table")
    ds = table.data
    
    name = ds.getValueAt(0, "ValueName")
    description = ds.getValueAt(0, "Description")
    decimals = ds.getValueAt(0, "DisplayDecimals")
    trigValue = ds.getValueAt(0, "TriggerValueId")
    callBack = ds.getValueAt(0, "Callback")
    resultItemId = ds.getValueAt(0, "ResultItemId")
    sampleTimeTolerance = ds.getValueAt(0, "SampleTimeTolerance")
    newSampleWaitTime = ds.getValueAt(0, "NewSampleWaitTime")
    unitId = rootContainer.getComponent("Dropdown").selectedValue
    isSelector = 0
    
    if name != "" and description != "" and decimals >= 0 and trigValue >= 0 and callBack != "" and isSelector != "":
        SQL = "INSERT INTO LtValue (ValueName, Description, DisplayDecimals, UnitId, IsSelector) "\
            " VALUES ('%s', '%s', %i, %i, %i)" % (name, description, decimals, unitId, isSelector)
        print SQL
        valueId = system.db.runUpdateQuery(SQL, tx=txId, getKey=1)
        sql = "INSERT INTO LtDerivedValue (ValueId, TriggerValueId, Callback, ResultItemId, SampleTimeTolerance, NewSampleWaitTime) "\
            " VALUES (%i, %i, '%s', '%s', %i, %i)" % (valueId, trigValue, callBack, resultItemId, sampleTimeTolerance, newSampleWaitTime)
        print sql
        system.db.runUpdateQuery(sql, tx=txId)
        
        print "Hello"
    else:
        print "Insufficient data to update the database..."
               
#update the database when user directly changes table 
def cellEdited(table, rowIndex, colName, newValue):
    print "A cell has been edited so update the database..."
    rootContainer = table.parent
    txId = rootContainer.txId
    ds = table.data
    valueId =  ds.getValueAt(rowIndex, "ValueId")
    
    if colName == "ValueName":
        SQL = "UPDATE LtValue SET ValueName = '%s' "\
            "WHERE ValueId = %i " % (newValue, valueId)
        print SQL
        system.db.runUpdateQuery(SQL, tx=txId)
    elif colName == "Description":
        SQL = "UPDATE LtValue SET Description = '%s' "\
            "WHERE ValueId = %i " % (newValue, valueId)
        print SQL
        system.db.runUpdateQuery(SQL, tx=txId)
    elif colName == "DisplayDecimals":
        SQL = "UPDATE LtValue SET DisplayDecimals = %i "\
            "WHERE ValueId = %i " % (newValue, valueId)
        print SQL
        system.db.runUpdateQuery(SQL, tx=txId)
    elif colName == "TiggerValueId":
        SQL = "UPDATE LtDerivedValue SET TriggerValueId = %i "\
            "WHERE ValueId = %i " % (newValue, valueId)
        print SQL
        system.db.runUpdateQuery(SQL, tx=txId)
    elif colName == "Callback":
        SQL = "UPDATE LtDerivedValue SET Callback = '%s' "\
            "WHERE ValueId = %i " % (newValue, valueId)
        print SQL
        system.db.runUpdateQuery(SQL, tx=txId)
    elif colName == "SampleTimeTolerance":
        SQL = "UPDATE LtDerivedValue SET SampleTimeTolerance = %i "\
            "WHERE ValueId = %i " % (newValue, valueId)
        print SQL
        system.db.runUpdateQuery(SQL, tx=txId)
    elif colName == "NewSampleWaitTime":
        SQL = "UPDATE LtDerivedValue SET NewSampleWaitTime = %i "\
            "WHERE ValueId = %i " % (newValue, valueId)
        print SQL
        system.db.runUpdateQuery(SQL, tx=txId)
    elif colName == "ResultItemId":
        SQL = "UPDATE LtDerivedValue SET ResultItemId = '%s' "\
            "WHERE ValueId = %i " % (newValue, valueId)
        print SQL
        system.db.runUpdateQuery(SQL, tx=txId)
    elif colName == "TriggerValueName":
        SQL = "SELECT ValueId FROM LtValue V "\
            " WHERE ValueName = '%s' " % (newValue)
        triggerValueId = system.db.runScalarQuery(SQL, tx = txId)
        print "triggerValueId = ", triggerValueId
        SQL = "UPDATE LtDerivedValue SET TriggerValueId = '%s' "\
            "WHERE ValueId = %i " % (triggerValueId, valueId)
        print SQL
        system.db.runUpdateQuery(SQL, tx=txId)
    elif colName == "ServerName":
        SQL = "SELECT WriteLocationId FROM TkWriteLocation "\
            " WHERE ServerName = '%s' " % (newValue)
        writeLocationId = system.db.runScalarQuery(SQL, tx=txId)
        print "writeLocationId = ", writeLocationId
        SQL = "UPDATE LtDerivedValue SET ResultWriteLocationId = %i "\
            "WHERE ValueId = %i " % (writeLocationId, valueId)
        print SQL
        system.db.runUpdateQuery(SQL, tx=txId)
                 
#remove the selected row
def removeRow(event):
    rootContainer = event.source.parent
    txId = rootContainer.txId
    table = rootContainer.getComponent("Power Table")
    ds = table.data
    
    row = table.selectedRow
    valueId = ds.getValueAt(row, "ValueId")
    
    #remove row from LtRelatedData first
    derivedValueId = ds.getValueAt(row, "DerivedValueId")
    sql = "DELETE FROM LtRelatedData "\
        " WHERE DerivedValueId = %i " % (derivedValueId)
    system.db.runUpdateQuery(sql, tx=txId)
    
    #remove the selected row
    SQL = "DELETE FROM LtDerivedValue "\
        " WHERE ValueId = %i "\
        % (valueId)
    system.db.runUpdateQuery(SQL, tx=txId)
    
    #refresh table
    print "Calling update() from removeRow()..." 
    update(rootContainer)
    
#add a row
def insertRow(event):
    rootContainer = event.source.parent
    table = rootContainer.getComponent("Power Table")
    ds = table.data
    newRow = [-1, "", "", "", -1, -1, -1, "", 10, 30, "", ""]
    ds = system.dataset.addRow(ds, 0, newRow)
    table.data = ds
    
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
    txId = rootContainer.txId
    relatedTable = rootContainer.getComponent("relatedLabDataTable")
    row = relatedTable.selectedRow
    ds = relatedTable.data
    valueId = ds.getValueAt(row, "ValueId")
        
    #remove the selected row
    SQL = "DELETE FROM LtRelatedData "\
        "WHERE RelatedValueId = %i " % (valueId)
    system.db.runUpdateQuery(SQL, tx=txId)
    
    #refresh table
    print "Calling updateRelatedTable() from removeRelatedDataRow()..." 
    updateRelatedTable(rootContainer)
    
#update the database when user directly changes table 
def relatedDataCellEdited(table, rowIndex, colName, newValue):
    print "A related data cell has been edited so update the database..."
    rootContainer = table.parent
    txId = rootContainer.txId
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
        relatedDataId = system.db.runScalarQuery(SQL, tx=txId)
        print "relatedDataId = ", relatedDataId
    
        #get RelatedValueId (Value to insert)
        SQL = "SELECT ValueId FROM LtValue "\
            " WHERE ValueName = '%s' " % (newValue)
        relatedValueId = system.db.runScalarQuery(SQL, tx=txId)
        print "relatedValueId = ", relatedValueId
    
        #update the database
        SQL = "UPDATE LtRelatedData SET RelatedValueId = %i "\
            "WHERE RelatedDataId = %i " % (relatedValueId, relatedDataId)
        print SQL
        system.db.runUpdateQuery(SQL, tx=txId)
    else:
        print "inserting new row"
        SQL = "SELECT ValueId FROM LtValue WHERE ValueName = '%s' " % (newValue)
        relatedValueId = system.db.runScalarQuery(SQL, tx=txId)
        SQL = "INSERT INTO LtRelatedData (DerivedValueId, RelatedValueId) "\
            " VALUES (%i, %i) " % (derivedValueId, relatedValueId)
        print SQL
        system.db.runUpdateQuery(SQL, tx=txId, getKey=1)
        updateRelatedTable(rootContainer)