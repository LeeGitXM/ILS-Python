'''
Created on Feb 1, 2017

@author: phass
'''

import system, string
from ils.common.cast import toBit
from ils.common.error import catchError, notifyError
from ils.sfc.recipeData.core import fetchRecipeDataTypeId, recipeDataExistsForStepId
from ils.common.config import getDatabaseClient
from ils.common.util import escapeSqlQuotes
from ils.log import getLogger
log =getLogger(__name__)

from ils.sfc.recipeData.constants import ARRAY, GROUP, INPUT, MATRIX, OUTPUT, OUTPUT_RAMP, RECIPE, SIMPLE_VALUE, SQC, TIMER

# The chart path is passed as a property when the window is opened.  Look up the chartId, refresh the Steps table and clear the RecipeData Table
def internalFrameOpened(rootContainer):
    db = getDatabaseClient()
    log.infof("In %s.internalFrameOpened(), db: %s", __name__, db)
    rootContainer.initialized = False
    
    recipeDataId = rootContainer.getPropertyValue("recipeDataId")
    recipeDataType = rootContainer.getPropertyValue("recipeDataType")
    
    if recipeDataId > 0:
        
        if recipeDataType == SIMPLE_VALUE:
            print "Fetching a simple value..."
            SQL = "select * from SfcRecipeDataSimpleValueView where recipeDataId = %s" % (recipeDataId)
            pds = system.db.runQuery(SQL, db)
            if len(pds) <> 1:
                raise ValueError, "Unable to fetch a Simple Value recipe data with id: %s" % (str(recipeDataId))
            record = pds[0]
            rootContainer.simpleValueDataset = pds

        elif recipeDataType == ARRAY:
            print "Fetching an Array"
            SQL = "select * from SfcRecipeDataArrayView where recipeDataId = %s" % (recipeDataId)
            pds = system.db.runQuery(SQL, db)
            if len(pds) <> 1:
                raise ValueError, "Unable to fetch an Array recipe data with id: %s" % (str(recipeDataId))
            record = pds[0]
            rootContainer.arrayDataset = pds
            
            # Set the visibility of the values columns so only the one for the target valueType is shown
            valueType = record["ValueType"]
            setArrayTableColumnVisibility(rootContainer, valueType)

            indexKeyId = record["IndexKeyId"]
            if indexKeyId == None:
                print "The array is not keyed..."
                SQL = "select convert(varchar(25), ArrayIndex) as ArrayIndex, FloatValue, IntegerValue, StringValue, BooleanValue from SfcRecipeDataArrayElementView where recipeDataId = %s order by ArrayIndex" % (recipeDataId)
                pds = system.db.runQuery(SQL, db)
            else:
                print "The array is keyed..."
                # First fetch the array 
                print "Fetching the array..."
                SQL = "select * from SfcRecipeDataArrayElementView where recipeDataId = %s order by ArrayIndex" % (recipeDataId)
                pds = system.db.runQuery(SQL, db)
                ds = system.dataset.toDataSet(pds)
                
                # Now Fetch the array Key
                print "Fetching the key..."
                SQL = "select * from SfcRecipeDataKeyView where KeyId = %s order by KeyIndex" % (indexKeyId)
                pds = system.db.runQuery(SQL, db)
                dsKey = system.dataset.toDataSet(pds)
                
                # They had better both have the same length
                if ds.rowCount != dsKey.rowCount:
                    print "AAAAgh they are not the same length"
                
                header = ["Key", "FloatValue", "IntegerValue", "StringValue", "BooleanValue"]
                data = []
                for i in range(dsKey.rowCount):
                    if i <= ds.rowCount:
                        key = dsKey.getValueAt(i, "KeyValue")
                        print "Overwriting the index with ", key
                        floatValue = ds.getValueAt(i, "FloatValue")
                        integerValue = ds.getValueAt(i, "IntegerValue")
                        stringValue = ds.getValueAt(i, "StringValue")
                        booleanValue = ds.getValueAt(i, "BooleanValue")

                        data.append([key, floatValue, integerValue, stringValue, booleanValue])
                        print ""
                
                ds = system.dataset.toDataSet(header, data)
                # Overwrite the arrayIndex of the first dataset, which are integeres, with the values of the key array, which are strings
                pds = system.dataset.toPyDataSet(ds)
                
            rootContainer.arrayValuesDataset = pds
            
        elif recipeDataType == MATRIX:
            print "Fetching an Matrix"
            SQL = "select * from SfcRecipeDataMatrixView where recipeDataId = %s" % (recipeDataId)
            pds = system.db.runQuery(SQL, db)
            if len(pds) <> 1:
                raise ValueError, "Unable to fetch a Matrix recipe data with id: %s" % (str(recipeDataId))
            record = pds[0]
            rootContainer.matrixDataset = pds
            numRows = record["Rows"]
            numColumns = record["Columns"]
            print "...the matrix is %d X %d..." % (numRows, numColumns)
            
            # Set the visibility of the values columns so only the one for the target valueType is shown
            valueType = record["ValueType"]
            setArrayTableColumnVisibility(rootContainer, valueType)
            
            rowIndexKeyId = record["RowIndexKeyId"]
            columnIndexKeyId = record["ColumnIndexKeyId"]
            
            if rowIndexKeyId == None and columnIndexKeyId == None:
                SQL = "select * from SfcRecipeDataMatrixElementView where recipeDataId = %s order by RowIndex, ColumnIndex" % (recipeDataId)
                pds = system.db.runQuery(SQL, db)
                rootContainer.matrixValuesDataset = pds
                
                rowLabels = []
                for i in range(0, numRows):
                    rowLabels.append(str(i))
                
                columnLabels = []
                for i in range(0, numColumns):
                    columnLabels.append(str(i))

            else:
                print "The matrix is keyed!"
                rowLabels = []
                columnLabels = []
                
                # Fetch the matrix data
                SQL = "select * from SfcRecipeDataMatrixElementView where recipeDataId = %s order by RowIndex, ColumnIndex" % (recipeDataId)
                pds = system.db.runQuery(SQL, db)
                ds = system.dataset.toDataSet(pds)
                rootContainer.matrixValuesDataset = pds
                
                # Now Fetch the row Key
                if rowIndexKeyId != None:
                    print "Fetching the row key..."
                    SQL = "select * from SfcRecipeDataKeyView where KeyId = %s order by KeyIndex" % (rowIndexKeyId)
                    pdsRow = system.db.runQuery(SQL, db)
                    dsRowKey = system.dataset.toDataSet(pdsRow)
                
                    # They had better both have the same length
                    if numRows != dsRowKey.rowCount:
                        print "AAAAgh the length of the row key and the number of rows in the matrix do not match.  There are %d rows in the matrix and %d row labels." % (numRows, dsRowKey.rowCount)
                    
                    header = ["Key", "FloatValue", "IntegerValue", "StringValue", "BooleanValue"]
                    data = []
                    rowLabels = []
                    for i in range(dsRowKey.rowCount):
                        if i <= ds.rowCount:
                            rowLabels.append(dsRowKey.getValueAt(i, "KeyValue"))
                else:
                    for i in range(0, numRows):
                        rowLabels.append(str(i))
                         
                # Now Fetch the array Key
                if columnIndexKeyId != None:
                    print "Fetching the column key..."
                    SQL = "select * from SfcRecipeDataKeyView where KeyId = %s order by KeyIndex" % (columnIndexKeyId)
                    pdsColumns = system.db.runQuery(SQL, db)
                    dsColumnKey = system.dataset.toDataSet(pdsColumns)
                
                    # They had better both have the same length
                    if numColumns != dsColumnKey.rowCount:
                        print "AAAAgh the length of the column key and the number of columns in the matrix do not match.  There are %d columns in the matrix and %d column labels." % (numColumns, dsColumnKey.rowCount)
            
                    header = ["Key", "FloatValue", "IntegerValue", "StringValue", "BooleanValue"]
                    data = []
                    columnLabels = []
                    for i in range(dsColumnKey.rowCount):
                        if i <= ds.rowCount:
                            columnLabels.append(dsColumnKey.getValueAt(i, "KeyValue"))
                else:
                    for i in range(0, numColumns):
                        columnLabels.append(str(i))
            
            print "The row labels are: ", rowLabels
            print "The column labels are: ", columnLabels
            
            container = rootContainer.getComponent("Matrix Container")
            updateMatrixTable(container, pds, rowLabels, columnLabels)

        elif recipeDataType == INPUT:
            print "Fetching an Input"
            SQL = "select * from SfcRecipeDataInputView where recipeDataId = %s" % (recipeDataId)
            pds = system.db.runQuery(SQL, db)
            if len(pds) <> 1:
                raise ValueError, "Unable to fetch an Input recipe data with id: %s" % (str(recipeDataId))
            record = pds[0]
            rootContainer.inputDataset = pds

        elif recipeDataType == OUTPUT:
            print "Fetching an Output"
            SQL = "select * from SfcRecipeDataOutputView where recipeDataId = %s" % (recipeDataId)
            pds = system.db.runQuery(SQL, db)
            if len(pds) <> 1:
                raise ValueError, "Unable to fetch an Output recipe data with id: %s" % (str(recipeDataId))
            record = pds[0]
            rootContainer.outputDataset = pds            
        
        elif recipeDataType == OUTPUT_RAMP:
            print "Fetching an Output Ramp"
            SQL = "select * from SfcRecipeDataOutputRampView where recipeDataId = %s" % (recipeDataId)
            pds = system.db.runQuery(SQL, db)
            if len(pds) <> 1:
                raise ValueError, "Unable to fetch an Output Ramp recipe data with id: %s" % (str(recipeDataId))
            record = pds[0]
            print "The output type is: ", record["OutputType"]
            rootContainer.outputRampDataset = pds
        
        elif recipeDataType == RECIPE:
            print "Fetching a Recipe"
            SQL = "select * from SfcRecipeDataRecipeView where recipeDataId = %s" % (recipeDataId)
            pds = system.db.runQuery(SQL, db)
            if len(pds) <> 1:
                raise ValueError, "Unable to fetch a Recipe recipe data with id: %s" % (str(recipeDataId))
            record = pds[0]
            rootContainer.recipeDataset = pds

        elif recipeDataType == TIMER:
            print "Fetching a Timer"
            SQL = "select * from SfcRecipeDataTimerView where recipeDataId = %s" % (recipeDataId)
            pds = system.db.runQuery(SQL, db)
            if len(pds) <> 1:
                raise ValueError, "Unable to fetch a Timer recipe data with id: %s" % (str(recipeDataId))
            record = pds[0]
            rootContainer.timerDataset = pds
            
        elif recipeDataType == SQC:
            print "Fetching a SQC"
            SQL = "select * from SfcRecipeDataSQCView where recipeDataId = %s" % (recipeDataId)
            pds = system.db.runQuery(SQL, db)
            if len(pds) <> 1:
                raise ValueError, "Unable to fetch a SQC recipe data with id: %s" % (str(recipeDataId))
            record = pds[0]
            rootContainer.sqcDataset = pds
        
        elif recipeDataType == GROUP:
            print "Fetching a Folder"
            SQL = "select * from SfcRecipeDataFolder where recipeDataFolderId = %s" % (recipeDataId)
            pds = system.db.runQuery(SQL, db)
            if len(pds) <> 1:
                raise ValueError, "Unable to fetch a GROUP recipe data with id: %s" % (str(recipeDataId))
            record = pds[0]
            rootContainer.groupDataset = pds

        else:
            raise ValueError, "Unexpected recipe data type <%s>" % (str(recipeDataType))

        rootContainer.description = record["Description"]
        rootContainer.advice = record["Advice"]
        rootContainer.label = record["Label"]
        
        if recipeDataType <> GROUP:
            rootContainer.recipeDataFolderId = record["FolderId"]
            units = record["Units"]
            if units <> None:
                units = string.upper(units)
            rootContainer.units = units
            print "Setting the units to: ", units
        
    else:
        if recipeDataType == GROUP:
            print "Initializing a group..."
            ds = rootContainer.groupDataset
            ds = system.dataset.setValue(ds, 0, "RecipeDataKey", "")
            ds = system.dataset.setValue(ds, 0, "Description", "")
            ds = system.dataset.setValue(ds, 0, "Advice", "")
            ds = system.dataset.setValue(ds, 0, "Label", "")
            rootContainer.groupDataset = ds
            
        elif recipeDataType == SIMPLE_VALUE:
            print "Initializing a simple value..."
            ds = rootContainer.simpleValueDataset
            ds = system.dataset.setValue(ds, 0, "RecipeDataKey", "")
            ds = system.dataset.setValue(ds, 0, "Description", "")
            ds = system.dataset.setValue(ds, 0, "Advice", "")
            ds = system.dataset.setValue(ds, 0, "Label", "")
            ds = system.dataset.setValue(ds, 0, "FloatValue", 0.0)
            ds = system.dataset.setValue(ds, 0, "IntegerValue", 0)
            ds = system.dataset.setValue(ds, 0, "StringValue", "")
            ds = system.dataset.setValue(ds, 0, "BooleanValue", 0)
            rootContainer.simpleValueDataset = ds

        elif recipeDataType == OUTPUT:
            print "Initializing an Output..."
            ds = rootContainer.outputDataset
            ds = system.dataset.setValue(ds, 0, "OutputFloatValue", 0.0)
            ds = system.dataset.setValue(ds, 0, "OutputIntegerValue", 0)
            ds = system.dataset.setValue(ds, 0, "OutputStringValue", "")
            ds = system.dataset.setValue(ds, 0, "OutputBooleanValue", False)
            ds = system.dataset.setValue(ds, 0, "TargetFloatValue", 0.0)
            ds = system.dataset.setValue(ds, 0, "TargetIntegerValue", 0)
            ds = system.dataset.setValue(ds, 0, "TargetStringValue", "")
            ds = system.dataset.setValue(ds, 0, "TargetBooleanValue", False)
            ds = system.dataset.setValue(ds, 0, "PVFloatValue", 0.0)
            ds = system.dataset.setValue(ds, 0, "PVIntegerValue", 0)
            ds = system.dataset.setValue(ds, 0, "PVStringValue", "")
            ds = system.dataset.setValue(ds, 0, "PVBooleanValue", False)
            ds = system.dataset.setValue(ds, 0, "Timing", 0.0)
            ds = system.dataset.setValue(ds, 0, "MaxTiming", 0.0)
            ds = system.dataset.setValue(ds, 0, "ActualTiming", 0.0)
            ds = system.dataset.setValue(ds, 0, "Tag", "")
            ds = system.dataset.setValue(ds, 0, "DownloadStatus", "")
            ds = system.dataset.setValue(ds, 0, "PVMonitorStatus", "")
            ds = system.dataset.setValue(ds, 0, "ErrorCode", "")
            ds = system.dataset.setValue(ds, 0, "ErrorText", "")
            ds = system.dataset.setValue(ds, 0, "WriteConfirmed", 0)
            ds = system.dataset.setValue(ds, 0, "PVMonitorActive", 0)
            rootContainer.outputDataset = ds
            
        elif recipeDataType == OUTPUT_RAMP:
            print "Initializing an Output Ramp..."
            ds = rootContainer.outputRampDataset
            ds = system.dataset.setValue(ds, 0, "OutputType", "Setpoint Ramp")
            ds = system.dataset.setValue(ds, 0, "OutputFloatValue", 0.0)
            ds = system.dataset.setValue(ds, 0, "OutputIntegerValue", 0)
            ds = system.dataset.setValue(ds, 0, "OutputStringValue", "")
            ds = system.dataset.setValue(ds, 0, "OutputBooleanValue", False)
            ds = system.dataset.setValue(ds, 0, "TargetFloatValue", 0.0)
            ds = system.dataset.setValue(ds, 0, "TargetIntegerValue", 0)
            ds = system.dataset.setValue(ds, 0, "TargetStringValue", "")
            ds = system.dataset.setValue(ds, 0, "TargetBooleanValue", False)
            ds = system.dataset.setValue(ds, 0, "PVFloatValue", 0.0)
            ds = system.dataset.setValue(ds, 0, "PVIntegerValue", 0)
            ds = system.dataset.setValue(ds, 0, "PVStringValue", "")
            ds = system.dataset.setValue(ds, 0, "PVBooleanValue", False)
            ds = system.dataset.setValue(ds, 0, "Timing", 0.0)
            ds = system.dataset.setValue(ds, 0, "MaxTiming", 0.0)
            ds = system.dataset.setValue(ds, 0, "ActualTiming", 0.0)
            ds = system.dataset.setValue(ds, 0, "Tag", "")
            ds = system.dataset.setValue(ds, 0, "DownloadStatus", "")
            ds = system.dataset.setValue(ds, 0, "PVMonitorStatus", "")
            ds = system.dataset.setValue(ds, 0, "ErrorCode", "")
            ds = system.dataset.setValue(ds, 0, "ErrorText", "")
            ds = system.dataset.setValue(ds, 0, "WriteConfirmed", False)
            ds = system.dataset.setValue(ds, 0, "PVMonitorActive", False)
            ds = system.dataset.setValue(ds, 0, "RampTimeMinutes", 10)
            ds = system.dataset.setValue(ds, 0, "UpdateFrequencySeconds", 30)
            ds = system.dataset.setValue(ds, 0, "Download", True)
            ds = system.dataset.setValue(ds, 0, "WriteConfirm", True)
            rootContainer.outputRampDataset = ds
            
        elif recipeDataType == INPUT:
            print "Initializing a new Input..."
            ds = rootContainer.inputDataset
            ds = system.dataset.setValue(ds, 0, "TargetFloatValue", 0.0)
            ds = system.dataset.setValue(ds, 0, "TargetIntegerValue", 0)
            ds = system.dataset.setValue(ds, 0, "TargetStringValue", "")
            ds = system.dataset.setValue(ds, 0, "TargetBooleanValue", False)
            ds = system.dataset.setValue(ds, 0, "PVFloatValue", 0.0)
            ds = system.dataset.setValue(ds, 0, "PVIntegerValue", 0)
            ds = system.dataset.setValue(ds, 0, "PVStringValue", "")
            ds = system.dataset.setValue(ds, 0, "PVBooleanValue", False)
            ds = system.dataset.setValue(ds, 0, "Tag", "")
            ds = system.dataset.setValue(ds, 0, "PVMonitorStatus", "")
            ds = system.dataset.setValue(ds, 0, "ErrorCode", "")
            ds = system.dataset.setValue(ds, 0, "ErrorText", "")
            ds = system.dataset.setValue(ds, 0, "PVMonitorActive", 0)
            rootContainer.inputDataset = ds
        
        elif recipeDataType == RECIPE:
            print "Initializing a new Recipe..."
            ds = rootContainer.recipeDataset
            ds = system.dataset.setValue(ds, 0, "PresentationOrder", 0)
            ds = system.dataset.setValue(ds, 0, "StoreTag", "")
            ds = system.dataset.setValue(ds, 0, "CompareTag", "")
            ds = system.dataset.setValue(ds, 0, "ModeAttribute", "")
            ds = system.dataset.setValue(ds, 0, "ModeValue", "")
            ds = system.dataset.setValue(ds, 0, "ChangeLevel", "")
            ds = system.dataset.setValue(ds, 0, "RecommendedValue", "")
            ds = system.dataset.setValue(ds, 0, "LowLimit", "")
            ds = system.dataset.setValue(ds, 0, "HighLimit", "")
            rootContainer.recipeDataset = ds

        elif recipeDataType == TIMER:
            print "Initializing a Timer..."
            ds = rootContainer.timerDataset
            rootContainer.timerDataset = ds
            
        elif recipeDataType == SQC:
            print "Initializing a SQC value..."
            ds = rootContainer.sqcDataset
            ds = system.dataset.setValue(ds, 0, "LowLimit", 0.0)
            ds = system.dataset.setValue(ds, 0, "TargetValue", 0.0)
            ds = system.dataset.setValue(ds, 0, "HighLimit", 0.0)
            rootContainer.sqcDataset = ds
        
        elif recipeDataType == ARRAY:
            print "Initializing an Array..."
            ds = rootContainer.arrayDataset
            rootContainer.arrayDataset = ds
            
            header = ["ArrayIndex","FloatValue","IntegerValue","StringValue","BooleanValue"]
            ds = system.dataset.toDataSet(header, [])
            rootContainer.arrayValuesDataset = ds
            
        elif recipeDataType == MATRIX:
            print "Initializing a new Matrix..."
            ds = rootContainer.matrixDataset
            ds = system.dataset.setValue(ds, 0, "RowIndexKeyName", None)
            ds = system.dataset.setValue(ds, 0, "RowIndexKeyId", None)
            ds = system.dataset.setValue(ds, 0, "ColumnIndexKeyName", None)
            ds = system.dataset.setValue(ds, 0, "ColumnIndexKeyId", None)
            rootContainer.matrixDataset = ds
            container = rootContainer.getComponent("Matrix Container")
            
            header = []
            data = []
            ds = system.dataset.toDataSet(header, data)
            pds = system.dataset.toPyDataSet(ds)
            updateMatrixTable(container, pds, [], [])

        else:
            raise ValueError, "Unexpected NEW recipe data type <%s>" % (recipeDataType)
        
        rootContainer.description = ""
        rootContainer.label = ""
        rootContainer.units = ""

#-------------------------------------------------------------------
# Array Related Procedures
#-------------------------------------------------------------------

def setArrayTableColumnVisibility(rootContainer, valueType):
    print "Setting the table column visibility"
    container = rootContainer.getComponent("Array Container")
    table = container.getComponent("Array Table")
    columnAttributes = table.columnAttributesData
    
    for column in ["Float", "Integer", "Boolean", "String"]:
        if column == valueType:
            hidden = False
        else:
            hidden = True

        # Find the row in the dataset for this data type (One row per dataType
        for row in range(columnAttributes.rowCount):
            if columnAttributes.getValueAt(row, "name") == column + "Value":
                columnAttributes = system.dataset.setValue(columnAttributes, row, "hidden", hidden)
    
    table.columnAttributesData = columnAttributes
    
    if valueType == "String":
        system.gui.transform(table, newX=50, newY=48, newWidth=377, newHeight=300)
        
        # This attempt at settin column width doesn't seem to work...
        table.setColumnWidth(0,20)
        table.setColumnWidth(1,20)
    else:
        system.gui.transform(table, newX=265, newY=48, newWidth=162, newHeight=300)
    
'''
The user has just selected a new array Key (or maybe this is called on startup)
This only applies to KEYED arrays, there are some shared data structures so make sure we are KEYED!
'''
def setArrayIndexVisibility(rootContainer, valueType):
    if rootContainer.recipeDataType != "Array":
        print "No need to set index visibility because the recipe data is not a keyed array"
        return
    
    print "Setting the Index column visibility for a keyed array"
    db = ""
    recipeDataId = rootContainer.recipeDataId
    container = rootContainer.getComponent("Array Container")
    table = container.getComponent("Array Table")
    columnAttributes = table.columnAttributesData
    
    combo = container.getComponent("Index Key Dropdown")
    keyName = combo.selectedStringValue
    keyId = combo.selectedValue
    
    print "...the indexKey is: ", keyName
    
    if keyId == -1:
        print "The user has changed the array from a keyed to unkeyed"
        ds = table.data

        for i in range(0, ds.rowCount):
            ds = system.dataset.setValue(ds, i, 0, str(i))

        table.data = ds
        
    else:
        SQL = "select KeyValue From SfcRecipeDataKeyView where KeyId = %d order by KeyIndex" % (keyId)
        pds = system.db.runQuery(SQL, db)
        
        print "...there are %d elements in the key..." % (len(pds))
        
        ds = rootContainer.arrayValuesDataset
        rowsInArray = ds.rowCount
        
        i = 0
        for record in pds:
            key = record["KeyValue"]
            print "Key: ", key
            
            if i < rowsInArray:
                print "Setting a row..."
                ds = system.dataset.setValue(ds, i, 0, key)
            else:
                print "Adding a row..."
                ds = system.dataset.addRow(ds,[key, 0.0, 0, "", 0])
            i = i + 1
        
        # If we are downsizing the array (the new key has fewer elements than the old key) then delete the extra rows
    #    if ds.rowCount > i:
        for i in range(i,ds.rowCount):
            print "Deleting an extra row...", i
            ds = system.dataset.deleteRow(ds, ds.rowCount - 1)
            
        rootContainer.arrayValuesDataset = ds

def addArrayRow(table):
    print "Adding a Row"
    ds = table.data
    recipeDataId = table.parent.parent.recipeDataId
    vals = [1, 0.0, 0, "", 0]
    selectedRow = table.selectedRow
    if selectedRow < 0:
        # Insert at the end
        row = ds.rowCount
        print "Inserting a row at the End"
        ds = system.dataset.addRow(ds, row, vals)
    else:
        print "Inserting after current row "
        ds = system.dataset.addRow(ds, selectedRow + 1, vals)
        
    table.data = ds
    renumberArrayRows(table)

def deleteArrayRow(table):
    print "Deleting a Row"
    selectedRows = table.getSelectedRows()
    ds = system.dataset.deleteRows(table.data, selectedRows)
    table.data = ds
    renumberArrayRows(table)

def renumberArrayRows(table):
    ds = table.data
    for row in range(ds.rowCount):
        ds = system.dataset.setValue(ds, row, 0, row)
    table.data = ds
    

#-------------------------------------------------------------------
# Matrix Related Procedures
#-------------------------------------------------------------------

'''
When updating the matrix data structure we MUST honor the length of the rows and columns and
fill in the blanks if needed.
'''
def updateMatrixTable(container, pds, rowLabels, columnLabels):
    table = container.getComponent("Matrix Table")
    
    columnLabels.insert(0,'row')
    
    data = []
    for label in rowLabels:
        row = [label]
        for val in range(0,len(columnLabels) - 1):
            row.append(None)
        data.append(row)
 
    ds = system.dataset.toDataSet(columnLabels, data)
    
    for record in pds:
        row = record["RowIndex"]
        column = record["ColumnIndex"] + 1
        val = record["FloatValue"]
        
        ds = system.dataset.setValue(ds, row, column, val)
    
    table.data = ds


'''
The user has just selected a new array Key (or maybe this is called on startup)
This only applies to KEYED arrays, there are some shared data structures so make sure we are KEYED!
'''
def setMatrixRowIndexVisibility(rootContainer, valueType):
    if rootContainer.recipeDataType != MATRIX:
        print "No need to set index visibility because the recipe data is not a keyed matrix"
        return
    
    if rootContainer.initialized == False:
        print "Not setting the row keys because the window is not initialized"
        return
    
    db = ""
    recipeDataId = rootContainer.recipeDataId
    container = rootContainer.getComponent("Matrix Container")
    table = container.getComponent("Matrix Table")
    combo = container.getComponent("Row Index Key Dropdown")
    indexKey = combo.selectedStringValue
    indexRecipeDataId = combo.selectedValue
    
    if indexRecipeDataId == -1:
        print "The user has changed the matrix row from a keyed to unkeyed"
        ds = table.data

        for i in range(0, ds.rowCount):
            ds = system.dataset.setValue(ds, i, 0, str(i))

        table.data = ds
    else:
        print "Setting the row keys for a keyed matrix..."
        print "...the indexKey is: ", indexKey
        
        SQL = "select KeyValue From SfcRecipeDataKeyView where KeyName = '%s' order by KeyIndex" % (indexKey)
        pds = system.db.runQuery(SQL, db)
        
        ds = table.data
        rowsInArray = ds.rowCount
        
        i = 0
        for record in pds:
            key = record["KeyValue"]
            print "Key: ", key
            
            if i < rowsInArray:
                ds = system.dataset.setValue(ds, i, "row", key)
            else:
                vals = [key]
                for j in range(1,ds.columnCount):
                    vals.append(0.0)
    
                ds = system.dataset.addRow(ds, vals)
            i = i + 1
    
        
        # If we are downsizing the array (the new key has fewer elements than the old key) then delete the extra row
        for i in range(i,ds.rowCount):
            ds = system.dataset.deleteRow(ds,ds.rowCount - 1)   # Always delete the last row
            
        table.data = ds

'''
The user has just selected a new array Key (or maybe this is called on startup)
This only applies to KEYED arrays, there are some shared data structures so make sure we are KEYED!
'''
def setMatrixColumnIndexVisibility(rootContainer, valueType):
    if rootContainer.recipeDataType != MATRIX:
        print "No need to set index visibility because the recipe data is not a keyed matrix"
        return
    
    if rootContainer.initialized == False:
        print "Not setting the column keys because the window is not initialized"
        return
    
    print "Setting the column keys for a keyed matrix"
    db = ""
    recipeDataId = rootContainer.recipeDataId
    container = rootContainer.getComponent("Matrix Container")
    table = container.getComponent("Matrix Table")
    ds = table.data
    oldRowCount = ds.rowCount
    oldColumnCount = ds.columnCount
       
    combo = container.getComponent("Column Index Key Dropdown")
    indexKey = combo.selectedStringValue
    indexRecipeDataId = combo.selectedValue
    
    print "...the indexKey is: ", indexKey
    
    if indexRecipeDataId == -1:
        print "The user has changed the matrix column from a keyed to unkeyed"

        '''
        I can't find a way to update the table header, so totally recreate the dataset
        '''
        header = ["row"]
        for col in range(0, oldColumnCount - 1):
            header.append(col)
            
        data = []
        for row in range(0, oldRowCount):
            vals = []
            for col in range(0, oldColumnCount):
                if col < oldColumnCount:
                    val = ds.getValueAt(row, col)
                else:
                    val = 0.0
                vals.append(val)
            data.append(vals)

        ds = system.dataset.toDataSet(header, data)
        table.data = ds
    else:
        SQL = "select KeyValue From SfcRecipeDataKeyView where KeyName = '%s' order by KeyIndex" % (indexKey)
        pds = system.db.runQuery(SQL, db)
        header = ["row"]
        for record in pds:
            key = record["KeyValue"]
            header.append(key)
        print "New header: ", header
        newColumnCount = len(header)
        
        data = []
        for row in range(0, oldRowCount):
            vals = []
            for col in range(0, newColumnCount):
                print "(%d, %d)" % (row, col)
                if col < oldColumnCount:
                    val = ds.getValueAt(row, col)
                else:
                    val = 0.0
                vals.append(val)
            print "Adding row: ", vals
            data.append(vals)
        ds = system.dataset.toDataSet(header, data)
        
    table.data = ds


def renumberMatrixRows(ds):
    for row in range(ds.rowCount):
        ds = system.dataset.setValue(ds, row, "row", row)
    return ds
    
def addMatrixRow(table):
    ds = table.data
    
    if table.selectedRow >= 0:
        vals = [table.selectedRow]
    else:
        vals = [ds.rowCount]
    
    for i in range(ds.columnCount - 1):
        vals.append(0.0)
    
    print vals
    if table.selectedRow >= 0:
        ds = system.dataset.addRow(ds, table.selectedRow, vals)
    else:
        ds = system.dataset.addRow(ds, vals)

    ds = renumberMatrixRows(ds)
    table.data = ds


def addMatrixColumn(table):
    ds = table.data
    
    # Append a new column header
    header = system.dataset.getColumnHeaders(ds)
    header.append(ds.columnCount - 1)
    
    vals = []
    for i in range(ds.rowCount):
        row = []
        for j in range(ds.columnCount):
            if j == table.selectedColumn:
                row.append(0.0)
                
            val=ds.getValueAt(i,j)
            row.append(val)
        
        # If there wasn't a selected column then add a new value at the end
        if table.selectedColumn == -1:
            row.append(0.0)
    
        vals.append(row)

    ds = system.dataset.toDataSet(header, vals)
    table.data = ds
    
    if ds.columnCount > 6:
        table.autoResizeMode = 0
    else:
        table.autoResizeMode = 1
        

# This is called once by a timer shortly after the window is activated.  It gets around the age old problem I have where the
# list of values are bound to query and the selected value is bound to a property and there is a timing issue between the two of them.
def refreshComboBoxes(event):
    print "Refreshing the combo boxes from a timer"
    rootContainer = event.source.parent
    
    # Common Combos
    # --- I'm not sure why the units seems to work ---
    
    recipeDataType = rootContainer.recipeDataType
    
    if recipeDataType == SIMPLE_VALUE:
        # Simple Value Combos
        container = rootContainer.getComponent("Simple Value Container")
        combo = container.getComponent("Value Type Dropdown")
        ds = rootContainer.simpleValueDataset
        valueType = ds.getValueAt(0,"ValueType")
        combo.selectedStringValue = valueType
    
    elif recipeDataType == INPUT:
        # Input Combos
        container = rootContainer.getComponent("Input Container")    
        combo = container.getComponent("Value Type Dropdown")
        ds = rootContainer.inputDataset
        valueType = ds.getValueAt(0,"ValueType")
        combo.selectedStringValue = valueType
    
    elif recipeDataType == OUTPUT:
        # Output Combos
        container = rootContainer.getComponent("Output Container")
        combo = container.getComponent("Output Type Dropdown")
        ds = rootContainer.outputDataset
        outputType = ds.getValueAt(0,"OutputType")
        combo.selectedStringValue = outputType
        
        combo = container.getComponent("Value Type Dropdown")
        valueType = ds.getValueAt(0,"ValueType")
        combo.selectedStringValue = valueType
    
    elif recipeDataType == OUTPUT_RAMP:
        print "Setting the combo box values for an output ramp..."
        # Output Combos
        container = rootContainer.getComponent("Output Ramp Container")
        combo = container.getComponent("Output Type Dropdown")
        ds = rootContainer.outputRampDataset
        outputType = ds.getValueAt(0,"OutputType")
        print "...setting the output type to: ", outputType
        combo.selectedStringValue = outputType

        combo = container.getComponent("Value Type Dropdown")
        valueType = ds.getValueAt(0,"ValueType")
        print "...setting the value type to: ", valueType
        combo.selectedStringValue = valueType
    
    elif recipeDataType == ARRAY:
        # Array Combos
        print "Updating the array combo boxes..."
        container = rootContainer.getComponent("Array Container")
        
        combo = container.getComponent("Value Type Dropdown")
        ds = rootContainer.arrayDataset
        rows = ds.rowCount
        valueType = ds.getValueAt(0,"ValueType")
        combo.selectedStringValue = valueType
        
        combo = container.getComponent("Index Key Dropdown")
        addUnselectionChoice(combo)
        keyName = ds.getValueAt(0,"KeyName")
        if rows == 0:
            combo.selectedValue = -1
        else:
            combo.selectedStringValue = keyName
    
    elif recipeDataType == MATRIX:
        # Matrix Combos
        print "Updating the matrix combo boxes..."
        container = rootContainer.getComponent("Matrix Container")
        
        combo = container.getComponent("Row Index Key Dropdown")
        addUnselectionChoice(combo)
        
        ds = rootContainer.matrixDataset
        rows = ds.rowCount  # Not sure what this is suppossed to do
        indexKey = ds.getValueAt(0,"RowIndexKeyName")
        print "Setting the row index key to: ", indexKey
        if rows == 0:
            combo.selectedValue = -1
        else:
            combo.selectedStringValue = indexKey
        
        combo = container.getComponent("Column Index Key Dropdown")
        addUnselectionChoice(combo)
        
        indexKey = ds.getValueAt(0,"ColumnIndexKeyName")
        print "Setting the column index key to: ", indexKey
        if rows == 0:
            combo.selectedValue = -1
        else:
            combo.selectedStringValue = indexKey

'''
Add the unselect choice at the top of the list
'''
def addUnselectionChoice(combo):
    print "Adding unselection choice"
    ds = combo.data
    ds = system.dataset.addRow(ds, 0, [-1, "<Select One>"])
    combo.data = ds
    
def validateKey(source):
    ''' 
    This is called from the focusLost handler.  
    Source is the key text field.
    Key validation is:
        1) there aren't any periods
        2) isn't NULL
        3) is unique
    '''
    
    db = getDatabaseClient()
    key = source.text
    
    ''' Validate for an empty key '''
    if key == "":
        system.gui.warningBox("Warning: you must specify a key")
        return False
    
    ''' Validate that the key does not contain periods '''
    if key.find(".") >= 0:
        system.gui.warningBox("Warning: the key cannot contain periods")
        return False
    
    ''' Validate that a key for a new recipe entity is unique. '''
    rootContainer = source.parent
    stepId = rootContainer.stepId
    folderId = rootContainer.recipeDataFolderId
    recipeDataId = rootContainer.recipeDataId
    if recipeDataId < 0:
        print "Validate key uniqueness for a new recipe data entity"
        if (recipeDataExistsForStepId(stepId, folderId, key, db)):
            system.gui.warningBox("Warning: the key already exists, keys must be unique!")
            return False
    
    ''' Validate that the key is unique when the key is being changed '''
    if recipeDataId > 0:
        oldKey = getKeyForId(recipeDataId, db)
        if oldKey != key:
            print "Validate uniqueness of a renamed KEY"
            if (recipeDataExistsForStepId(stepId, folderId, key, db)):
                system.gui.warningBox("Warning: the key already exists, keys must be unique!")
                return False
    
    return True 

def getKeyForId(recipeDataId, db):
    key = system.db.runScalarQuery("select RecipeDataKey from SfcRecipeData where RecipeDataId = %s" % (str(recipeDataId)), db)
    return key

def saveGroup(event):
    print "Saving a group"
    
    rootContainer = event.source.parent.parent
    
    if not(validateKey(rootContainer.getComponent("Key"))):
        return

    db = getDatabaseClient()
    recipeDataId = rootContainer.recipeDataId
    stepId = rootContainer.stepId
    recipeDataFolderId = rootContainer.recipeDataFolderId
    key = rootContainer.getComponent("Key").text
    description = rootContainer.getComponent("Description").text
    description = escapeSqlQuotes(description)
    advice = rootContainer.getComponent("Advice").text
    advice = escapeSqlQuotes(advice)
    label = rootContainer.getComponent("Label").text
    label = escapeSqlQuotes(label)
    
    tx = system.db.beginTransaction(db)
    
    try:
        if recipeDataId < 0:
            print "Inserting a new group..."
            if recipeDataFolderId < 0:
                SQL = "insert into SfcRecipeDataFolder (StepId, RecipeDataKey, Description, Advice, Label) "\
                    "values (%s, '%s', '%s', '%s', '%s')" % (stepId, key, description, advice, label)
            else:
                SQL = "insert into SfcRecipeDataFolder (StepId, RecipeDataKey, Description, Advice, Label, ParentRecipeDataFolderId) "\
                    "values (%s, '%s', '%s', '%s', '%s', %s)" % (stepId, key, description, advice, label, recipeDataFolderId)
            print SQL
            recipeDataId = system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
            rootContainer.recipeDataId = recipeDataId
        else:
            print "Updating a group..."
            recipeDataId = rootContainer.recipeDataId
            SQL = "update SfcRecipeDataFolder set RecipeDataKey='%s', Description='%s', Advice = '%s', Label = '%s' where RecipeDataFolderId = %d " % (key, description, advice, label, recipeDataId)
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)
            
        system.db.commitTransaction(tx)
        system.db.closeTransaction(tx) 
    except:
        errorTxt = notifyError("ils.sfc.recipeData.visionEditor.saveGroup", "Caught an error, rolling back transactions")
        system.db.rollbackTransaction(tx)
        system.db.closeTransaction(tx)
        raise Exception("Save Recipe Data Exception: %s", errorTxt)
    
    closeAndOpenBrowser(event)


def saveSimpleValue(event):
    print "Saving a simple value"

    rootContainer = event.source.parent.parent
    
    if not(validateKey(rootContainer.getComponent("Key"))):
        return

    db = getDatabaseClient()
    recipeDataId = rootContainer.recipeDataId
    stepId = rootContainer.stepId
    folderId = rootContainer.recipeDataFolderId
    key = rootContainer.getComponent("Key").text
    description = rootContainer.getComponent("Description").text
    description = escapeSqlQuotes(description)
    advice = rootContainer.getComponent("Advice").text
    advice = escapeSqlQuotes(advice)
    label = rootContainer.getComponent("Label").text
    label = escapeSqlQuotes(label)
    units = rootContainer.getComponent("Units Dropdown").selectedStringValue
    simpleValueContainer=rootContainer.getComponent("Simple Value Container")
    valueType = simpleValueContainer.getComponent("Value Type Dropdown").selectedStringValue
    valueTypeId = simpleValueContainer.getComponent("Value Type Dropdown").selectedValue
    
    tx = system.db.beginTransaction(db)
    
    try:
        if recipeDataId < 0:
            print "Inserting a simple value..."
            
            recipeDataType = rootContainer.recipeDataType
            recipeDataTypeId = fetchRecipeDataTypeId(recipeDataType, db)
            
            recipeDataId = insertRecipeData(stepId, key, recipeDataTypeId, description, advice, label, units, folderId, tx)
            rootContainer.recipeDataId = recipeDataId
            
            if valueType == "Float":
                val = simpleValueContainer.getComponent("Float Value").floatValue
                SQL = "Insert into SfcRecipeDataValue (RecipeDataId, FloatValue) values (%d, %f)" % (recipeDataId, val)
            elif valueType == "Integer":
                val = simpleValueContainer.getComponent("Integer Value").intValue
                SQL = "Insert into SfcRecipeDataValue (RecipeDataId, IntegerValue) values (%d, %d)" % (recipeDataId, val)
            elif valueType == "String":
                val = simpleValueContainer.getComponent("String Value").text
                val = escapeSqlQuotes(val)
                SQL = "Insert into SfcRecipeDataValue (RecipeDataId, StringValue) values (%d, '%s')" % (recipeDataId, val)
            elif valueType == "Boolean":
                val = simpleValueContainer.getComponent("Boolean Value").selected
                val = toBit(val)
                SQL = "Insert into SfcRecipeDataValue (RecipeDataId, BooleanValue) values (%d, %d)" % (recipeDataId, val)
            
            print SQL
            valueId = system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
            
            SQL = "Insert into SfcRecipeDataSimpleValue (RecipeDataId, ValueTypeId, ValueId) values (%d, %d, %d)" % (recipeDataId, valueTypeId, valueId)
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)
            
        else:
            print "Updating a simple value..."
            ds = rootContainer.simpleValueDataset
            valueId = ds.getValueAt(0,"ValueId")
            recipeDataId = rootContainer.recipeDataId
            updateRecipeData(key, description, advice, label, units, recipeDataId, tx)
            
            SQL = "Update SfcRecipeDataSimpleValue set ValueTypeId=%d where RecipeDataId = %d" % (valueTypeId, recipeDataId)
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)
            
            if valueType == "Float":
                val = simpleValueContainer.getComponent("Float Value").floatValue
            elif valueType == "Integer":
                val = simpleValueContainer.getComponent("Integer Value").intValue
            elif valueType == "String":
                val = simpleValueContainer.getComponent("String Value").text
                val = escapeSqlQuotes(val)
            elif valueType == "Boolean":
                val = simpleValueContainer.getComponent("Boolean Value").selected
                val = toBit(val)
    
            updateRecipeDataValue(valueId, valueType, val, tx)

        system.db.commitTransaction(tx)
        system.db.closeTransaction(tx) 
    except:
        errorTxt = catchError("ils.sfc.recipeData.visionEditor.saveSimpleValue", "Caught an error, rolling back transactions")
        system.db.rollbackTransaction(tx)
        system.db.closeTransaction(tx)
        raise Exception("Save Recipe Data Exception: %s" % (errorTxt))
    
    closeAndOpenBrowser(event)

def saveInput(event):
    print "Saving an Input"
    
    rootContainer = event.source.parent.parent
    
    if not(validateKey(rootContainer.getComponent("Key"))):
        return

    db = getDatabaseClient()
    recipeDataId = rootContainer.recipeDataId
    stepId = rootContainer.stepId
    folderId = rootContainer.recipeDataFolderId
    key = rootContainer.getComponent("Key").text
    description = rootContainer.getComponent("Description").text
    description = escapeSqlQuotes(description)
    advice = rootContainer.getComponent("Advice").text
    advice = escapeSqlQuotes(advice)
    label = rootContainer.getComponent("Label").text
    label = escapeSqlQuotes(label)
    units = rootContainer.getComponent("Units Dropdown").selectedStringValue
    inputContainer=rootContainer.getComponent("Input Container")
    
    tag = inputContainer.getComponent("Tag").text
    
    # For now, the valueType of an output is always a Float
    valueType = inputContainer.getComponent("Value Type Dropdown").selectedStringValue
    valueTypeId = inputContainer.getComponent("Value Type Dropdown").selectedValue
    
    tx = system.db.beginTransaction(db)
    
    try:
        if recipeDataId < 0:
            print "Inserting an Input..."
            
            recipeDataType = rootContainer.recipeDataType
            recipeDataTypeId = fetchRecipeDataTypeId(recipeDataType, db)
            recipeDataId = insertRecipeData(stepId, key, recipeDataTypeId, description, advice, label, units, folderId, tx)
            rootContainer.recipeDataId = recipeDataId
            
            # The values are meaningless until someone uses this data in a PV Monitoring block
            SQL = "insert into SfcRecipeDataValue (recipeDataId, BooleanValue) values (%d, 0)" % (recipeDataId)
            pvValueId = system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
            SQL = "insert into SfcRecipeDataValue (recipeDataId, BooleanValue) values (%d, 0)" % (recipeDataId)
            targetValueId = system.db.runUpdateQuery(SQL, getKey=True, tx=tx)

            SQL = "Insert into SfcRecipeDataInput (RecipeDataId, ValueTypeId, TargetValueId, PVValueId, Tag) "\
                "values (%d, %d, %d, %d, '%s')" \
                % (recipeDataId, valueTypeId, targetValueId, pvValueId, tag)            
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)
        else:
            print "Updating an Input..."
            recipeDataId = rootContainer.recipeDataId
            updateRecipeData(key, description, advice, label, units, recipeDataId, tx)

            SQL = "Update SfcRecipeDataInput set ValueTypeId=%d, Tag='%s' where RecipeDataId = %d" % (valueTypeId, tag, recipeDataId)
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)

        system.db.commitTransaction(tx)
        system.db.closeTransaction(tx) 
    except:
        errorTxt = catchError("ils.sfc.recipeData.visionEditor.saveInput", "Caught an error, rolling back transactions")
        system.db.rollbackTransaction(tx)
        system.db.closeTransaction(tx) 
        raise Exception("Save Recipe Data Exception: %s", errorTxt)
    
    closeAndOpenBrowser(event)


def saveOutput(event):
    print "Saving an Output"
    
    rootContainer = event.source.parent.parent
    
    if not(validateKey(rootContainer.getComponent("Key"))):
        return

    db = getDatabaseClient()
    recipeDataId = rootContainer.recipeDataId
    stepId = rootContainer.stepId
    folderId = rootContainer.recipeDataFolderId
    key = rootContainer.getComponent("Key").text
    description = rootContainer.getComponent("Description").text
    description = escapeSqlQuotes(description)
    advice = rootContainer.getComponent("Advice").text
    advice = escapeSqlQuotes(advice)
    label = rootContainer.getComponent("Label").text
    label = escapeSqlQuotes(label)
    units = rootContainer.getComponent("Units Dropdown").selectedStringValue
    outputContainer=rootContainer.getComponent("Output Container")
    
    outputType = outputContainer.getComponent("Output Type Dropdown").selectedStringValue
    outputTypeId = outputContainer.getComponent("Output Type Dropdown").selectedValue
    tag = outputContainer.getComponent("Tag").text
    download = outputContainer.getComponent("Download").selected
    download=toBit(download)
    timing = outputContainer.getComponent("Timing").floatValue
    maxTiming = outputContainer.getComponent("Max Timing").floatValue
    writeConfirm = outputContainer.getComponent("Write Confirm").selected
    writeConfirm=toBit(writeConfirm)
    
    # For now, the valueType of an output is always a Float
    valueType = outputContainer.getComponent("Value Type Dropdown").selectedStringValue
    valueTypeId = outputContainer.getComponent("Value Type Dropdown").selectedValue
    
    tx = system.db.beginTransaction(db)
    
    try:
        if recipeDataId < 0:
            print "Inserting an Output..."
            
            recipeDataType = rootContainer.recipeDataType
            recipeDataTypeId = fetchRecipeDataTypeId(recipeDataType, db)
            recipeDataId = insertRecipeData(stepId, key, recipeDataTypeId, description, advice, label, units, folderId, tx)
            rootContainer.recipeDataId = recipeDataId
            
            valueIds=[]
            for i in [0,1,2]:
                # TargetValue and PV Value are dynamic values that cannot be edited.
                if i == 0:
                    attr = valueType + "Value"
                    if valueType == 'String':
                        val = outputContainer.getComponent("Output String Value").text
                        SQL = "insert into SfcRecipeDataValue (recipeDataId, %s) values (%d, '%s')" % (attr, recipeDataId, val)
                    else:
                        if valueType == 'Float':
                            val = outputContainer.getComponent("Output Float Value").floatValue
                        elif valueType == 'Integer':
                            val = outputContainer.getComponent("Output Integer Value").intValue
                        elif valueType == 'Boolean':
                            val = outputContainer.getComponent("Output Boolean Value").selected
                            val = toBit(val)
                        SQL = "insert into SfcRecipeDataValue (recipeDataId, %s) values (%d, %s)" % (attr, recipeDataId, str(val))
                else:
                    SQL = "insert into SfcRecipeDataValue (recipeDataId, FloatValue) values (%d, NULL)" % (recipeDataId)
                print SQL
                valueId = system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
                valueIds.append(valueId)

            SQL = "Insert into SfcRecipeDataOutput (RecipeDataId, ValueTypeId, OutputTypeId, OutputValueId, TargetValueId, PVValueId, Tag, Download, Timing, MaxTiming, WriteConfirm) "\
                "values (%d, %d, %d, %d, %d, %d, '%s', %d, %f, %f, %d)" \
                % (recipeDataId, valueTypeId, outputTypeId, valueIds[0], valueIds[1], valueIds[2], tag, download, timing, maxTiming, writeConfirm)            
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)
        else:
            print "Updating an Output..."
            recipeDataId = rootContainer.recipeDataId
            updateRecipeData(key, description, advice, label, units, recipeDataId, tx)

            SQL = "Update SfcRecipeDataOutput set ValueTypeId=%d, OutputTypeId=%d, Tag='%s', Download=%d, Timing=%f, MaxTiming=%f, WriteConfirm=%d "\
                "where RecipeDataId = %d" % (valueTypeId, outputTypeId, tag, download, timing, maxTiming, writeConfirm, recipeDataId)
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)
                       
            ds = rootContainer.outputDataset
            valueId = ds.getValueAt(0,"OutputValueId")
            if valueType == "Float":
                val = outputContainer.getComponent("Output Float Value").floatValue
            elif valueType == "Integer":
                val = outputContainer.getComponent("Output Integer Value").intValue
            elif valueType == "String":
                val = outputContainer.getComponent("Output String Value").text
            elif valueType == "Boolean":
                val = outputContainer.getComponent("Output Boolean Value").selected
                val = toBit(val)
            updateRecipeDataValue(valueId, valueType, val, tx)

        system.db.commitTransaction(tx)
        system.db.closeTransaction(tx) 
    except:
        errorTxt = catchError("ils.sfc.recipeData.visionEditor.saveOutput", "Caught an error, rolling back transactions")
        system.db.rollbackTransaction(tx)
        system.db.closeTransaction(tx)
        raise Exception("Save Recipe Data Exception: %s", errorTxt)
    
    closeAndOpenBrowser(event)


def saveOutputRamp(event):
    print "Saving an Output Ramp"
    
    rootContainer = event.source.parent.parent
    
    if not(validateKey(rootContainer.getComponent("Key"))):
        return

    db = getDatabaseClient()
    recipeDataId = rootContainer.recipeDataId
    stepId = rootContainer.stepId
    folderId = rootContainer.recipeDataFolderId
    key = rootContainer.getComponent("Key").text
    description = rootContainer.getComponent("Description").text
    description = escapeSqlQuotes(description)
    advice = rootContainer.getComponent("Advice").text
    advice = escapeSqlQuotes(advice)
    label = rootContainer.getComponent("Label").text
    label = escapeSqlQuotes(label)
    units = rootContainer.getComponent("Units Dropdown").selectedStringValue
    outputContainer=rootContainer.getComponent("Output Ramp Container")
    
    outputType = outputContainer.getComponent("Output Type Dropdown").selectedStringValue
    outputTypeId = outputContainer.getComponent("Output Type Dropdown").selectedValue
    tag = outputContainer.getComponent("Tag").text
    download = outputContainer.getComponent("Download").selected
    download=toBit(download)
    timing = outputContainer.getComponent("Timing").floatValue
    maxTiming = outputContainer.getComponent("Max Timing").floatValue
    writeConfirm = outputContainer.getComponent("Write Confirm").selected
    writeConfirm=toBit(writeConfirm)
    
    rampTime = outputContainer.getComponent("Ramp Time").floatValue
    updateFrequency = outputContainer.getComponent("Update Frequency").floatValue
    
    # For now, the valueType of an output is always a Float
    valueType = outputContainer.getComponent("Value Type Dropdown").selectedStringValue
    valueTypeId = outputContainer.getComponent("Value Type Dropdown").selectedValue
    
    tx = system.db.beginTransaction(db)
    
    try:
        if recipeDataId < 0:
            print "Inserting a new Output Ramp..."
            recipeDataType = rootContainer.recipeDataType
            recipeDataTypeId = fetchRecipeDataTypeId(recipeDataType, db)
            recipeDataId = insertRecipeData(stepId, key, recipeDataTypeId, description, advice, label, units, folderId, tx)
            rootContainer.recipeDataId = recipeDataId
            
            valueIds=[]
            for i in [0,1,2]:
                # TargetValue and PV Value are dynamic values that cannot be edited.
                if i == 0:
                    attr = valueType + "Value"
                    if valueType == 'String':
                        val = outputContainer.getComponent("Output String Value").text
                        SQL = "insert into SfcRecipeDataValue (recipeDataId, %s) values (%d, '%s')" % (attr, recipeDataId, val)
                    else:
                        if valueType == 'Float':
                            val = outputContainer.getComponent("Output Float Value").floatValue
                        elif valueType == 'Integer':
                            val = outputContainer.getComponent("Output Integer Value").intValue
                        elif valueType == 'Boolean':
                            val = outputContainer.getComponent("Output Boolean Value").selected
                            val = toBit(val)
                        SQL = "insert into SfcRecipeDataValue (recipeDataId, %s) values (%d, %s)" % (attr, recipeDataId, str(val))
                else:
                    SQL = "insert into SfcRecipeDataValue (recipeDataId, FloatValue) values (%d, NULL)" % (recipeDataId)
                print SQL
                valueId = system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
                valueIds.append(valueId)

            SQL = "Insert into SfcRecipeDataOutput (RecipeDataId, ValueTypeId, OutputTypeId, OutputValueId, TargetValueId, PVValueId, Tag, Download, Timing, MaxTiming, WriteConfirm) "\
                "values (%d, %d, %d, %d, %d, %d, '%s', %d, %f, %f, %d)" \
                % (recipeDataId, valueTypeId, outputTypeId, valueIds[0], valueIds[1], valueIds[2], tag, download, timing, maxTiming, writeConfirm)            
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)
            
            SQL = "Insert into SfcRecipeDataOutputRamp (RecipeDataId, RampTimeMinutes, UpdateFrequencySeconds) "\
                "values (%d, %f, %f)" \
                % (recipeDataId, rampTime, updateFrequency)            
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)
        else:
            print "Updating an existing Output Ramp..."
            recipeDataId = rootContainer.recipeDataId
            updateRecipeData(key, description, advice, label, units, recipeDataId, tx)

            SQL = "Update SfcRecipeDataOutput set ValueTypeId=%d, OutputTypeId=%d, Tag='%s', Download=%d, Timing=%f, MaxTiming=%f, WriteConfirm=%d "\
                "where RecipeDataId = %d" % (valueTypeId, outputTypeId, tag, download, timing, maxTiming, writeConfirm, recipeDataId)
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)

            SQL = "Update SfcRecipeDataOutputRamp set RampTimeMinutes=%f, UpdateFrequencySeconds=%f where RecipeDataId = %d" % (rampTime, updateFrequency, recipeDataId)
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)

            ds = rootContainer.outputRampDataset
            valueId = ds.getValueAt(0,"OutputValueId")
            if valueType == "Float":
                val = outputContainer.getComponent("Output Float Value").floatValue
            elif valueType == "Integer":
                val = outputContainer.getComponent("Output Integer Value").intValue
            elif valueType == "String":
                val = outputContainer.getComponent("Output String Value").text
            elif valueType == "Boolean":
                val = outputContainer.getComponent("Output Boolean Value").selected
                val = toBit(val)
            updateRecipeDataValue(valueId, valueType, val, tx)

        system.db.commitTransaction(tx)
        system.db.closeTransaction(tx) 
    except:
        errorTxt = catchError("ils.sfc.recipeData.visionEditor.saveOutputRamp", "Caught an error, rolling back transactions")
        system.db.rollbackTransaction(tx)
        system.db.closeTransaction(tx) 
        raise Exception("Save Recipe Data Exception: %s", errorTxt)
    
    closeAndOpenBrowser(event)


def saveTimerValue(event):
    print "Saving a timer value"
    
    rootContainer = event.source.parent.parent
    
    if not(validateKey(rootContainer.getComponent("Key"))):
        return

    db = getDatabaseClient()
    recipeDataId = rootContainer.recipeDataId
    stepId = rootContainer.stepId
    folderId = rootContainer.recipeDataFolderId
    key = rootContainer.getComponent("Key").text
    description = rootContainer.getComponent("Description").text
    description = escapeSqlQuotes(description)
    advice = rootContainer.getComponent("Advice").text
    advice = escapeSqlQuotes(advice)
    label = rootContainer.getComponent("Label").text
    label = escapeSqlQuotes(label)
    units = rootContainer.getComponent("Units Dropdown").selectedStringValue
    timerContainer=rootContainer.getComponent("Timer Container")
    
    tx = system.db.beginTransaction(db)
    
    try:
        if recipeDataId < 0:
            print "Inserting a timer..."
            recipeDataType = rootContainer.recipeDataType
            recipeDataTypeId = fetchRecipeDataTypeId(recipeDataType, db)
            recipeDataId = insertRecipeData(stepId, key, recipeDataTypeId, description, advice, label, units, folderId, tx)
            rootContainer.recipeDataId = recipeDataId
            
            val = timerContainer.getComponent("Popup Calendar").text
            SQL = "Insert into SfcRecipeDataTimer (RecipeDataId, StartTime) values (%d, '%s')" % (recipeDataId, val)
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)
        else:
            print "Updating a timer..."
            recipeDataId = rootContainer.recipeDataId
            updateRecipeData(key, description, advice, label, units, recipeDataId, tx)
            
            val = timerContainer.getComponent("Popup Calendar").text
            SQL = "Update SfcRecipeDataTimer set StartTime='%s' where RecipeDataId = %d" % (val, recipeDataId)
            
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)

        system.db.commitTransaction(tx)
        system.db.closeTransaction(tx) 
    except:
        errorTxt = catchError("ils.sfc.recipeData.visionEditor.saveTimer", "Caught an error, rolling back transactions")
        system.db.rollbackTransaction(tx)
        system.db.closeTransaction(tx)
        raise Exception("Save Recipe Data Exception: %s", errorTxt)
    
    closeAndOpenBrowser(event)

def saveSqcValue(event):
    print "Saving a SQC value"
    
    rootContainer = event.source.parent.parent
    
    if not(validateKey(rootContainer.getComponent("Key"))):
        return

    db = getDatabaseClient()
    recipeDataId = rootContainer.recipeDataId
    stepId = rootContainer.stepId
    folderId = rootContainer.recipeDataFolderId
    key = rootContainer.getComponent("Key").text
    description = rootContainer.getComponent("Description").text
    description = escapeSqlQuotes(description)
    advice = rootContainer.getComponent("Advice").text
    advice = escapeSqlQuotes(advice)
    label = rootContainer.getComponent("Label").text
    label = escapeSqlQuotes(label)
    units = rootContainer.getComponent("Units Dropdown").selectedStringValue
     
    sqcContainer=rootContainer.getComponent("SQC Container")
    highLimit = sqcContainer.getComponent("High Limit").floatValue
    targetValue = sqcContainer.getComponent("Target Value").floatValue
    lowLimit = sqcContainer.getComponent("Low Limit").floatValue
    
    tx = system.db.beginTransaction(db)
    
    try:
        if recipeDataId < 0:
            print "Inserting a SQC..."
            recipeDataType = rootContainer.recipeDataType
            recipeDataTypeId = fetchRecipeDataTypeId(recipeDataType, db)
            recipeDataId = insertRecipeData(stepId, key, recipeDataTypeId, description, advice, label, units, folderId, tx)
            rootContainer.recipeDataId = recipeDataId
            
            SQL = "Insert into SfcRecipeDataSQC (RecipeDataId, HighLimit, TargetValue, LowLimit) values (%d, %f, %f, %f)" % (recipeDataId, highLimit, targetValue, lowLimit)
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)
        else:
            print "Updating a SQC..."
            recipeDataId = rootContainer.recipeDataId
            updateRecipeData(key, description, advice, label, units, recipeDataId, tx)
            
            SQL = "Update SfcRecipeDataSQC set HighLimit=%f, TargetValue=%f, LowLimit=%f where RecipeDataId = %d" % (highLimit, targetValue, lowLimit, recipeDataId)
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)

        system.db.commitTransaction(tx)
        system.db.closeTransaction(tx) 
    except:
        errorTxt = catchError("ils.sfc.recipeData.visionEditor.saveTimer", "Caught an error, rolling back transactions")
        system.db.rollbackTransaction(tx)
        system.db.closeTransaction(tx)
        raise Exception("Save Recipe Data Exception: %s", errorTxt)
    
    closeAndOpenBrowser(event)


def saveRecipe(event):
    print "Saving a recipe"
    
    rootContainer = event.source.parent.parent
    
    if not(validateKey(rootContainer.getComponent("Key"))):
        return

    db = getDatabaseClient()
    recipeDataId = rootContainer.recipeDataId
    stepId = rootContainer.stepId
    folderId = rootContainer.recipeDataFolderId
    key = rootContainer.getComponent("Key").text
    description = rootContainer.getComponent("Description").text
    description = escapeSqlQuotes(description)
    advice = rootContainer.getComponent("Advice").text
    advice = escapeSqlQuotes(advice)
    label = rootContainer.getComponent("Label").text
    label = escapeSqlQuotes(label)
    units = rootContainer.getComponent("Units Dropdown").selectedStringValue
    container=rootContainer.getComponent("Recipe Container")
    
    tx = system.db.beginTransaction(db)
    
    try:
        presentationOrder = container.getComponent("Presentation Order").intValue
        storeTag = container.getComponent("Store Tag").text
        compareTag = container.getComponent("Compare Tag").text
        modeAttribute = container.getComponent("Mode Attribute").text
        modeValue = container.getComponent("Mode Value").text
        changeLevel = container.getComponent("Mode Attribute").text
        recommendedValue = container.getComponent("Recommended Value").text
        lowLimit = container.getComponent("Low Limit").text
        highLimit = container.getComponent("High Limit").text
        
        if recipeDataId < 0:
            print "Inserting a recipe..."
            recipeDataType = rootContainer.recipeDataType
            recipeDataTypeId = fetchRecipeDataTypeId(recipeDataType, db)
            recipeDataId = insertRecipeData(stepId, key, recipeDataTypeId, description, advice, label, units, folderId, tx)
            rootContainer.recipeDataId = recipeDataId
            
            SQL = "Insert into SfcRecipeDataRecipe (RecipeDataId, PresentationOrder, StoreTag, CompareTag, ModeAttribute, ModeValue, ChangeLevel, RecommendedValue, LowLimit, HighLimit) "\
                "values (%d, %d, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % \
                (recipeDataId, presentationOrder, storeTag, compareTag, modeAttribute, modeValue, changeLevel, recommendedValue, lowLimit, highLimit)
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)
        else:
            print "Updating a recipe..."
            recipeDataId = rootContainer.recipeDataId
            updateRecipeData(key, description, advice, label, units, recipeDataId, tx)

            SQL = "Update SfcRecipeDataRecipe set PresentationOrder=%d, StoreTag='%s', CompareTag='%s', ModeAttribute='%s', ModeValue='%s', ChangeLevel='%s', "\
                "RecommendedValue='%s', LowLimit='%s', HighLimit='%s' where RecipeDataId = %d" % \
                (presentationOrder, storeTag, compareTag, modeAttribute, modeValue, changeLevel, recommendedValue, lowLimit, highLimit, recipeDataId)
            
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)

        system.db.commitTransaction(tx)
        system.db.closeTransaction(tx) 
    except:
        errorTxt = catchError("ils.sfc.recipeData.visionEditor.saveRecipe", "Caught an error, rolling back transactions")
        system.db.rollbackTransaction(tx)
        system.db.closeTransaction(tx)
        raise Exception("Save Recipe Data Exception: %s", errorTxt)

    closeAndOpenBrowser(event)

'''
This code is shared between an array and a Keyed array, there are seperate containers on the window.
'''
def saveArray(event):
    print "In %s.saveArray(), saving an array...." % (__name__)
    
    rootContainer = event.source.parent.parent
    
    if not(validateKey(rootContainer.getComponent("Key"))):
        return

    db = getDatabaseClient()
    recipeDataId = rootContainer.recipeDataId
    stepId = rootContainer.stepId
    folderId = rootContainer.recipeDataFolderId
    key = rootContainer.getComponent("Key").text
    description = rootContainer.getComponent("Description").text
    description = escapeSqlQuotes(description)
    advice = rootContainer.getComponent("Advice").text
    advice = escapeSqlQuotes(advice)
    label = rootContainer.getComponent("Label").text
    label = escapeSqlQuotes(label)
    units = rootContainer.getComponent("Units Dropdown").selectedStringValue
    
    recipeDataType = rootContainer.recipeDataType
    arrayContainer=rootContainer.getComponent("Array Container")
        
    valueType = arrayContainer.getComponent("Value Type Dropdown").selectedStringValue
    valueTypeId = arrayContainer.getComponent("Value Type Dropdown").selectedValue
    
    indexKey = arrayContainer.getComponent("Index Key Dropdown").selectedStringValue
    indexKeyId = arrayContainer.getComponent("Index Key Dropdown").selectedValue
    
    print "Index Key: ", indexKey
    print "Index Key Id: ", indexKeyId
    
    tx = system.db.beginTransaction(db)
    
    try:
        if recipeDataId < 0:
            print "Inserting a new array..."
            recipeDataType = rootContainer.recipeDataType
            recipeDataTypeId = fetchRecipeDataTypeId(recipeDataType, db)
            recipeDataId = insertRecipeData(stepId, key, recipeDataTypeId, description, advice, label, units, folderId, tx)
            rootContainer.recipeDataId = recipeDataId
            
            if indexKeyId <= 0:
                indexKeyId = None
                
            SQL = "Insert into SfcRecipeDataArray (RecipeDataId, ValueTypeId, IndexKeyId) values (?, ?, ?)"
            args = [recipeDataId, valueTypeId, indexKeyId]
            
            system.db.runPrepUpdate(SQL, args, tx=tx)
        else:
            print "Updating an array..."
            recipeDataId = rootContainer.recipeDataId
            updateRecipeData(key, description, advice, label, units, recipeDataId, tx)

            if indexKeyId <= 0:
                indexKeyId = None

            SQL = "Update SfcRecipeDataArray set ValueTypeId=?, IndexKeyId=? where RecipeDataId = ?" 
            print SQL
            args = [valueTypeId, indexKeyId, recipeDataId]
            system.db.runPrepUpdate(SQL, args, tx=tx)

        # Now deal with the array.  First delete all of the rows than insert new ones.  There are no foreign keys or ids so this should be fast and easy.
        # There is a cascade delete to the SFcRecipeDataValue table, but the PK is there, not here
        print "...updating the array elements..."
        SQL = "select ValueId from SfcRecipeDataArrayElement where RecipeDataId = %d" % (recipeDataId)
        pds = system.db.runQuery(SQL, tx=tx)
        
        SQL = "delete from SfcRecipeDataArrayElement where RecipeDataId = %d" % (recipeDataId)
        cnt = system.db.runUpdateQuery(SQL, tx=tx)
        print "...deleted %d array elements from SfcRecipeDataArrayElement..." % (cnt)
        
        rows=0
        for record in pds:
            SQL = "delete from SfcRecipeDataValue where valueId = %d" % record["ValueId"]
            cnt = system.db.runUpdateQuery(SQL, tx=tx)
            rows = rows + cnt
        print "...deleted %d array elements..." % (rows)
        
        table = arrayContainer.getComponent("Array Table")
        ds = table.data
        for row in range(ds.rowCount):
            print"---- inserting a row ---"
            if valueType == 'String':
                val = ds.getValueAt(row, "StringValue")
                SQL = "insert into SfcRecipeDataValue (RecipeDataId, StringValue) values (%d, '%s')" % (recipeDataId, val)
            else:
                valueColumnName = valueType + "Value"
                val = ds.getValueAt(row, valueColumnName)

                if valueType == "Boolean":
                    val = toBit(val)
                SQL = "insert into SfcRecipeDataValue (RecipeDataId, %s) values (%d, '%s')" % (valueColumnName, recipeDataId, val)
          
            valueId=system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
            
            SQL = "insert into SfcRecipeDataArrayElement (RecipeDataId, ArrayIndex, ValueId) values (%d, %d, %d)" % (recipeDataId, row, valueId)
            system.db.runUpdateQuery(SQL, tx=tx)

        system.db.commitTransaction(tx)
        system.db.closeTransaction(tx) 
    except:
        errorTxt = catchError("ils.sfc.recipeData.visionEditor.saveArray", "Caught an error, rolling back transactions")
        system.db.rollbackTransaction(tx)
        system.db.closeTransaction(tx)
        raise Exception("Save Recipe Data Exception: %s", errorTxt)

    closeAndOpenBrowser(event)

def saveMatrix(event):
    print "Saving an matrix...."
    
    rootContainer = event.source.parent.parent

    if not(validateKey(rootContainer.getComponent("Key"))):
        return

    db = getDatabaseClient()
    recipeDataId = rootContainer.recipeDataId
    stepId = rootContainer.stepId
    folderId = rootContainer.recipeDataFolderId
    key = rootContainer.getComponent("Key").text    
    description = rootContainer.getComponent("Description").text
    description = escapeSqlQuotes(description)
    advice = rootContainer.getComponent("Advice").text
    advice = escapeSqlQuotes(advice)
    label = rootContainer.getComponent("Label").text
    label = escapeSqlQuotes(label)
    units = rootContainer.getComponent("Units Dropdown").selectedStringValue
    
    recipeDataType = rootContainer.recipeDataType
    if recipeDataId > 0:
        if not(checkRecipeDataId(recipeDataId, recipeDataType, db)):
            recipeDataId = -1
        
    matrixContainer=rootContainer.getComponent("Matrix Container")

    valueType = matrixContainer.getComponent("Value Type Dropdown").selectedStringValue
    valueTypeId = matrixContainer.getComponent("Value Type Dropdown").selectedValue
    
    rowIndexKeyId = matrixContainer.getComponent("Row Index Key Dropdown").selectedValue
    columnIndexKeyId = matrixContainer.getComponent("Column Index Key Dropdown").selectedValue
    
    table = matrixContainer.getComponent("Matrix Table")
    ds = table.data
    rows = ds.rowCount
    columns = ds.columnCount - 1
    
    tx = system.db.beginTransaction(db)
    
    try:
        if recipeDataId < 0:
            print "Inserting a new matrix..."
            recipeDataType = rootContainer.recipeDataType
            recipeDataTypeId = fetchRecipeDataTypeId(recipeDataType, db)
            recipeDataId = insertRecipeData(stepId, key, recipeDataTypeId, description, advice, label, units, folderId, tx)
            rootContainer.recipeDataId = recipeDataId
            
            SQL = "Insert into SfcRecipeDataMatrix (RecipeDataId, ValueTypeId, Rows, Columns, RowIndexKeyId, ColumnIndexKeyId) values (?, ?, ?, ?, ?, ?)"
            args = [recipeDataId, valueTypeId, rows, columns]
            
            if rowIndexKeyId > 0:
                args.append(rowIndexKeyId)
            else:
                args.append(None)
            
            if columnIndexKeyId > 0:
                args.append(columnIndexKeyId)
            else:
                args.append(None)

            system.db.runPrepUpdate(SQL, args, tx=tx)
        else:
            print "Updating an matrix..."
            recipeDataId = rootContainer.recipeDataId
            updateRecipeData(key, description, advice, label, units, recipeDataId, tx)

            rowIndexKeyId = matrixContainer.getComponent("Row Index Key Dropdown").selectedValue
            if rowIndexKeyId <= 0:
                rowIndexKeyId = None
                
            columnIndexKeyId = matrixContainer.getComponent("Column Index Key Dropdown").selectedValue
            if columnIndexKeyId <= 0:
                columnIndexKeyId = None
                
            SQL = "Update SfcRecipeDataMatrix set ValueTypeId=?, RowIndexKeyId=?, ColumnIndexKeyId=? where RecipeDataId = ?"
            args = [valueTypeId, rowIndexKeyId, columnIndexKeyId, recipeDataId]
            print SQL, args
            system.db.runPrepUpdate(SQL, args, tx=tx)

        # Now deal with the matrix.  First delete all of the rows than insert new ones.  There are no foreign keys or ids so this should be fast and easy.
        # There is a cascade delete to the SFcRecipeDataValue table, but the PK is there, not here
        # First delete everything...
        SQL = "select ValueId from SfcRecipeDataMatrixElement where RecipeDataId = %d" % (recipeDataId)
        pds = system.db.runQuery(SQL, tx=tx)
        
        SQL = "delete from SfcRecipeDataMatrixElement where RecipeDataId = %d" % (recipeDataId)
        cnt = system.db.runUpdateQuery(SQL, tx=tx)
        print "...deleted %d matrix elements..." % (rows)
        
        rows=0
        cnt = 0
        for record in pds:
            SQL = "delete from SfcRecipeDataValue where valueId = %d" % record["ValueId"]
            cnt = system.db.runUpdateQuery(SQL, tx=tx)
            rows = rows + cnt
        print "...deleted %d data value elements..." % (rows)
        
        # Now insert everything...
        for rowIndex in range(ds.rowCount):
            for columnIndex in range(ds.columnCount - 1):
                val = ds.getValueAt(rowIndex, columnIndex + 1) # The columns are offset by 1 because the key is in column 0
                print "(%d, %d) = %s" % (rowIndex, columnIndex, str(val))
                SQL = "insert into SfcRecipeDataValue (RecipeDataId, %s) values (%d, '%s')" % ("FloatValue", recipeDataId, val)
                print SQL
                valueId=system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
                
                print "Inserting %s at  (%d, %d)..." % (str(val), rowIndex, columnIndex)
                SQL = "insert into SfcRecipeDataMatrixElement (RecipeDataId, RowIndex, ColumnIndex, ValueId) values (%d, %d, %d, %d)" % (recipeDataId, rowIndex, columnIndex, valueId)
                system.db.runUpdateQuery(SQL, tx=tx)

        system.db.commitTransaction(tx)
        system.db.closeTransaction(tx) 
    except:
        errorTxt = catchError("ils.sfc.recipeData.visionEditor.saveMatrix", "Caught an error, rolling back transactions")
        system.db.rollbackTransaction(tx)
        system.db.closeTransaction(tx) 
        raise Exception("Save Recipe Data Exception: %s", errorTxt)

    closeAndOpenBrowser(event)

def updateRecipeDataValue(valueId, valueType, val, tx):
    if valueType == "Float":
        SQL = "Update SfcRecipeDataValue set IntegerValue=NULL, FloatValue=%f, StringValue=NULL, BooleanValue=NULL where ValueId = %d" % (val, valueId)
    elif valueType == "Integer":
        SQL = "Update SfcRecipeDataValue set IntegerValue=%d, FloatValue=NULL, StringValue=NULL, BooleanValue=NULL where ValueId = %d" % (val, valueId)
    elif valueType == "String":
        SQL = "Update SfcRecipeDataValue set IntegerValue=NULL, FloatValue=NULL, StringValue='%s', BooleanValue=NULL where ValueId = %d" % (val, valueId)
    elif valueType == "Boolean":
        val = toBit(val)
        SQL = "Update SfcRecipeDataValue set IntegerValue=NULL, FloatValue=NULL, StringValue=NULL, BooleanValue=%d where ValueId = %d" % (val, valueId)

    print SQL
    system.db.runUpdateQuery(SQL, tx=tx)
    
def insertRecipeData(stepId, key, recipeDataTypeId, description, advice, label, units, folderId, tx):
    if folderId < 0:
        SQL = "insert into SfcRecipeData (StepId, RecipeDataKey, RecipeDataTypeId, Description, Advice, Label, Units) "\
            "values (%s, '%s', %d, '%s', '%s', '%s', '%s')" % (stepId, key, recipeDataTypeId, description, advice, label, units)
    else:
        SQL = "insert into SfcRecipeData (StepId, RecipeDataKey, RecipeDataTypeId, Description, Advice, Label, Units, RecipeDataFolderId) "\
            "values (%s, '%s', %d, '%s', '%s', '%s', '%s', %s)" % (stepId, key, recipeDataTypeId, description, advice, label, units, str(folderId))

    print SQL
    recipeDataId = system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
    return recipeDataId

def updateRecipeData(key, description, advice, label, units, recipeDataId, tx):
    SQL = "update SfcRecipeData set RecipeDataKey='%s', Description='%s', Advice='%s', Label = '%s', Units='%s' where RecipeDataId = %d " % (key, description, advice, label, units, recipeDataId)
    print SQL
    system.db.runUpdateQuery(SQL, tx=tx)
    
def checkRecipeDataId(recipeDataId, recipeDataType, db):
    '''
    If there is some invalid data in the form when creating a new recipe data entity then the database transactions will be rolled back but that is AFTER the new recipe data id has been
    returned and put in the form so that if they correct the error and press OK then we think we are updating an existing recipe entity rather than creating a new one.  This will verify that 
    the recipe entity really does exist. 
    '''
    SQL = "select count(*) from SFCRecipeData RD, SFCRecipeDataType RDT " \
        "where RD.RecipeDataTypeId = RDT.RecipeDataTypeId " \
        "and RDT.RecipeDataType = '%s' " \
        "and RD.recipeDataId = %s " % (recipeDataType, str(recipeDataId))
    rows = system.db.runScalarQuery(SQL, database=db)
    if rows == 1:
        return True
    
    return False 

def closeAndOpenBrowser(event):
    '''
    This can be called from two different windows - the SFC Hierarchy Browser and the SFC Viewer so we can't 
    hard code what to open.  If it was open then it should come back to the top.
    
    system.nav.openWindow("SFC/SfcHierarchyWithRecipeBrowser")
    '''
    system.nav.closeParentWindow(event)