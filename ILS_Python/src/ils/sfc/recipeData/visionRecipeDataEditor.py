'''
Created on Feb 1, 2017

@author: phass
'''

import system, string
from ils.common.cast import toBit
from ils.common.error import catch
from ils.sfc.recipeData.core import fetchRecipeDataTypeId, fetchValueTypeId
from mailbox import fcntl
log=system.util.getLogger("com.ils.sfc.visionEditor")

from ils.sfc.recipeData.constants import ARRAY, INPUT, MATRIX, OUTPUT, RECIPE, SIMPLE_VALUE, TIMER

    
# The chart path is passed as a property when the window is opened.  Look up the chartId, refresh the Steps table and clear the RecipeData Table
def internalFrameOpened(rootContainer, db=""):
    print "In internalFrameOpened"
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
            
            SQL = "select * from SfcRecipeDataArrayElementView where recipeDataId = %s order by ArrayIndex" % (recipeDataId)
            pds = system.db.runQuery(SQL, db)
            rootContainer.arrayValuesDataset = pds
            
        elif recipeDataType == MATRIX:
            print "Fetching an Matrix"
            SQL = "select * from SfcRecipeDataMatrixView where recipeDataId = %s" % (recipeDataId)
            pds = system.db.runQuery(SQL, db)
            if len(pds) <> 1:
                raise ValueError, "Unable to fetch a Matrix recipe data with id: %s" % (recipeDataId)
            record = pds[0]
            rootContainer.matrixDataset = pds
            
            # Set the visibility of the values columns so only the one for the target valueType is shown
            valueType = record["ValueType"]
            setArrayTableColumnVisibility(rootContainer, valueType)
            
            SQL = "select * from SfcRecipeDataMatrixElementView where recipeDataId = %s order by RowIndex, ColumnIndex" % (recipeDataId)
            pds = system.db.runQuery(SQL, db)
            rootContainer.matrixValuesDataset = pds
            
            updateMatrixTable(rootContainer, pds)
            
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
            
            header = ["RecipeDataId", "ArrayIndex","FloatValue","IntegerValue","StringValue","BooleanValue"]
            ds = system.dataset.toDataSet(header, [])
            rootContainer.arrayValuesDataset = ds
            
        elif recipeDataType == MATRIX:
            print "Initializing an Matrix..."
            ds = rootContainer.matrixDataset
            rootContainer.matrixDataset = ds
            
            header = ["RecipeDataId", "RowIndex", "ColumnIndex", "FloatValue","IntegerValue","StringValue","BooleanValue"]
            ds = system.dataset.toDataSet(header, [[-1,0,0,0.0,0,"", False]])
            pds = system.dataset.toPyDataSet(ds)
            updateMatrixTable(rootContainer, pds)   

        else:
            raise ValueError, "Unexpected NEW recipe data type <%s>" % (recipeDataType)
        
        rootContainer.description = ""
        rootContainer.label = ""
        rootContainer.units = ""

def updateMatrixTable(rootContainer, pds):
    container = rootContainer.getComponent("Matrix Container")
    table = container.getComponent("Matrix Table")
    
    header = ['row']
    data = []
    lastRow = 0
    row = 0
    rowData = [0]
    for record in pds:
        row = record["RowIndex"]
        column = record["ColumnIndex"]
        val = record["FloatValue"]
        
        if row == 0:
            header.append(column)
            
        if row <> lastRow:
            data.append(rowData)
            rowData = [row, val]
        else:
            rowData.append(val)
        lastRow = row
    
    data.append(rowData)
    print header
    print data
    ds = system.dataset.toDataSet(header, data)
    table.data = ds

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

def renumberMatrixRows(ds):
    for row in range(ds.rowCount):
        ds = system.dataset.setValue(ds, row, "Row", row)
    return ds

def renumberMatrixColumns(ds):
#    for row in range(ds.rowCount):
#        ds = system.dataset.setValue(ds, row, "ArrayIndex", row)
    return ds
    
def addArrayRow(table):
    print "Adding a Row"
    ds = table.data
    recipeDataId = table.parent.parent.recipeDataId
    vals = [recipeDataId, 1, None, None, None, None]
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
        ds = system.dataset.setValue(ds, row, "ArrayIndex", row)
    table.data = ds
    
# This is called once by a timer shortly after the window is activated.  It gets around the Age old problem I have where the
# list of values are bound to query and the selected value is bound to a property and there is a timing issue between the two of them.
def refreshComboBoxes(event):
    print "Refreshing the combo boxes"
    rootContainer = event.source.parent
    
    # Common Combos
    # --- I'm not sure why the units seems to work ---
    
    # Simple Value Combos
    container = rootContainer.getComponent("Simple Value Container")
    combo = container.getComponent("Value Type Dropdown")
    ds = rootContainer.simpleValueDataset
    valueType = ds.getValueAt(0,"ValueType")
    combo.selectedStringValue = valueType
    
    # Input Combos
    container = rootContainer.getComponent("Input Container")    
    combo = container.getComponent("Value Type Dropdown")
    valueType = ds.getValueAt(0,"ValueType")
    combo.selectedStringValue = valueType
    
    # Output Combos
    container = rootContainer.getComponent("Output Container")
    combo = container.getComponent("Output Type Dropdown")
    ds = rootContainer.outputDataset
    outputType = ds.getValueAt(0,"OutputType")
    combo.selectedStringValue = outputType
    
    combo = container.getComponent("Value Type Dropdown")
    valueType = ds.getValueAt(0,"ValueType")
    combo.selectedStringValue = valueType
    
    # Array Combos
    container = rootContainer.getComponent("Array Container")
    combo = container.getComponent("Value Type Dropdown")
    ds = rootContainer.arrayDataset
    valueType = ds.getValueAt(0,"ValueType")
    combo.selectedStringValue = valueType
    

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

def saveArray(rootContainer, db=""):
    print "Saving an array...."

    recipeDataId = rootContainer.recipeDataId
    stepId = rootContainer.stepId
    
    key = rootContainer.getComponent("Key").text
    description = rootContainer.getComponent("Description").text
    label = rootContainer.getComponent("Label").text
    units = rootContainer.getComponent("Units Dropdown").selectedStringValue
    arrayContainer=rootContainer.getComponent("Array Container")
    valueType = arrayContainer.getComponent("Value Type Dropdown").selectedStringValue
    valueTypeId = arrayContainer.getComponent("Value Type Dropdown").selectedValue
    
    tx = system.db.beginTransaction(db)
    
    try:
        if recipeDataId < 0:
            print "Inserting a new array..."
            
            recipeDataType = rootContainer.recipeDataType
            recipeDataTypeId = fetchRecipeDataTypeId(recipeDataType, db)
            
            SQL = "insert into SfcRecipeData (StepId, RecipeDataKey, RecipeDataTypeId, Description, Label, Units) "\
                "values (%s, '%s', %d, '%s', '%s', '%s')" % (stepId, key, recipeDataTypeId, description, label, units)
            print SQL
            recipeDataId = system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
            rootContainer.recipeDataId = recipeDataId
            
            SQL = "Insert into SfcRecipeDataArray (RecipeDataId, ValueTypeId) values (%d, %d)" % (recipeDataId, valueTypeId)
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)
        else:
            print "Updating an array..."
            recipeDataId = rootContainer.recipeDataId
            SQL = "update SfcRecipeData set RecipeDataKey='%s', Description='%s', Label = '%s', Units='%s' where RecipeDataId = %d " % (key, description, label, units, recipeDataId)
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)

            SQL = "Update SfcRecipeDataArray set ValueTypeId=%d where RecipeDataId = %d" % (valueTypeId, recipeDataId)
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)

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
            print SQL            
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
    matrixContainer=rootContainer.getComponent("Matrix Container")
    
    valueType = matrixContainer.getComponent("Value Type Dropdown").selectedStringValue
    valueTypeId = matrixContainer.getComponent("Value Type Dropdown").selectedValue
    
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
            
            SQL = "Insert into SfcRecipeDataMatrix (RecipeDataId, ValueTypeId, Rows, Columns) values (%d, %d, %d, %d)" % (recipeDataId, valueTypeId, rows, columns)
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)
        else:
            print "Updating an matrix..."
            recipeDataId = rootContainer.recipeDataId
            SQL = "update SfcRecipeData set RecipeDataKey='%s', Description='%s', Label = '%s', Units='%s' where RecipeDataId = %d " % (key, description, label, units, recipeDataId)
            print SQL
            system.db.runUpdateQuery(SQL, tx=tx)

            SQL = "Update SfcRecipeDataMatrix set ValueTypeId=%d, rows=%d, columns=%d where RecipeDataId = %d" % (valueTypeId, rows, columns, recipeDataId)
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