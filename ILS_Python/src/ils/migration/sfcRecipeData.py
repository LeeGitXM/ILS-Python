'''
Created on Oct 10, 2018

@author: phass

This is an attempt to migrate recipe data into Ignition directly from the G2 XML export file.
 
'''
import xml.etree.ElementTree as ET
import system, string
from ils.common.error import catchError
log=system.util.getLogger("com.ils.sfc.import")

def loadSteps(rootContainer):
    print "In loadSteps()"
    
    filename = rootContainer.getComponent('File Field').text
    
    if not(system.file.fileExists(filename)):
        system.gui.errorBox("The import file (" + filename + ") does not exist. Please specify a valid filename.")  
        return

    tree = ET.parse(filename)
    root = tree.getroot()
    
    steps = []
    for block in root.findall('block'):
        g2Class = block.get("class")
        g2Name = block.get("g2Name")
        print g2Class, g2Name
        step = "%s - %s" % (g2Class, g2Name)
        steps.append([step])
        
    ds = system.dataset.toDataSet(["step"], steps)
    stepList = rootContainer.getComponent('Step List')
    stepList.data = ds

def loadRecipeData(rootContainer):
    print "In loadRecipeData()"
    
    stepList = rootContainer.getComponent('Step List')
    ds = stepList.data
    row = stepList.selectedIndex
    
    if row < 0:
        system.gui.errorBox("Please select a row in the Step List")
        return

    txt = ds.getValueAt(row, 0)
    print "The selected text is: ", txt
    
    stepName = txt[txt.find(" - ") + 3:]
    print "The name is <%s>" % (stepName)
    
    filename = rootContainer.getComponent('File Field').text
    tree = ET.parse(filename)
    root = tree.getroot()
    
    recipeKeys=[]
    for block in root.findall('block'):
        g2Class = block.get("class")
        g2Name = block.get("g2Name")
        
        if g2Name == stepName:
            print "*** FOUND IT ***"
            
            for recipe in block.findall('recipe'):
                key = recipe.get("key")
                className = recipe.get("class-name")
                recipeKeys.append(["", key, className])
            
    ds = system.dataset.toDataSet(["status","key","class"], recipeKeys)
    recipeTable = rootContainer.getComponent('Recipe Table')
    recipeTable.data = ds

def translate(recipeClass):
    recipeDataType = "UNKNOWN"
    if recipeClass == "S88-RECIPE-OUTPUT-RAMP-DATA":
        recipeDataType = "Output Ramp"
        
    return recipeDataType

def importRecipeData(rootContainer):
    db = ""
    print "In importRecipeData()"
    
    '''
    The user needs to select a step in the upper left list, this is the step for the XML file whose data is to import.
    '''
    recipeStepList = rootContainer.getComponent('Step List')
    ds = recipeStepList.data
    row = recipeStepList.selectedIndex
    
    if row < 0:
        system.gui.errorBox("Please select a row in the Step List")
        return

    txt = ds.getValueAt(row, 0)
    recipeStepName = txt[txt.find(" - ") + 3:]
    
    '''
    Now the user needs to select a step in the chart hierarchy which will be the recipient of the data
    '''
    stepTable = rootContainer.getComponent('Step Container').getComponent("Steps")
    ds = stepTable.data
    row = stepTable.selectedRow
    if row < 0:
        system.gui.errorBox("Please select a row in the Chart Hierarchy Step List")
        return
    
    stepId = ds.getValueAt(row, 2)
    log.infof("Importing recipe data for step %s with id: %d", recipeStepName, stepId)
    
    recipeDataKeys = loadRecipeDataKeys(db)
    stepTypes = loadStepTypes(db)
    recipeDataTypes = loadRecipeDataTypes(db)
    valueTypes = loadValueTypes(db)
    outputTypes = loadOutputTypes(db)
    
    filename = rootContainer.getComponent('File Field').text
    tree = ET.parse(filename)
    root = tree.getroot()
    
    txId = system.db.beginTransaction(db)
    
    recipeDataCounter = 0
    errorCounter = 0
    
    for block in root.findall('block'):
        g2Class = block.get("class")
        g2Name = block.get("g2Name")
        
        if g2Name == recipeStepName:
            
            for recipe in block.findall('recipe'):
                recipeDataClass = recipe.get("class-name")
                recipeDataType = translate(recipeDataClass)
                
                if recipeDataType == "Output Ramp" and recipeDataCounter < 1000 and errorCounter < 1000:
                    print "Importing a ramp..."
                    recipeDataTypeId = recipeDataTypes.get(recipeDataType, -99)
                    recipeDataKey = recipe.get("key")
                    label = recipe.get("label")
                    description = recipe.get("description")
                    
                    inserted = importRecipeDatum(stepId, recipe, recipeDataType, recipeDataTypeId, recipeDataKey, label, description, stepTypes, recipeDataTypes, valueTypes, outputTypes, txId)
                    if inserted:
                        recipeDataCounter = recipeDataCounter + 1
                    else:
                        errorCounter = errorCounter + 1

    system.db.commitTransaction(txId)
    system.db.closeTransaction(txId)
    
    print "Done - Success: %d, Errors: %d" % (recipeDataCounter, errorCounter)

def importRecipeDatum(stepId, recipe, recipeDataType, recipeDataTypeId, recipeDataKey, label, description, stepTypes, recipeDataTypes, valueTypes, outputTypes, txId):
    log.infof("Entering importRecipeDatum with: %s", recipeDataKey)
    try:
        if recipeDataType == "Simple Value":
            valueType = recipe.get("type")
            valueTypeId = valueTypes.get(valueType, -99)
            val = recipe.get("val")
            units = recipe.get("units", "")
            recipeDataId = insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, units, txId)
            insertSimpleRecipeData(recipeDataId, valueType, valueTypeId, val, txId)
        
        elif recipeDataType in ["Output"]:
            valueType = recipe.get("valueType", "float")
            valueTypeId = valueTypes.get(valueType, -99)
            val = recipe.get("val", 0.0)
            units = recipe.get("units", "")
            outputType = recipe.get("val-type", "")
            outputTypeId = outputTypes.get(outputType, -99)
            tag = recipe.get("tag", "")
            download = recipe.get("download", "True")
            timing = recipe.get("timing", "0.0")
            maxTiming = recipe.get("max-timing", "0.0")
            writeConfirm = recipe.get("write-confirm", "True")
            
            recipeDataId = insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, units, txId)
            insertOutputRecipeData(recipeDataId, valueType, valueTypeId, outputType, outputTypeId, tag, download, timing, maxTiming, val, writeConfirm, txId)
            
            if recipeDataType == "Output Ramp":
                rampTimeMinutes = recipe.get("ramp-time", "0.0")
                updateFrequencySeconds = recipe.get("update-frequency", "0.0")
                insertOutputRampRecipeData(recipeDataId, rampTimeMinutes, updateFrequencySeconds, txId)
                    
        elif recipeDataType in ["Output Ramp"]:
            print "Yo"
            deleteRecipeData(stepId, recipeDataKey)
                
            valueType = recipe.get("valueType", "float")
            valueTypeId = valueTypes.get(valueType, -99)
            val = recipe.get("val", 0.0)
            units = recipe.get("units", "")
            outputType = recipe.get("val-type", "")
            if outputType == "RAMP-OUTOUT":
                outputType = "Output"
            else:
                outputType = "Setpoint"
            outputTypeId = outputTypes.get(outputType, -99)
            tag = recipe.get("tag", "")
            download = recipe.get("download", "True")
            timing = recipe.get("timing", "0.0")
            maxTiming = recipe.get("max-timing", "0.0")
            writeConfirm = recipe.get("write-confirm", "True")
            
            recipeDataId = insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, units, txId)
            insertOutputRecipeData(recipeDataId, valueType, valueTypeId, outputType, outputTypeId, tag, download, timing, maxTiming, val, writeConfirm, txId)
            
            if recipeDataType == "Output Ramp":
                rampTimeMinutes = recipe.get("ramp-time", "0.0")
                updateFrequencySeconds = recipe.get("update-frequency", "0.0")
                insertOutputRampRecipeData(recipeDataId, rampTimeMinutes, updateFrequencySeconds, txId)

        elif recipeDataType in ["Input"]:
            valueType = recipe.get("valueType")
            valueTypeId = valueTypes.get(valueType, -99)
            units = recipe.get("units", "")
            tag = recipe.get("tag", "")

            recipeDataId = insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, units, txId)
            insertInputRecipeData(recipeDataId, valueType, valueTypeId, tag, txId)

        elif recipeDataType == "Array":
            valueType = recipe.get("valueType")
            valueTypeId = valueTypes.get(valueType, -99)
            units = recipe.get("units", "")
            indexKey = recipe.get("indexKey", None)
            if indexKey not in [None, 'None']:
                insertIndexKey(indexKey, txId)
            recipeDataId = insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, units, txId)
            insertArray(recipeDataId, valueType, valueTypeId, txId)
            
            for element in recipe.findall("element"):
                arrayIndex = element.get("arrayIndex")
                val = element.get("value")
                insertArrayElement(recipeDataId, valueType, valueTypeId, arrayIndex, val, txId)
      
        elif recipeDataType == "Matrix":
            valueType = recipe.get("valueType")
            valueTypeId = valueTypes.get(valueType, -99)
            units = recipe.get("units", "")
            rows = recipe.get("rows", "")
            columns = recipe.get("columns", "")
            
            rowIndexKey = recipe.get("rowIndexKey", None)
            if rowIndexKey not in [None, 'None']:
                rowIndexKeyId = insertIndexKey(rowIndexKey, txId)
            else:
                rowIndexKeyId = -1
                
            columnIndexKey = recipe.get("columnIndexKey", None)
            if rowIndexKey not in [None, 'None']:
                columnIndexKeyId = insertIndexKey(columnIndexKey, txId)
            else:
                columnIndexKeyId = -1
                
            recipeDataId = insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, units, txId)
            insertMatrix(recipeDataId, valueType, valueTypeId, rows, columns, rowIndexKey, columnIndexKey, txId)
            
            for element in recipe.findall("element"):
                rowIndex = element.get("rowIndex")
                columnIndex = element.get("columnIndex")
                val = element.get("value")
                insertMatrixElement(recipeDataId, valueType, valueTypeId, rowIndex, columnIndex, val, txId)
                
        elif recipeDataType == "Timer":
            units = recipe.get("units", "")
            recipeDataId = insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, units, txId)
            insertTimerRecipeData(recipeDataId, txId)
        
        elif recipeDataType == "Recipe":
            units = recipe.get("units", "")
            presentationOrder = recipe.get("presentationOrder", "0")
            storeTag = recipe.get("storeTag", "")
            compareTag = recipe.get("compareTag", "")
            modeAttribute = recipe.get("modeAttribute", "")
            changeLevel = recipe.get("changeLevel", "")
            recommendedValue = recipe.get("recommendedValue", "")
            lowLimit = recipe.get("lowLimit", "")
            highLimit = recipe.get("highLimit", "")
            
            recipeDataId = insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, units, txId)
            insertRecipeRecipeData(recipeDataId, presentationOrder, storeTag, compareTag, modeAttribute, changeLevel, recommendedValue, lowLimit, highLimit, txId)
            
        else:
            txt = "Error: Unable to import recipe data type: %s with key %s" % (recipeDataType, recipeDataKey)
            print txt
            log.errorf(txt)
            system.db.rollbackTransaction(txId)
            system.db.closeTransaction(txId)
            system.gui.errorBox(txt)
            return False
    except:
        errorTxt = catchError(recipeDataType, recipeDataKey)
        print errorTxt
        return False
                
    return True

'''
Copied from the SFC import module.  Copied here so it can be tweaked without ramifacations if needed
'''
def insertRecipeData(stepId, key, recipeDataType, recipeDataTypeId, label, description, units, txId):
    log.infof("      Inserting recipe data:  %s - %s...", key, recipeDataType)
    SQL = "insert into SfcRecipeData (StepID, RecipeDataKey, RecipeDataTypeId, Label, Description, Units) values (%d, '%s', %d, '%s', '%s', '%s')" % \
        (stepId, key, recipeDataTypeId, label, description, units)
    recipeDataId = system.db.runUpdateQuery(SQL, tx=txId, getKey=True)
    return recipeDataId

def insertSimpleRecipeData(recipeDataId, valueType, valueTypeId, val, txId):
    log.tracef("          Inserting a Simple Value...")
    valueId = insertRecipeDataValue(valueType, val, txId)
    SQL = "insert into SfcRecipeDataSimpleValue (recipeDataId, valueTypeId, ValueId) values (%d, %d, %d)" % (recipeDataId, valueTypeId, valueId)
    system.db.runUpdateQuery(SQL, tx=txId)
    
def insertOutputRecipeData(recipeDataId, valueType, valueTypeId, outputType, outputTypeId, tag, download, timing, maxTiming, val, writeConfirm, txId):
    log.tracef("          Inserting an Output recipe data with timing: %s and val: %s...", str(timing), str(val))
    outputValueId = insertRecipeDataValue(valueType, val, txId)
    targetValueId = insertRecipeDataValue(valueType, 0.0, txId)
    pvValueId = insertRecipeDataValue(valueType, 0.0, txId)
    SQL = "insert into SfcRecipeDataOutput (recipeDataId, valueTypeId, outputTypeId, tag, download, timing, maxTiming, outputValueId, targetValueId, pvValueId, writeConfirm) "\
        "values (%d, %d, %d, '%s', '%s', %s, %s, %d, %d, %d, '%s')" % \
        (recipeDataId, valueTypeId, outputTypeId, tag, download, str(timing), str(maxTiming), outputValueId, targetValueId, pvValueId, writeConfirm)
    print SQL
    system.db.runUpdateQuery(SQL, tx=txId)

def insertOutputRampRecipeData(recipeDataId, rampTimeMinutes, updateFrequencySeconds, txId):
    log.tracef("          Inserting an Output Ramp recipe data with rampMinutes: %s and update frequency: %s...", str(rampTimeMinutes), str(updateFrequencySeconds))
    SQL = "insert into SfcRecipeDataOutputRamp (recipeDataId, rampTimeMinutes, updateFrequencySeconds) values (%d, %s, %s)" % \
        (recipeDataId, str(rampTimeMinutes), str(updateFrequencySeconds))
    system.db.runUpdateQuery(SQL, tx=txId)
    
def insertInputRecipeData(recipeDataId, valueType, valueTypeId, tag, txId):
    log.tracef("          Inserting an Input recipe data...")
    targetValueId = insertRecipeDataValue(valueType, 0.0, txId)
    pvValueId = insertRecipeDataValue(valueType, 0.0, txId)
    SQL = "insert into SfcRecipeDataInput (recipeDataId, valueTypeId, tag, pvValueId, targetValueId) values (%d, %d, '%s', %d, %d)" % \
        (recipeDataId, valueTypeId, tag, pvValueId, targetValueId)
    system.db.runUpdateQuery(SQL, tx=txId)
    
def insertArray(recipeDataId, valueType, valueTypeId, txId):
    log.tracef("          Inserting an array...")
    SQL = "insert into SfcRecipeDataArray (recipeDataId, valueTypeId) values (%d, %d)" % (recipeDataId, valueTypeId)
    system.db.runUpdateQuery(SQL, tx=txId)
    
def insertArrayElement(recipeDataId, valueType, valueTypeId, arrayIndex, val, txId):
    log.tracef("          Inserting an array element...")
    valueId = insertRecipeDataValue(valueType, val, txId)
    SQL = "insert into SfcRecipeDataArrayElement (recipeDataId, arrayIndex, ValueId) values (%d, %d, %d)" % (recipeDataId, int(arrayIndex), valueId)
    system.db.runUpdateQuery(SQL, tx=txId)

def insertMatrix(recipeDataId, valueType, valueTypeId, rows, columns, rowIndexKey, columnIndexKey, txId):
    log.tracef("          Inserting a matrix...")
    SQL = "insert into SfcRecipeDataMatrix (recipeDataId, valueTypeId, rows, columns) values (%d, %d, %d, %d)" % (recipeDataId, valueTypeId, int(rows), int(columns))
    system.db.runUpdateQuery(SQL, tx=txId)
    
def insertMatrixElement(recipeDataId, valueType, valueTypeId, rowIndex, columnIndex, val, txId):
    log.tracef("          Inserting a matrix element...")
    valueId = insertRecipeDataValue(valueType, val, txId)
    SQL = "insert into SfcRecipeDataMatrixElement (recipeDataId, rowIndex, columnIndex, ValueId) values (%d, %d, %d, %d)" % (recipeDataId, int(rowIndex), int(columnIndex), valueId)
    system.db.runUpdateQuery(SQL, tx=txId)
    
def insertTimerRecipeData(recipeDataId, txId):
    log.tracef("          Inserting a Timer...")
    SQL = "insert into SfcRecipeDataTimer (recipeDataId) values (%d)" % (recipeDataId)
    system.db.runUpdateQuery(SQL, tx=txId)

def insertRecipeRecipeData(recipeDataId, presentationOrder, storeTag, compareTag, modeAttribute, changeLevel, recommendedValue, lowLimit, highLimit, txId):
    log.tracef("          Inserting a RECIPE recipe data...")
    SQL = "insert into SfcRecipeDataRecipe (recipeDataId, PresentationOrder, StoreTag, CompareTag, ModeAttribute, ChangeLevel, RecommendedValue, LowLimit, HighLimit) "\
        " values (%d, %s, '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % \
        (recipeDataId, presentationOrder, storeTag, compareTag, modeAttribute, changeLevel, recommendedValue, lowLimit, highLimit)
    system.db.runUpdateQuery(SQL, tx=txId)
    
def insertRecipeDataValue(valueType, val, txId):
    log.tracef("        Inserting a recipe data value (type: %s, value: %s)...", valueType, val)
    
    if valueType in ["String", "symbol"]:
        SQL = "insert into SfcRecipeDataValue (StringValue) values ('%s')" % (val)
    elif valueType == "Integer":
        SQL = "insert into SfcRecipeDataValue (IntegerValue) values (%d)" % (int(val))
    elif string.lower(valueType) == "float":
        SQL = "insert into SfcRecipeDataValue (FloatValue) values (%f)" % (float(val))
    elif valueType == "Boolean":
        SQL = "insert into SfcRecipeDataValue (BooleanValue) values ('%s')" % (val)
    
    valueId = system.db.runUpdateQuery(SQL, tx=txId, getKey=True)
    return valueId


''' -----------------------------------------------------
    Generic utilities
    ----------------------------------------------------- '''

def loadRecipeDataKeys(db):
    SQL = "select KeyName, KeyId from SfcRecipeDataKeyMaster"
    pds = system.db.runQuery(SQL, db)
    
    keys = {}
    for record in pds:
        keys[record["KeyName"]] = record["KeyId"]
    
    log.infof("The keys are: %s", str(keys))
    return keys

def loadStepTypes(db):
    SQL = "select StepTypeId, StepType from SfcStepType order by stepType"
    pds = system.db.runQuery(SQL, db)
    
    stepTypes = {}
    for record in pds:
        stepTypes[record["StepType"]] = record["StepTypeId"]
    
    log.infof("The step types are: %s", str(stepTypes))
    return stepTypes

def loadRecipeDataTypes(db):
    SQL = "select RecipeDataTypeId, RecipeDataType from SfcRecipeDataType"
    pds = system.db.runQuery(SQL, db)
    
    recipeDataTypes = {}
    for record in pds:
        recipeDataTypes[record["RecipeDataType"]] = record["RecipeDataTypeId"]
    
    return recipeDataTypes

def loadOutputTypes(db):
    SQL = "select OutputTypeId, OutputType from SfcRecipeDataOutputType"
    pds = system.db.runQuery(SQL, db)
    
    recipeOutputTypes = {}
    for record in pds:
        recipeOutputTypes[record["OutputType"]] = record["OutputTypeId"]
    
    return recipeOutputTypes

def loadValueTypes(db):
    SQL = "select ValueTypeId, ValueType from SfcValueType"
    pds = system.db.runQuery(SQL, db)
    
    valueTypes = {}
    for record in pds:
        valueTypes[string.lower(record["ValueType"])] = record["ValueTypeId"]
    
    log.info("---------------")
    log.infof("The known value types are: %s", str(valueTypes))
    log.info("---------------")
    
    return valueTypes

def insertIndexKey(indexKey, txId):
    SQL = "select ValueTypeId, ValueType from SfcValueType"
    pds = system.db.runQuery(SQL, tx=txId)
    
    valueTypes = {}
    for record in pds:
        valueTypes[record["ValueType"]] = record["ValueTypeId"]
    
    return valueTypes

def deleteRecipeData(stepId, recipeDataKey):
    log.infof("Deleting existing recipe data for step %d with key: %s...", stepId, recipeDataKey)
    SQL = "select RecipeDataType from SfcRecipeDataView where StepId = %d and RecipeDataKey = '%s'" % (stepId, recipeDataKey) 
    print SQL
    pds = system.db.runQuery(SQL)
    
    for record in pds:
        recipeDataType = record["RecipeDataType"]
        if recipeDataType in ["Output", "Output Ramp"]:
            print "Deleting a %s..." % (recipeDataType)
            
            SQL = "select * from SfcRecipeDataOutputRampView where StepId = %s and RecipeDataKey = '%s'" % (str(stepId), recipeDataKey)
            pds = system.db.runQuery(SQL)
            for record in pds:
                outputValueId = record["OutputValueId"]
                targetValueId = record["TargetValueId"]
                pvValueId = record["PVValueId"]
                rows = system.db.runUpdateQuery("Delete from SfcRecipeData where RecipeDataId = %d" % (record["RecipeDataId"]))
                print "...deleted %d rows from SfcRecipeData..." % (rows)
                rows = system.db.runUpdateQuery("Delete from SfcRecipeDataValue where ValueId = %d or ValueId = %d or ValueId = %d" % (outputValueId, targetValueId, pvValueId))
                print "...deleted %d rows from SfcRecipeData..." % (rows)