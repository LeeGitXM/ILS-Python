'''
Created on Feb 1, 2017

@author: phass
'''

import system, string
from ils.common.cast import toBit
from ils.common.error import catch
from ils.sfc.recipeData.core import fetchRecipeDataTypeId, fetchValueTypeId
log=system.util.getLogger("com.ils.sfc.visionEditor")

from ils.sfc.recipeData.constants import ARRAY, INPUT, MATRIX, OUTPUT, RECIPE, SIMPLE_VALUE, TIMER

    
# The chart path is passed as a property when the window is opened.  Look up the chartId, refresh the Steps table and clear the RecipeData Table
def internalFrameOpened(rootContainer, db=""):
    print "In internalFrameOpened"
    rootContainer.initialized = False
    
    recipeDataId = rootContainer.getPropertyValue("recipeDataId")
    recipeDataType = rootContainer.getPropertyValue("recipeDataType")
    
    if recipeDataId > 0:
        
        if recipeDataType == SIMPLE_VALUE:
            print "Fetching a simple value..."
            SQL = "select * from SfcRecipeDataSimpleValueView where recipeDataId = %s" % (recipeDataId)
            pds = system.db.runQuery(SQL, db)
            if len(pds) <> 1:
                raise ValueError, "Unable to fetch a Simple Value recipe data with id: %s" % (recipeDataId)
            record = pds[0]
            rootContainer.simpleValueDataset = pds

        elif recipeDataType == ARRAY:
            print "Fetching an Array"
            SQL = "select * from SfcRecipeDataArrayView where recipeDataId = %s" % (recipeDataId)
            pds = system.db.runQuery(SQL, db)
            if len(pds) <> 1:
                raise ValueError, "Unable to fetch an Array recipe data with id: %s" % (recipeDataId)
            record = pds[0]
            rootContainer.arrayDataset = pds
            
            # Set the visibility of the values columns so only the one for the target valueType is shown
            valueType = record["ValueType"]
            setArrayTableColumnVisibility(rootContainer, valueType)

            indexRecipeDataId = record["IndexRecipeDataId"]
            if indexRecipeDataId == None:
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
                SQL = "select * from SfcRecipeDataArrayElementView where recipeDataId = %s order by ArrayIndex" % (indexRecipeDataId)
                pds = system.db.runQuery(SQL, db)
                dsKey = system.dataset.toDataSet(pds)
                
                # They had better both have the same length
                if ds.rowCount != dsKey.rowCount:
                    print "AAAAgh they are not the same length"
                
                header = ["Key", "FloatValue", "IntegerValue", "StringValue", "BooleanValue"]
                data = []
                for i in range(dsKey.rowCount):
                    if i <= ds.rowCount:
                        key = dsKey.getValueAt(i, "StringValue")
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
                raise ValueError, "Unable to fetch a Matrix recipe data with id: %s" % (recipeDataId)
            record = pds[0]
            rootContainer.matrixDataset = pds
            numRows = record["Rows"]
            numColumns = record["Columns"]
            print "...the matrix is %d X %d..." % (numRows, numColumns)
            
            # Set the visibility of the values columns so only the one for the target valueType is shown
            valueType = record["ValueType"]
            setArrayTableColumnVisibility(rootContainer, valueType)
            
            rowIndexRecipeDataId = record["RowIndexRecipeDataId"]
            columnIndexRecipeDataId = record["ColumnIndexRecipeDataId"]
            
            if rowIndexRecipeDataId == None and columnIndexRecipeDataId == None:
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
                
                # Fetch the matrix data
                SQL = "select * from SfcRecipeDataMatrixElementView where recipeDataId = %s order by RowIndex, ColumnIndex" % (recipeDataId)
                pds = system.db.runQuery(SQL, db)
                ds = system.dataset.toDataSet(pds)
                rootContainer.matrixValuesDataset = pds
                
                # Now Fetch the row Key
                if rowIndexRecipeDataId != None:
                    print "Fetching the row key..."
                    SQL = "select * from SfcRecipeDataArrayElementView where recipeDataId = %s order by ArrayIndex" % (rowIndexRecipeDataId)
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
                            rowLabels.append(dsRowKey.getValueAt(i, "StringValue"))
                            
                # Now Fetch the array Key
                if columnIndexRecipeDataId != None:
                    print "Fetching the column key..."
                    SQL = "select * from SfcRecipeDataArrayElementView where recipeDataId = %s order by ArrayIndex" % (columnIndexRecipeDataId)
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
                            columnLabels.append(dsColumnKey.getValueAt(i, "StringValue"))
                            
                print "The row labels are: ", rowLabels
                print "The column labels are: ", columnLabels
                
            container = rootContainer.getComponent("Matrix Container")
            updateMatrixTable(container, pds, rowLabels, columnLabels)

            
        elif recipeDataType == INPUT:
            print "Fetching an Input"
            SQL = "select * from SfcRecipeDataInputView where recipeDataId = %s" % (recipeDataId)
            pds = system.db.runQuery(SQL, db)
            if len(pds) <> 1:
                raise ValueError, "Unable to fetch an Input recipe data with id: %s" % (recipeDataId)
            record = pds[0]
            rootContainer.inputDataset = pds

        elif recipeDataType == OUTPUT:
            print "Fetching an Output"
            SQL = "select * from SfcRecipeDataOutputView where recipeDataId = %s" % (recipeDataId)
            pds = system.db.runQuery(SQL, db)
            if len(pds) <> 1:
                raise ValueError, "Unable to fetch an Output recipe data with id: %s" % (recipeDataId)
            record = pds[0]
            rootContainer.outputDataset = pds
        
        elif recipeDataType == RECIPE:
            print "Fetching a Recipe"
            SQL = "select * from SfcRecipeDataRecipeView where recipeDataId = %s" % (recipeDataId)
            pds = system.db.runQuery(SQL, db)
            if len(pds) <> 1:
                raise ValueError, "Unable to fetch a Recipe recipe data with id: %s" % (recipeDataId)
            record = pds[0]
            rootContainer.recipeDataset = pds

        elif recipeDataType == TIMER:
            print "Fetching a Timer"
            SQL = "select * from SfcRecipeDataTimerView where recipeDataId = %s" % (recipeDataId)
            pds = system.db.runQuery(SQL, db)
            if len(pds) <> 1:
                raise ValueError, "Unable to fetch a Timer recipe data with id: %s" % (recipeDataId)
            record = pds[0]
            rootContainer.timerDataset = pds

        else:
            raise ValueError, "Unexpected recipe data type <%s>" % (recipeDataType)

        rootContainer.description = record["Description"]
        rootContainer.label = record["Label"]
        
        units = record["Units"]
        if units <> None:
            units = string.upper(units)
        rootContainer.units = units
        print "Setting the units to: ", units
        
    else:
        if recipeDataType == SIMPLE_VALUE:
            print "Initializing a simple value..."
            ds = rootContainer.simpleValueDataset
            ds = system.dataset.setValue(ds, 0, "RecipeDataKey", "")
            ds = system.dataset.setValue(ds, 0, "Description", "")
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
            ds = system.dataset.setValue(ds, 0, "RowIndexKey", None)
            ds = system.dataset.setValue(ds, 0, "RowIndexRecipeDataId", None)
            ds = system.dataset.setValue(ds, 0, "ColumnIndexKey", None)
            ds = system.dataset.setValue(ds, 0, "ColumnIndexRecipeDataId", None)
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
    indexKey = combo.selectedStringValue
    indexRecipeDataId = combo.selectedValue
    
    print "...the indexKey is: ", indexKey
    
    if indexRecipeDataId == -1:
        print "The user has changed the array from a keyed to unkeyed"
        ds = table.data

        for i in range(0, ds.rowCount):
            ds = system.dataset.setValue(ds, i, 0, str(i))

        table.data = ds
        
    else:
        SQL = "select StringValue From SfcRecipeDataArrayElementView where RecipeDataId = %d order by ArrayIndex" % (indexRecipeDataId)
        pds = system.db.runQuery(SQL, db)
        
        print "...there are %d elements in the key..." % (len(pds))
        
        ds = rootContainer.arrayValuesDataset
        rowsInArray = ds.rowCount
        
        i = 0
        for record in pds:
            key = record["StringValue"]
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
        column = record["ColumnIndex"]
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
        
        SQL = "select StringValue From SfcRecipeDataArrayElementView where RecipeDataId = %d order by ArrayIndex" % (indexRecipeDataId)
        pds = system.db.runQuery(SQL, db)
        
        ds = table.data
        rowsInArray = ds.rowCount
        
        i = 0
        for record in pds:
            key = record["StringValue"]
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
        SQL = "select StringValue From SfcRecipeDataArrayElementView where RecipeDataId = %d order by ArrayIndex" % (indexRecipeDataId)
        pds = system.db.runQuery(SQL, db)
        header = ["row"]
        for record in pds:
            key = record["StringValue"]
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
    print "Refreshing the combo boxes"
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
        indexKey = ds.getValueAt(0,"IndexKey")
        if rows == 0:
            combo.selectedValue = -1
        else:
            combo.selectedStringValue = indexKey
    
    elif recipeDataType == MATRIX:
        # Matrix Combos
        print "Updating the matrix combo boxes..."
        container = rootContainer.getComponent("Matrix Container")
        
        combo = container.getComponent("Row Index Key Dropdown")
        addUnselectionChoice(combo)
        
        ds = rootContainer.matrixDataset
        rows = ds.rowCount  # Not sure what this is suppossed to do
        indexKey = ds.getValueAt(0,"RowIndexKey")
        print "Setting the row index key to: ", indexKey
        if rows == 0:
            combo.selectedValue = -1
        else:
            combo.selectedStringValue = indexKey
        
        combo = container.getComponent("Column Index Key Dropdown")
        addUnselectionChoice(combo)
        
        indexKey = ds.getValueAt(0,"ColumnIndexKey")
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


def saveSimpleValue(rootContainer, db=""):
    print "Saving a simple value"

    recipeDataId = rootContainer.recipeDataId
    stepId = rootContainer.stepId
    key = rootContainer.getComponent("Key").text
    description = rootContainer.getComponent("Description").text
    label = rootContainer.getComponent("Label").text
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
            
            SQL = "insert into SfcRecipeData (StepId, RecipeDataKey, RecipeDataTypeId, Description, Label, Units) "\
                "values (%s, '%s', %d, '%s', '%s', '%s')" % (stepId, key, recipeDataTypeId, description, label, units)
            print SQL
            recipeDataId = system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
            rootContainer.recipeDataId = recipeDataId
            
            if valueType == "Float":
                val = simpleValueContainer.getComponent("Float Value").floatValue
                SQL = "Insert into SfcRecipeDataValue (FloatValue) values (%f)" % (val)
            elif valueType == "Integer":
                val = simpleValueContainer.getComponent("Integer Value").intValue
                SQL = "Insert into SfcRecipeDataValue (IntegerValue) values (%d)" % (val)
            elif valueType == "String":
                val = simpleValueContainer.getComponent("String Value").text
                SQL = "Insert into SfcRecipeDataValue (StringValue) values ('%s')" % (val)
            elif valueType == "Boolean":
                val = simpleValueContainer.getComponent("Boolean Value").selected
                val = toBit(val)
                SQL = "Insert into SfcRecipeDataValue (BooleanValue) values (%d)" % (val)
            
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
            SQL = "update SfcRecipeData set RecipeDataKey='%s', Description='%s', Label = '%s', Units='%s' where RecipeDataId = %d " % (key, description, label, units, recipeDataId)
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)
            
            SQL = "Update SfcRecipeDataSimpleValue set ValueTypeId=%d where RecipeDataId = %d" % (valueTypeId, recipeDataId)
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)
            
            if valueType == "Float":
                val = simpleValueContainer.getComponent("Float Value").floatValue
            elif valueType == "Integer":
                val = simpleValueContainer.getComponent("Integer Value").intValue
            elif valueType == "String":
                val = simpleValueContainer.getComponent("String Value").text
            elif valueType == "Boolean":
                val = simpleValueContainer.getComponent("Boolean Value").selected
                val = toBit(val)
    
            updateRecipeDataValue(valueId, valueType, val, tx)

        system.db.commitTransaction(tx)
        system.db.closeTransaction(tx) 
    except:
        catch("ils.sfc.recipeData.visionEditor.saveSimpleValue", "Caught an error, rolling back transactions")
        system.db.rollbackTransaction(tx)
        system.db.closeTransaction(tx) 
    
    print "Done!"

def saveInput(rootContainer, db=""):
    print "Saving an Input"

    recipeDataId = rootContainer.recipeDataId
    stepId = rootContainer.stepId
    key = rootContainer.getComponent("Key").text
    description = rootContainer.getComponent("Description").text
    label = rootContainer.getComponent("Label").text
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
            
            SQL = "insert into SfcRecipeData (StepId, RecipeDataKey, RecipeDataTypeId, Description, Label, Units) "\
                "values (%s, '%s', %d, '%s', '%s', '%s')" % (stepId, key, recipeDataTypeId, description, label, units)
            print SQL
            recipeDataId = system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
            rootContainer.recipeDataId = recipeDataId
            
            # The values are meaningless until someone uses this data in a PV Monitoring block
            SQL = "insert into SfcRecipeDataValue (BooleanValue) values (0)"
            pvValueId = system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
            SQL = "insert into SfcRecipeDataValue (BooleanValue) values (0)"
            targetValueId = system.db.runUpdateQuery(SQL, getKey=True, tx=tx)

            SQL = "Insert into SfcRecipeDataInput (RecipeDataId, ValueTypeId, TargetValueId, PVValueId, Tag) "\
                "values (%d, %d, %d, %d, '%s')" \
                % (recipeDataId, valueTypeId, targetValueId, pvValueId, tag)            
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)
        else:
            print "Updating an Input..."
            recipeDataId = rootContainer.recipeDataId
            SQL = "update SfcRecipeData set RecipeDataKey='%s', Description='%s', Label='%s', Units='%s' where RecipeDataId = %d " % (key, description, label, units, recipeDataId)
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)

            SQL = "Update SfcRecipeDataInput set ValueTypeId=%d, Tag='%s' where RecipeDataId = %d" % (valueTypeId, tag, recipeDataId)
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)

        system.db.commitTransaction(tx)
        system.db.closeTransaction(tx) 
    except:
        catch("ils.sfc.recipeData.visionEditor.saveSimpleValue", "Caught an error, rolling back transactions")
        system.db.rollbackTransaction(tx)
        system.db.closeTransaction(tx) 
    
    print "Done!"


def saveOutput(rootContainer, db=""):
    print "Saving an Output"

    recipeDataId = rootContainer.recipeDataId
    stepId = rootContainer.stepId
    key = rootContainer.getComponent("Key").text
    description = rootContainer.getComponent("Description").text
    label = rootContainer.getComponent("Label").text
    units = rootContainer.getComponent("Units Dropdown").selectedStringValue
    outputContainer=rootContainer.getComponent("Output Container")
    
    outputType = outputContainer.getComponent("Output Type Dropdown").selectedStringValue
    outputTypeId = outputContainer.getComponent("Output Type Dropdown").selectedValue
    tag = outputContainer.getComponent("Tag").text
    download = outputContainer.getComponent("Download").selected
    download=toBit(download)
    timing = outputContainer.getComponent("Timing").floatValue
    maxTiming = outputContainer.getComponent("Max Timing").floatValue
    writeConfirm = outputContainer.getComponent("Download").selected
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
            
            SQL = "insert into SfcRecipeData (StepId, RecipeDataKey, RecipeDataTypeId, Description, Label, Units) "\
                "values (%s, '%s', %d, '%s', '%s', '%s')" % (stepId, key, recipeDataTypeId, description, label, units)
            print SQL
            recipeDataId = system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
            rootContainer.recipeDataId = recipeDataId
            
            valueIds=[]
            for i in [0,1,2]:
                # TargetValue and PV Value are dynamic values that cannot be edited.
                if i == 0:
                    attr = valueType + "Value"
                    if valueType == 'String':
                        val = outputContainer.getComponent("Output String Value").text
                        SQL = "insert into SfcRecipeDataValue (%s) values ('%s')" % (attr, val)
                    else:
                        if valueType == 'Float':
                            val = outputContainer.getComponent("Output Float Value").floatValue
                        elif valueType == 'Integer':
                            val = outputContainer.getComponent("Output Integer Value").intValue
                        elif valueType == 'Boolean':
                            val = outputContainer.getComponent("Output Boolean Value").selected
                            val = toBit(val)
                        SQL = "insert into SfcRecipeDataValue (%s) values (%s)" % (attr, str(val))
                else:
                    SQL = "insert into SfcRecipeDataValue (FloatValue) values (NULL)"
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
            SQL = "update SfcRecipeData set RecipeDataKey='%s', Description='%s', Label='%s', Units='%s' where RecipeDataId = %d " % (key, description, label, units, recipeDataId)
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)

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
        catch("ils.sfc.recipeData.visionEditor.saveSimpleValue", "Caught an error, rolling back transactions")
        system.db.rollbackTransaction(tx)
        system.db.closeTransaction(tx) 
    
    print "Done!"


def saveTimerValue(rootContainer, db=""):
    print "Saving a timer value"

    recipeDataId = rootContainer.recipeDataId
    stepId = rootContainer.stepId
    key = rootContainer.getComponent("Key").text
    description = rootContainer.getComponent("Description").text
    label = rootContainer.getComponent("Label").text
    units = rootContainer.getComponent("Units Dropdown").selectedStringValue
    timerContainer=rootContainer.getComponent("Timer Container")
    
    tx = system.db.beginTransaction(db)
    
    try:
        if recipeDataId < 0:
            print "Inserting..."
            
            recipeDataType = rootContainer.recipeDataType
            recipeDataTypeId = fetchRecipeDataTypeId(recipeDataType, db)
            
            SQL = "insert into SfcRecipeData (StepId, RecipeDataKey, RecipeDataTypeId, Description, Label, Units) "\
                "values (%s, '%s', %d, '%s', '%s', '%s')" % (stepId, key, recipeDataTypeId, description, label, units)
            print SQL
            recipeDataId = system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
            rootContainer.recipeDataId = recipeDataId
            
            val = timerContainer.getComponent("Popup Calendar").text
            SQL = "Insert into SfcRecipeDataTimer (RecipeDataId, StartTime) values (%d, '%s')" % (recipeDataId, val)
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)
        else:
            print "Updating..."
            recipeDataId = rootContainer.recipeDataId
            SQL = "update SfcRecipeData set RecipeDataKey='%s', Description='%s', Label = '%s', Units='%s' where RecipeDataId = %d " % (key, description, label, units, recipeDataId)
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)
            
            val = timerContainer.getComponent("Popup Calendar").text
            SQL = "Update SfcRecipeDataTimer set StartTime='%s' where RecipeDataId = %d" % (val, recipeDataId)
            
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)

        system.db.commitTransaction(tx)
        system.db.closeTransaction(tx) 
    except:
        catch("ils.sfc.recipeData.visionEditor.saveSimpleValue", "Caught an error, rolling back transactions")
        system.db.rollbackTransaction(tx)
        system.db.closeTransaction(tx) 
    
    print "Done!"

def saveRecipe(rootContainer, db=""):
    print "Saving a recipe"

    recipeDataId = rootContainer.recipeDataId
    stepId = rootContainer.stepId
    key = rootContainer.getComponent("Key").text
    description = rootContainer.getComponent("Description").text
    label = rootContainer.getComponent("Label").text
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
            print "Inserting..."
            
            recipeDataType = rootContainer.recipeDataType
            recipeDataTypeId = fetchRecipeDataTypeId(recipeDataType, db)
            
            SQL = "insert into SfcRecipeData (StepId, RecipeDataKey, RecipeDataTypeId, Description, Label, Units) "\
                "values (%s, '%s', %d, '%s', '%s', '%s')" % (stepId, key, recipeDataTypeId, description, label, units)
            print SQL
            recipeDataId = system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
            rootContainer.recipeDataId = recipeDataId
            
            SQL = "Insert into SfcRecipeDataRecipe (RecipeDataId, PresentationOrder, StoreTag, CompareTag, ModeAttribute, ModeValue, ChangeLevel, RecommendedValue, LowLimit, HighLimit) "\
                "values (%d, %d, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % \
                (recipeDataId, presentationOrder, storeTag, compareTag, modeAttribute, modeValue, changeLevel, recommendedValue, lowLimit, highLimit)
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)
        else:
            print "Updating..."
            recipeDataId = rootContainer.recipeDataId
            SQL = "update SfcRecipeData set RecipeDataKey='%s', Description='%s', Label = '%s', Units='%s' where RecipeDataId = %d " % (key, description, label, units, recipeDataId)
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)

            SQL = "Update SfcRecipeDataRecipe set PresentationOrder=%d, StoreTag='%s', CompareTag='%s', ModeAttribute='%s', ModeValue='%s', ChangeLevel='%s', "\
                "RecommendedValue='%s', LowLimit='%s', HighLimit='%s' where RecipeDataId = %d" % \
                (presentationOrder, storeTag, compareTag, modeAttribute, modeValue, changeLevel, recommendedValue, lowLimit, highLimit, recipeDataId)
            
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)

        system.db.commitTransaction(tx)
        system.db.closeTransaction(tx) 
    except:
        catch("ils.sfc.recipeData.visionEditor.saveSimpleValue", "Caught an error, rolling back transactions")
        system.db.rollbackTransaction(tx)
        system.db.closeTransaction(tx) 
    
    print "Done!"

'''
This code is shared between an array and a Keyed array, there are seperate containers on the window.
'''
def saveArray(rootContainer, db=""):
    print "Saving an array...."

    recipeDataId = rootContainer.recipeDataId
    stepId = rootContainer.stepId
    key = rootContainer.getComponent("Key").text
    description = rootContainer.getComponent("Description").text
    label = rootContainer.getComponent("Label").text
    units = rootContainer.getComponent("Units Dropdown").selectedStringValue
    
    recipeDataType = rootContainer.recipeDataType
    arrayContainer=rootContainer.getComponent("Array Container")
        
    valueType = arrayContainer.getComponent("Value Type Dropdown").selectedStringValue
    valueTypeId = arrayContainer.getComponent("Value Type Dropdown").selectedValue
    
    indexKey = arrayContainer.getComponent("Index Key Dropdown").selectedStringValue
    indexKeyRecipeDataId = arrayContainer.getComponent("Index Key Dropdown").selectedValue
    
    print "Index Key: ", indexKey
    print "Index Recipe Data Id: ", indexKeyRecipeDataId
    
    tx = system.db.beginTransaction(db)
    
    try:
        if recipeDataId < 0:
            print "Inserting a new array..."
            
            recipeDataType = rootContainer.recipeDataType
            recipeDataTypeId = fetchRecipeDataTypeId(recipeDataType, db)
            
            SQL = "insert into SfcRecipeData (StepId, RecipeDataKey, RecipeDataTypeId, Description, Label, Units) "\
                "values (%s, '%s', %d, '%s', '%s', '%s')" % (stepId, key, recipeDataTypeId, description, label, units)

            recipeDataId = system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
            rootContainer.recipeDataId = recipeDataId
            
            if indexKeyRecipeDataId <= 0:
                indexKeyRecipeDataId = None
                
            SQL = "Insert into SfcRecipeDataArray (RecipeDataId, ValueTypeId, IndexKeyRecipeDataId) values (?, ?, ?)"
            args = [recipeDataId, valueTypeId, indexKeyRecipeDataId]
            
            system.db.runPrepUpdate(SQL, args, tx=tx)
        else:
            print "Updating an array..."
            recipeDataId = rootContainer.recipeDataId
            SQL = "update SfcRecipeData set RecipeDataKey='%s', Description='%s', Label = '%s', Units='%s' where RecipeDataId = %d " % (key, description, label, units, recipeDataId)
            system.db.runUpdateQuery(SQL, tx=tx)

            if indexKeyRecipeDataId <= 0:
                indexKeyRecipeDataId = None

            SQL = "Update SfcRecipeDataArray set ValueTypeId=?, IndexKeyRecipeDataId=? where RecipeDataId = ?" 
            args = [valueTypeId, indexKeyRecipeDataId, recipeDataId]
            system.db.runPrepUpdate(SQL, args, tx=tx)

        # Now deal with the array.  First delete all of the rows than insert new ones.  There are no foreign keys or ids so this should be fast and easy.
        # There is a cascade delete to the SFcRecipeDataValue table, but the PK is there, not here
        
        SQL = "select ValueId from SfcRecipeDataArrayElement where RecipeDataId = %d" % (recipeDataId)
        pds = system.db.runQuery(SQL, tx=tx)
        rows=0
        for record in pds:
            SQL = "delete from SfcRecipeDataValue where valueId = %d" % record["ValueId"]
            cnt = system.db.runUpdateQuery(SQL, tx=tx)
            rows = rows + cnt
        print "...deleted %d array elements..." % (rows)
        
        table = arrayContainer.getComponent("Array Table")
        ds = table.data
        for row in range(ds.rowCount):
            if valueType == 'String':
                val = ds.getValueAt(row, "StringValue")
                SQL = "insert into SfcRecipeDataValue (StringValue) values ('%s')" % (val)
            else:
                valueColumnName = valueType + "Value"
                val = ds.getValueAt(row, valueColumnName)

                if valueType == "Boolean":
                    val = toBit(val)
                SQL = "insert into SfcRecipeDataValue (%s) values ('%s')" % (valueColumnName, val)
          
            valueId=system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
            
            SQL = "insert into SfcRecipeDataArrayElement (RecipeDataId, ArrayIndex, ValueId) values (%d, %d, %d)" % (recipeDataId, row, valueId)
            system.db.runUpdateQuery(SQL, tx=tx)

        system.db.commitTransaction(tx)
        system.db.closeTransaction(tx) 
    except:
        catch("ils.sfc.recipeData.visionEditor.saveSimpleValue", "Caught an error, rolling back transactions")
        system.db.rollbackTransaction(tx)
        system.db.closeTransaction(tx) 
    
    print "Done!"

def saveMatrix(rootContainer, db=""):
    print "Saving an matrix...."

    recipeDataId = rootContainer.recipeDataId
    stepId = rootContainer.stepId
    key = rootContainer.getComponent("Key").text    
    description = rootContainer.getComponent("Description").text
    label = rootContainer.getComponent("Label").text
    units = rootContainer.getComponent("Units Dropdown").selectedStringValue
    
    recipeDataType = rootContainer.recipeDataType
    matrixContainer=rootContainer.getComponent("Matrix Container")

    valueType = matrixContainer.getComponent("Value Type Dropdown").selectedStringValue
    valueTypeId = matrixContainer.getComponent("Value Type Dropdown").selectedValue
    
    rowIndexRecipeDataId = matrixContainer.getComponent("Row Index Key Dropdown").selectedValue
    columnIndexRecipeDataId = matrixContainer.getComponent("Column Index Key Dropdown").selectedValue
    
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
            
            SQL = "insert into SfcRecipeData (StepId, RecipeDataKey, RecipeDataTypeId, Description, Label, Units) "\
                "values (%s, '%s', %d, '%s', '%s', '%s')" % (stepId, key, recipeDataTypeId, description, label, units)
            print SQL
            recipeDataId = system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
            rootContainer.recipeDataId = recipeDataId
            
            SQL = "Insert into SfcRecipeDataMatrix (RecipeDataId, ValueTypeId, Rows, Columns, RowIndexKeyRecipeDataId, ColumnIndexKeyRecipeDataId) values (?, ?, ?, ?, ?, ?)"
            args = [recipeDataId, valueTypeId, rows, columns]
            
            if rowIndexRecipeDataId > 0:
                args.append(rowIndexRecipeDataId)
            else:
                args.append(None)
            
            if columnIndexRecipeDataId > 0:
                args.append(columnIndexRecipeDataId)
            else:
                args.append(None)

            system.db.runPrepUpdate(SQL, args, tx=tx)
        else:
            print "Updating an matrix..."
            recipeDataId = rootContainer.recipeDataId
            SQL = "update SfcRecipeData set RecipeDataKey='%s', Description='%s', Label = '%s', Units='%s' where RecipeDataId = %d " % (key, description, label, units, recipeDataId)
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)

            if recipeDataType == "Matrix":
                SQL = "Update SfcRecipeDataMatrix set ValueTypeId=%d, rows=%d, columns=%d where RecipeDataId = %d" % (valueTypeId, rows, columns, recipeDataId)
            else:
                rowIndexKeyRecipeDataId = matrixContainer.getComponent("Row Index Key Dropdown").selectedValue
                columnIndexKeyRecipeDataId = matrixContainer.getComponent("Column Index Key Dropdown").selectedValue
                SQL = "Update SfcRecipeDataMatrix set ValueTypeId=%d, RowIndexKeyRecipeDataId=%d, ColumnIndexKeyRecipeDataId=%d where RecipeDataId = %d" % \
                    (valueTypeId, rowIndexKeyRecipeDataId, columnIndexKeyRecipeDataId, recipeDataId)

            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)

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
            for columnIndex in range(1,ds.columnCount):
                val = ds.getValueAt(rowIndex, columnIndex)
                SQL = "insert into SfcRecipeDataValue (%s) values ('%s')" % ("FloatValue", val)
                print SQL
                valueId=system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
                
                print "Inserting %s at  (%d, %d)..." % (str(val), rowIndex, columnIndex)
                SQL = "insert into SfcRecipeDataMatrixElement (RecipeDataId, RowIndex, ColumnIndex, ValueId) values (%d, %d, %d, %d)" % (recipeDataId, rowIndex, columnIndex, valueId)
                system.db.runUpdateQuery(SQL, tx=tx)

        system.db.commitTransaction(tx)
        system.db.closeTransaction(tx) 
    except:
        catch("ils.sfc.recipeData.visionEditor.saveSimpleValue", "Caught an error, rolling back transactions")
        system.db.rollbackTransaction(tx)
        system.db.closeTransaction(tx) 
    
    print "Done!"

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