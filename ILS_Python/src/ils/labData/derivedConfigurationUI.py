'''
Created on Jul 1, 2015

@author: Pete
'''
import system
from ils.sfc.common.constants import SQL

#open transaction when window is opened
def internalFrameOpened(rootContainer):
    txID = system.db.beginTransaction(timeout=300000)
    rootContainer.txID = txID
    update(rootContainer)
    
#refresh when window is activated
def internalFrameActivated(rootContainer):
    update(rootContainer)

#open transaction when window is opened
def internalFrameClosing(rootContainer):
    try:
        txId=rootContainer.txID
        system.db.rollbackTransaction(txId)
        system.db.closeTransaction(txId)
    except:
        print "Caught an error trying to close the transaction"


#update the window
def update(rootContainer):
    txID = rootContainer.txID
    table = rootContainer.getComponent("Power Table")
    dropDown= rootContainer.getComponent("Dropdown")
    unitId = dropDown.selectedValue
    relatedTable = rootContainer.getComponent("relatedLabDataTable")
    ds = table.data
    
    
    #update display table
    SQL = "SELECT V.ValueId, V.ValueName, V.Description, V.DisplayDecimals, D.DerivedValueId, D.TriggerValueId, D.Callback, "\
        " D.SampleTimeTolerance, D.NewSampleWaitTime, W.ServerName, D.ResultItemId "\
        " FROM LtValue V, LtDerivedValue D, TkWriteLocation W"\
        " WHERE V.ValueId = D.ValueId AND V.UnitId = %i AND W.WriteLocationId = D.ResultWriteLocationId "\
        " ORDER BY V.ValueName " % (unitId)
    print SQL
    pds = system.db.runQuery(SQL, tx=txID)
    table.updateInProgress = True
    table.data = pds
    table.updateInProgress = False
    
    #update related table
    if table.selectedRow >= 0:
        row = table.selectedRow
        derivedValueId = ds.getValueAt(row, "DerivedValueId")
        print derivedValueId
        sql = "SELECT V.ValueId, V.ValueName, V.Description "\
            " FROM LtValue V, LtRelatedData R "\
            " WHERE R.DerivedValueId = %i AND R.RelatedValueId = V.ValueId"\
            " ORDER BY V.ValueName" % (derivedValueId) 
        print sql
        pds = system.db.runQuery(sql, tx=txID)
        relatedTable.data = pds
   
#update the database when user completes the newly added row 
def updateDatabase(rootContainer):
    txID = rootContainer.txID
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
    
    if name != "" and description != "" and decimals >= 0 and trigValue >= 0 and callBack != "":
        SQL = "INSERT INTO LtValue (ValueName, Description, DisplayDecimals, UnitId) "\
            " VALUES ('%s', '%s', %i, %i)" % (name, description, decimals, unitId)
        print SQL
        valueId = system.db.runUpdateQuery(SQL, tx=txID, getKey=1)
        sql = "INSERT INTO LtDerivedValue (ValueId, TriggerValueId, Callback, ResultItemId, SampleTimeTolerance, NewSampleWaitTime) "\
            " VALUES (%i, %i, '%s', '%s', %i, %i)" % (valueId, trigValue, callBack, resultItemId, sampleTimeTolerance, newSampleWaitTime)
        print sql
        system.db.runUpdateQuery(sql, tx=txID)
        
        print "Hello"
               
#update the database when user directly changes table 
def cellEdited(table, rowIndex, colName, newValue):
    rootContainer = table.parent
    txID = rootContainer.txID
    ds = table.data
    valueId =  ds.getValueAt(rowIndex, "ValueId")
    
    
    if colName == "ValueName":
        SQL = "UPDATE LtValue SET ValueName = '%s' "\
            "WHERE ValueId = %i " % (newValue, valueId)
    elif colName == "Description":
        SQL = "UPDATE LtValue SET Description = '%s' "\
            "WHERE ValueId = %i " % (newValue, valueId)
    elif colName == "DisplayDecimals":
        SQL = "UPDATE LtValue SET DisplayDecimals = %i "\
            "WHERE ValueId = %i " % (newValue, valueId)
    elif colName == "TiggerValueId":
        SQL = "UPDATE LtDerivedValue SET TriggerValueId = %i "\
            "WHERE ValueId = %i " % (newValue, valueId)
    elif colName == "Callback":
        SQL = "UPDATE LtDerivedValue SET Callback = '%s' "\
            "WHERE ValueId = %i " % (newValue, valueId)
    elif colName == "SampleTimeTolerance":
        SQL = "UPDATE LtDerivedValue SET SampleTimeTolerance = %i "\
            "WHERE ValueId = %i " % (newValue, valueId)
    elif colName == "NewSampleWaitTime":
        SQL = "UPDATE LtDerivedValue SET NewSampleWaitTime = %i "\
            "WHERE ValueId = %i " % (newValue, valueId)
    elif colName == "ResultItemId":
        SQL = "UPDATE LtDerivedValue SET ResultItemId = '%s' "\
            "WHERE ValueId = %i " % (newValue, valueId)
            
    print SQL
    system.db.runUpdateQuery(SQL, tx=txID)
    
    #update(rootContainer)
       
#remove the selected row
def removeRow(event):
    rootContainer = event.source.parent
    txID = rootContainer.txID
    table = rootContainer.getComponent("Power Table")
    ds = table.data
    
    row = table.selectedRow
    valueId = ds.getValueAt(row, "ValueId")
    
    #check for references
    #sql = "SELECT count(*) FROM LtValue WHERE ValueId = %i" %(valueId)
    #rows = system.db.runScalarQuery(sql, tx=txID)
    
    #if rows > 0:
     #   ans = system.gui.confirm("This table is in use. Do you want to remove this table?", "Confirm")
      #  if ans == False:
       #     return
       # else:
        #    sql = "update LtDerivedValue SET ValueId = NULL WHERE ValueId = %i" %(valueId)
         #   system.db.runUpdateQuery(sql, tx=txID)
    
    #remove row from LtRelatedData first
    derivedValueId = ds.getValueAt(row, "DerivedValueId")
    sql = "DELETE FROM LtRelatedData "\
        " WHERE DerivedValueId = %i " % (derivedValueId)
    system.db.runUpdateQuery(sql, tx=txID)
    
    #remove the selected row
    SQL = "DELETE FROM LtDerivedValue "\
        " WHERE ValueId = %i "\
        % (valueId)
    system.db.runUpdateQuery(SQL, tx=txID)
    
    #refresh table
    update(rootContainer)
    
#add a row
def insertRow(event):
    rootContainer = event.source.parent
    table = rootContainer.getComponent("Power Table")
    ds = table.data
    newRow = [-1, "", "", -1, -1, "", 10, 30, "", ""]
    ds = system.dataset.addRow(ds, 0, newRow)
    table.data = ds
    
#add a row of related lab data
def insertRelatedDataRow(event):
    rootContainer = event.source.parent
    txID = rootContainer.txID
    
    relatedValueId = rootContainer.getComponent("Dropdown").selectedValue
    derivedValueId = rootContainer.derivedValueId
    
    #insert the user's data as a new row
    SQL = "INSERT INTO LtRelatedData (DerivedValueId, RelatedValueId) "\
        " VALUES (%i, %i) " %(derivedValueId, relatedValueId)
    print SQL
    system.db.runUpdateQuery(SQL, tx=txID)
    
#remove the selected row
def removeRelatedDataRow(event):
    rootContainer = event.source.parent
    txID = rootContainer.txID
    relatedTable = rootContainer.getComponent("relatedLabDataTable")
    row = relatedTable.selectedRow
    ds = relatedTable.data
    valueId = ds.getValueAt(row, "ValueId")
        
    #remove the selected row
    SQL = "DELETE FROM LtRelatedData "\
        "WHERE RelatedValueId = %i " % (valueId)
    system.db.runUpdateQuery(SQL, tx=txID)
    
    #refresh table
    update(rootContainer)