'''
Created on Jan 9, 2017

@author: phass
'''

import system, string, time
from system.util import jsonDecode
import xml.etree.ElementTree as ET
from ils.io.util import readTag
from ils.sfc.recipeData.structureManager import getTxId
from ils.common.error import catchError
from ils.common.cast import toBit, isFloat
from ils.sfc.recipeData.core import fetchValueTypeId, fetchOutputTypeId, fetchRecipeDataTypeId, fetchStepIdFromUUID
from ils.common.config import getTagProvider, getDatabase
from ils.log import getLogger
log = getLogger(__name__)

def migrateChart(chartPath, resourceId, chartResourceAsXML):
    db = getDatabase()
    
    provider = getTagProvider()
    recipeDataMigrationEnabled = readTag("[%s]Configuration/SFC/sfcRecipeDataMigrationEnabled" % (provider)).value
    if not(recipeDataMigrationEnabled):
        log.infof("Recipe Data migration is disabled!")
        log.tracef("========================")
        log.tracef(chartResourceAsXML)
        log.tracef("========================")
        return
    
    log.infof("***************")
    log.infof("Migrating a charts recipe data(PYTHON) (%s-%s) ...", chartPath, str(resourceId))
    log.tracef(chartResourceAsXML)
    log.infof("***************")
    
    # This runs immediately after the chart hierarchy analysis which has a number of database transactions.  Give those time to get
    # committed to the database.  This only runs in designer during migration, so we are not super concerned about performance.
    time.sleep(5)
    try:
        #log.tracef(chartResourceAsXML)
        tx = getTxId(db)
        log.tracef("parsing the tree...")
        root = ET.fromstring(chartResourceAsXML)

        for step in root.findall('step'):
            processStep(step, db, tx)
        
        for parallel in root.findall('parallel'):
            print "Handling a parallel"

            for step in parallel.findall('step'):
                print "Found a step inside of a parallel..."
                processStep(step, db, tx)
        
        log.infof("***************")
        log.infof(" Done migrating recipe data, committing transactions...")
        log.infof("***************") 
        
    except:
        errorTxt = catchError("Migrating Recipe Data - rolling back transactions")
        log.errorf(errorTxt)
        system.db.rollbackTransaction(tx)
        
    else:
        system.db.commitTransaction(tx)
    
    finally:
        system.db.closeTransaction(tx)


def processStep(step, db, tx):
    log.tracef("==============")
    try:
        stepName = step.get("name")
        log.infof("Migrating step: %s...", stepName)
        stepUUID = step.get("id")
        stepId = fetchStepIdFromUUID(stepUUID, tx)
        stepType = step.get("factory-id")
        log.tracef("Found a step %s - %s - %s- %d....", stepName, stepType, stepUUID, stepId)
        
        SQL = "delete from SfcRecipeData where StepId = %d" % stepId
        log.tracef(SQL)
        rows=system.db.runUpdateQuery(SQL, tx=tx)
        log.tracef("...Deleted %d rows from SfcRecipeData", rows)
        
        SQL = "delete from SfcRecipeDataFolder where StepId = %d" % stepId
        log.tracef(SQL)
        rows=system.db.runUpdateQuery(SQL, tx=tx)
        log.tracef("...Deleted %d rows from SfcRecipeDataFolder", rows)
        
        for associatedData in step.findall('associated-data'):
    
            # This looks a lot like a dictionary of dictionaries
            log.tracef("  Raw Text:            %s", str(associatedData.text))
            log.tracef("  That text was   %s bytes", str(len(str(associatedData.text))))
            
            # The associated data is a text string that looks like a dictionary.  Python can convert it but is a little picky about some format things
            txt=associatedData.text
            txt = string.replace(txt, "null","\"\"")
            txt = string.replace(txt, "false","False")
            txt = string.replace(txt, "true","True")
    #        log.tracef("  Converted Text:      %s", txt)
            myDict = jsonDecode(txt)
            log.tracef("  Dictionary:          %s", str(myDict))
            
            for k in myDict.keys():
                recipeData = myDict.get(k)
                recipeDataType = getRecipeDataTypeFromAssociatedData(recipeData)
                
                if recipeDataType == "Output":
                    output(stepName, stepType, stepId, None, recipeData, db, tx)
                elif recipeDataType == "Group":
                    group(stepName, stepType, stepId, None, recipeData, db, tx)
                elif recipeDataType == "OutputRamp":
                    outputRamp(stepName, stepType, stepId, None, recipeData, db, tx)
                elif recipeDataType == "Input":
                    input(stepName, stepType, stepId, None, recipeData, db, tx)
                elif recipeDataType == "Value":
                    simpleValue(stepName, stepType, stepId, None, recipeData, db, tx)
                elif recipeDataType == "Timer":
                    timer(stepName, stepType, stepId, None, recipeData, db, tx)
                elif recipeDataType == "Array":
                    arrayData(stepName, stepType, stepId, None, recipeData, db, tx)
                elif recipeDataType == "Matrix":
                    matrixData(stepName, stepType, stepId, None, recipeData, db, tx)
                elif recipeDataType == "EMData":
                    recipeDataMigrator(stepName, stepType, stepId, None, recipeData, db, tx)
                elif recipeDataType == "SQC":
                    sqc(stepName, stepType, stepId, None, recipeData, db, tx)
    
                elif recipeDataType == None:
                    log.trace("Skipping a NULL value")
                else:
                    raise ValueError, "Unexpected type of recipe data: %s" % (recipeDataType)

        log.trace("Done with step")
    except:
        errorTxt = catchError("Error migrating recipe data for a step")
        log.errorf(errorTxt)
            
def getRecipeDataTypeFromAssociatedData(recipeData):
    try:
        recipeDataType = recipeData.get("class", None)
    except:
        recipeDataType = None
        
    return recipeDataType

def matrixData(stepName, stepType, stepId, recipeDataFolderId, recipeData, db, tx):
    key = recipeData.get("key","")
    
    log.infof("  Migrating a MATRIX with key: %s for step: %s", key, stepName)
    description = recipeData.get("description","")
    label = recipeData.get("label","")
    units = recipeData.get("units","")
    rows = recipeData.get("rows","")
    columns = recipeData.get("columns","")
    recipeDataTypeId=fetchRecipeDataTypeId("Matrix", db)
    
    recipeDataId = insertRecipeData(stepName, stepType, stepId, recipeDataFolderId, key, recipeDataTypeId, description, label, units, tx)
    
    valueType = recipeData.get("valueType","Float")
    valueType = convertValueType(valueType)
    valueTypeId = fetchValueTypeId(valueType, db)
    valueMatrix = recipeData.get("value", None)
    
    SQL = "insert into SfcRecipeDataMatrix (RecipeDataId, ValueTypeId, Rows, Columns) values (%d, %d, %s, %s)" % (recipeDataId, valueTypeId, str(rows), str(columns))
    system.db.runUpdateQuery(SQL, tx=tx)
    
    print "Matrix Value 1: ", valueMatrix
    valueMatrix = string.lstrip(valueMatrix, "[")
    valueMatrix = string.rstrip(valueMatrix, "]")
    print "Matrix Value 2: ", valueMatrix
    
    rowIdx = 0
    for row in valueMatrix.split("],["):
        print "Row: ", row
        colIdx = 0
        for val in row.split(","):
            print "Parsed values: ", val
            if valueType == "Float":
                val = float(val)
                SQL = "insert into SfcRecipeDataValue (FloatValue) values (%s)" % (str(val))
            elif valueType == "Integer":
                val = int(val)
                SQL = "insert into SfcRecipeDataValue (IntegerValue) values (%s)" % (str(val))
            elif valueType == "String":
                SQL = "insert into SfcRecipeDataValue (StringValue) values ('%s')" % (str(val))
            elif valueType == "Boolean":
                val=toBit(val)
                SQL = "insert into SfcRecipeDataValue (BooleanValue) values (%d)" % (val)
            else:
                errorTxt = "Unknown value type: %s" % str(valueType)
                raise ValueError, errorTxt
        
            log.tracef(SQL)
            valueId=system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
    
            SQL = "insert into SfcRecipeDataMatrixElement (RecipeDataId, RowIndex, ColumnIndex, ValueId) values (%d, %d, %d, %d)" % (recipeDataId, rowIdx, colIdx, valueId)
            system.db.runUpdateQuery(SQL, tx=tx)
            colIdx = colIdx + 1

        rowIdx = rowIdx + 1
        
    log.tracef("   ...done inserting an Array!")
    


def arrayData(stepName, stepType, stepId, recipeDataFolderId, recipeData, db, tx):
    key = recipeData.get("key","")
    log.infof("  Migrating an ARRAY with key: %s for step: %s", key, stepName)
    description = recipeData.get("description","")
    label = recipeData.get("label","")
    units = recipeData.get("units","")
    recipeDataTypeId=fetchRecipeDataTypeId("Array", db)
    
    recipeDataId = insertRecipeData(stepName, stepType, stepId, recipeDataFolderId, key, recipeDataTypeId, description, label, units, tx)
    
    valueType = recipeData.get("valueType","String")
    valueType = convertValueType(valueType)
    valueTypeId = fetchValueTypeId(valueType, db)
    valueArray = recipeData.get("value", None)
    
    SQL = "insert into SfcRecipeDataArray (RecipeDataId, ValueTypeId) values (%d, %d)" % (recipeDataId, valueTypeId)
    system.db.runUpdateQuery(SQL, tx=tx)
    
    valueArray = string.lstrip(valueArray, "[")
    valueArray = string.rstrip(valueArray, "]")
    
    idx = 0
    for val in valueArray.split(","):
        if valueType == "Float":
            val = float(val)
            SQL = "insert into SfcRecipeDataValue (FloatValue) values (%s)" % (str(val))
        elif valueType == "Integer":
            val = int(val)
            SQL = "insert into SfcRecipeDataValue (IntegerValue) values (%s)" % (str(val))
        elif valueType == "String":
            SQL = "insert into SfcRecipeDataValue (StringValue) values ('%s')" % (str(val))
        elif valueType == "Boolean":
            val=toBit(val)
            SQL = "insert into SfcRecipeDataValue (BooleanValue) values (%d)" % (val)
        else:
            errorTxt = "Unknown value type: %s" % str(valueType)
            raise ValueError, errorTxt
        
        log.tracef(SQL)
        valueId=system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
        
        SQL = "insert into SfcRecipeDataArrayElement (RecipeDataId, ArrayIndex, ValueId) values (%d, %d, %d)" % (recipeDataId, idx, valueId)
        system.db.runUpdateQuery(SQL, tx=tx)

        idx = idx + 1
        
    log.tracef("   ...done inserting an Array!")

def group(stepName, stepType, stepId, recipeDataFolderId, groupData, db, tx):
    key = groupData.get("key","")

    log.infof("  Migrating a GROUP with key: %s for step: %s", key, stepName)
    
    description = groupData.get("description","")
    label = groupData.get("label","")
    
    if recipeDataFolderId < 0 or recipeDataFolderId == None:
        SQL = "insert into SfcRecipeDataFolder (stepId, RecipeDataKey, Description, Label) "\
            " values (?, ?, ?, ?)"
        log.tracef(SQL)
        recipeDataFolderId = system.db.runPrepUpdate(SQL, [stepId, key, description, label], getKey=True, tx=tx)
    else:
        SQL = "insert into SfcRecipeDataFolder (stepId, RecipeDataKey, Description, Label, RecipeDataFolderId) "\
            " values (?, ?, ?, ?, ?)"
        log.tracef(SQL)
        recipeDataFolderId = system.db.runPrepUpdate(SQL, [stepId, key, description, label, recipeDataFolderId], getKey=True, tx=tx)
        
    log.tracef("   ...inserted a record into SfcRecipeDataFolder with id: %d", recipeDataFolderId)

    for k in groupData.keys():
        recipeData = groupData.get(k)
        
        recipeDataType = getRecipeDataTypeFromAssociatedData(recipeData)
        
        if recipeDataType == "Output":
            output(stepName, stepType, stepId, recipeDataFolderId, recipeData, db, tx)
        elif recipeDataType == "Group":
            group(stepName, stepType, stepId, recipeDataFolderId, recipeData, db, tx)
        elif recipeDataType == "OutputRamp":
            outputRamp(stepName, stepType, stepId, recipeDataFolderId, recipeData, db, tx)
        elif recipeDataType == "Input":
            input(stepName, stepType, stepId, recipeDataFolderId, recipeData, db, tx)
        elif recipeDataType == "Value":
            simpleValue(stepName, stepType, stepId, recipeDataFolderId, recipeData, db, tx)
        elif recipeDataType == "Timer":
            timer(stepName, stepType, stepId, recipeDataFolderId, recipeData, db, tx)
        elif recipeDataType == "Array":
            arrayData(stepName, stepType, stepId, recipeDataFolderId, recipeData, db, tx)
        elif recipeDataType == "Matrix":
            matrixData(stepName, stepType, stepId, recipeDataFolderId, recipeData, db, tx)
        elif recipeDataType == "EMData":
            recipeDataMigrator(stepName, stepType, stepId, recipeDataFolderId, recipeData, db, tx)
        elif recipeDataType == "SQC":
            sqc(stepName, stepType, stepId, None, recipeData, db, tx)
        elif recipeDataType == None:
            log.trace("Skipping a NULL value")
        else:
            raise ValueError, "Unexpected type of recipe data: %s" % (recipeDataType)        


def simpleValue(stepName, stepType, stepId, recipeDataFolderId, recipeData, db, tx):
    key = recipeData.get("key","")
    log.infof("  Migrating a SIMPLE VALUE with key: %s for step: %s", key, stepName)
    description = recipeData.get("description","")
    label = recipeData.get("label","")
    units = recipeData.get("units","")
    recipeDataTypeId=fetchRecipeDataTypeId("Simple Value", db)
    
    recipeDataId = insertRecipeData(stepName, stepType, stepId, recipeDataFolderId, key, recipeDataTypeId, description, label, units, tx)
    
    valueType = recipeData.get("valueType","String")
    valueType = convertValueType(valueType)
    
    val = recipeData.get("value", None)
    if val in ["NO-VALUE", "****"]:
        val = "NULL"
        
    '''
    Just because they said it was a float, doesn't mean it is a float!
    If they said it was a float but I can't convert it to a float, then change the type to a string
    '''
    if valueType == "Float" and val <> "NULL":
        if not(isFloat(val)):
            valueType = "String"
            log.warnf("  Overriding the datatype for key <%s> in step <%s> because the value <%s> could not be converted to a float", key, stepName, str(val))

    valueTypeId = fetchValueTypeId(valueType, db)
    if valueType == "Float":
        if str(val) == "False":
            log.info("--Overriding False for a float to 0.0--")
            val = 0.0
        elif str(val) == "True":
            log.info("--Overriding True for a float to 1.0--")
            val = 1.0
        SQL = "insert into SfcRecipeDataValue (FloatValue) values (%s)" % (str(val))
    elif valueType == "Integer":
        SQL = "insert into SfcRecipeDataValue (IntegerValue) values (%s)" % (str(val))
    elif valueType == "String":
        val = string.replace(str(val), "'", "")
        SQL = "insert into SfcRecipeDataValue (StringValue) values ('%s')" % (str(val))
    elif valueType == "Boolean":
        val=toBit(val)
        SQL = "insert into SfcRecipeDataValue (BooleanValue) values (%d)" % (val)
    else:
        errorTxt = "Unknown value type: %s" % str(valueType)
        raise ValueError, errorTxt
    
    log.tracef(SQL)
    valueId=system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
    
    SQL = "insert into SfcRecipeDataSimpleValue (RecipeDataId, ValueTypeId, ValueId) values (%d, %d, %d)" % (recipeDataId, valueTypeId, valueId)
    system.db.runUpdateQuery(SQL, tx=tx)

    log.tracef("   ...done inserting a simple value!")

#
def recipeDataMigrator(stepName, stepType, stepId, recipeDataFolderId, recipeData, db, tx):
    key = recipeData.get("key","")
    log.infof("  Migrating a RECIPE with key: %s for step: %s", key, stepName)
    description = recipeData.get("description","")
    label = recipeData.get("label","")
    units = recipeData.get("units","")
    recipeDataTypeId=fetchRecipeDataTypeId("Recipe", db)

    recipeDataId = insertRecipeData(stepName, stepType, stepId, recipeDataFolderId, key, recipeDataTypeId, description, label, units, tx)

    presentationOrder = recipeData.get("pres",1)
    storeTag = recipeData.get("stag","")
    compareTag = recipeData.get("ctag","")
    modeAttribute = recipeData.get("modattr","")
    modeValue = recipeData.get("modattr_val","")
    changeLevel = recipeData.get("chg_lev","")
    recommendedValue = recipeData.get("recc","")
    lowLimit = recipeData.get("lolim","")
    highLimit = recipeData.get("hilim","")

    SQL = "Insert into SfcRecipeDataRecipe (RecipeDataId, PresentationOrder, StoreTag, CompareTag, ModeAttribute, ModeValue, ChangeLevel, RecommendedValue, LowLimit, HighLimit) "\
        "values (%d, %d, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % \
        (recipeDataId, presentationOrder, storeTag, compareTag, modeAttribute, modeValue, changeLevel, recommendedValue, lowLimit, highLimit)
    
    system.db.runUpdateQuery(SQL, tx=tx)

    log.tracef("   ...done inserting a recipe value!")

def output(stepName, stepType, stepId, recipeDataFolderId, recipeData, db, tx):
    key = recipeData.get("key","")
    log.infof("  Migrating an OUTPUT with key: %s for step: %s", key, stepName)
    log.tracef("  Dictionary: %s", str(recipeData))
    description = recipeData.get("description","")
    label = recipeData.get("label","")
    units = recipeData.get("units","")
    recipeDataTypeId=fetchRecipeDataTypeId("Output", db)

    recipeDataId = insertRecipeData(stepName, stepType, stepId, recipeDataFolderId, key, recipeDataTypeId, description, label, units, tx)
    
    outputType = recipeData.get("outputType","Setpoint")
    outputTypeId = fetchOutputTypeId(outputType, db)
    if outputTypeId == None:
        log.warnf("    -- Overriding unknown output type <%s> to <Setpoint> --", outputType)
        outputTypeId = fetchOutputTypeId("Setpoint", db)
    
    valueType = recipeData.get("valueType","String")
    valueType = convertValueType(valueType)
    valueTypeId = fetchValueTypeId(valueType, db)
    
    tag = recipeData.get("tagPath","")
    download = recipeData.get("download",False)
    download = toBit(download)
    timing = recipeData.get("timing",0.0)
    maxTiming = recipeData.get("maxTiming",0.0)
    outputValue = recipeData.get("value",0.0)
    targetValue = recipeData.get("targetValue",0.0)
    writeConfirm = recipeData.get("writeConfirm",False)
    writeConfirm = toBit(writeConfirm)
    
    # Guard against missing string values in places where we need floats.
    if timing == "":
        timing = 0.0
    if maxTiming == "":
        maxTiming = 0.0
    if outputValue == "":
        outputValue = 0.0
    if targetValue == "":
        targetValue = 0.0
        
        '''
    Just because they said it was a float, doesn't mean it is a float!
    If they said it was a float but I can't convert it to a float, then change the type to a string
    '''
    if valueType == "Float" and outputValue <> "NULL":
        if not(isFloat(outputValue)):
            valueType = "String"
            log.warnf("  Overriding the datatype for key <%s> in step <%s> because the value <%s> could not be converted to a float", key, stepName, str(outputValue))
     

    # Insert values into the value table
    SQL = "insert into SfcRecipeDataValue (%sValue) values ('%s')" % (valueType, outputValue)
    log.tracef(SQL)
    outputValueId = system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
    
    SQL = "insert into SfcRecipeDataValue (%sValue) values ('%s')" % (valueType, targetValue)
    log.tracef(SQL)
    targetValueId = system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
    
    SQL = "insert into SfcRecipeDataValue (%sValue) values ('0.0')" % (valueType)
    log.tracef(SQL)
    pvValueId = system.db.runUpdateQuery(SQL, getKey=True, tx=tx)

    SQL = "insert into SfcRecipeDataOutput (RecipeDataId, ValueTypeId, OutputTypeId, Tag, Download, Timing, MaxTiming, OutputValueId, TargetValueId, PVValueId, WriteConfirm) "\
        "values (%s, %s, %s, '%s', %s, %s, %s, %s, %s, %s, %s)"\
        % (str(recipeDataId), str(valueTypeId), str(outputTypeId), tag, str(download), str(timing), str(maxTiming), str(outputValueId), str(targetValueId), str(pvValueId), str(writeConfirm))
    log.tracef(SQL)
    system.db.runUpdateQuery(SQL, tx=tx)
    log.tracef("   ...done inserting an output!")


def outputRamp(stepName, stepType, stepId, recipeDataFolderId, recipeData, db, tx):
    key = recipeData.get("key","")
    log.infof("  Migrating an OUTPUT RAMP with key: %s for step: %s", key, stepName)
    log.tracef("  Dictionary: %s", str(recipeData))
    description = recipeData.get("description","")
    label = recipeData.get("label","")
    units = recipeData.get("units","")
    recipeDataTypeId=fetchRecipeDataTypeId("Output", db)

    recipeDataId = insertRecipeData(stepName, stepType, stepId, recipeDataFolderId, key, recipeDataTypeId, description, label, units, tx)
    
    outputType = recipeData.get("outputType","Setpoint")
    outputTypeId = fetchOutputTypeId(outputType, db)
    if outputTypeId == None:
        log.warnf("    --- Overriding unknown output type <%s> to <Setpoint> ---", outputType)
        outputTypeId = fetchOutputTypeId("Setpoint", db)
    
    valueType = recipeData.get("valueType","String")
    valueType = convertValueType(valueType)
    valueTypeId = fetchValueTypeId(valueType, db)
    
    tag = recipeData.get("tagPath","")
    download = recipeData.get("download",False)
    download = toBit(download)
    timing = recipeData.get("timing",0.0)
    maxTiming = recipeData.get("maxTiming",0.0)
    outputValue = recipeData.get("value",0.0)
    targetValue = recipeData.get("targetValue",0.0)
    writeConfirm = recipeData.get("writeConfirm",False)
    writeConfirm = toBit(writeConfirm)
    
    # Guard against missing string values in places where we need floats.
    if timing == "":
        timing = 0.0
    if maxTiming == "":
        maxTiming = 0.0
    if outputValue == "":
        outputValue = 0.0
    if targetValue == "":
        targetValue = 0.0
        
    # Get the ramp parameteres
    rampTime = recipeData.get("rampTime", 0.0)
    updateFrequency = recipeData.get("updateFrequency", 0.0)

    # Insert values into the value table
    SQL = "insert into SfcRecipeDataValue (%sValue) values ('%s')" % (valueType, outputValue)
    log.tracef(SQL)
    outputValueId = system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
    
    SQL = "insert into SfcRecipeDataValue (%sValue) values ('%s')" % (valueType, targetValue)
    log.tracef(SQL)
    targetValueId = system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
    
    SQL = "insert into SfcRecipeDataValue (%sValue) values ('0.0')" % (valueType)
    log.tracef(SQL)
    pvValueId = system.db.runUpdateQuery(SQL, getKey=True, tx=tx)

    SQL = "insert into SfcRecipeDataOutput (RecipeDataId, ValueTypeId, OutputTypeId, Tag, Download, Timing, MaxTiming, OutputValueId, TargetValueId, PVValueId, WriteConfirm) "\
        "values (%s, %s, %s, '%s', %s, %s, %s, %s, %s, %s, %s)"\
        % (str(recipeDataId), str(valueTypeId), str(outputTypeId), tag, str(download), str(timing), str(maxTiming), str(outputValueId), str(targetValueId), str(pvValueId), str(writeConfirm))
    log.tracef(SQL)
    system.db.runUpdateQuery(SQL, tx=tx)
    
    SQL = "insert into SfcRecipeDataOutputRamp (RecipeDataId, RampTimeMinutes, UpdateFrequencySeconds) "\
        "values (%s, %s, %s)"\
        % (str(recipeDataId), str(rampTime), str(updateFrequency))
    log.tracef(SQL)
    system.db.runUpdateQuery(SQL, tx=tx)
    log.tracef("   ...done inserting an output ramp!")

def input(stepName, stepType, stepId, recipeDataFolderId, recipeData, db, tx):
    key = recipeData.get("key","")
    log.infof("  Migrating an INPUT with key: %s for step: %s", key, stepName)
    log.tracef("  Dictionary: %s", str(recipeData))
    description = recipeData.get("description","")
    label = recipeData.get("label","")
    units = recipeData.get("units","")
    recipeDataTypeId=fetchRecipeDataTypeId("Input", db)

    recipeDataId = insertRecipeData(stepName, stepType, stepId, recipeDataFolderId, key, recipeDataTypeId, description, label, units, tx)
    
    valueType = recipeData.get("valueType","String")
    valueType = convertValueType(valueType)
    valueTypeId = fetchValueTypeId(valueType, db)
    
    tag = recipeData.get("tagPath","")
    targetValue = recipeData.get("targetValue",0.0)
    
    # Guard against missing string values in places where we need floats.
    if targetValue == "":
        targetValue = 0.0        

    # Insert values into the value table
    SQL = "insert into SfcRecipeDataValue (%sValue) values ('%s')" % (valueType, targetValue)
    log.tracef(SQL)
    targetValueId = system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
    
    SQL = "insert into SfcRecipeDataValue (%sValue) values ('0.0')" % (valueType)
    log.tracef(SQL)
    pvValueId = system.db.runUpdateQuery(SQL, getKey=True, tx=tx)

    SQL = "insert into SfcRecipeDataInput (RecipeDataId, ValueTypeId, Tag, TargetValueId, PVValueId) "\
        "values (%s, %s, '%s', %s, %s)"\
        % (str(recipeDataId), str(valueTypeId), tag, str(targetValueId), str(pvValueId))
    log.tracef(SQL)
    system.db.runUpdateQuery(SQL, tx=tx)
    log.tracef("   ...done inserting an input!")
    
def sqc(stepName, stepType, stepId, recipeDataFolderId, recipeData, db, tx):
    key = recipeData.get("key","")    
    log.infof("  Migrating an SQC with key: %s for step: %s", key, stepName)
    log.tracef("  Dictionary: %s", str(recipeData))
    description = recipeData.get("description","")
    label = recipeData.get("label","")
    units = recipeData.get("units","")
    recipeDataTypeId=fetchRecipeDataTypeId("SQC", db)

    recipeDataId = insertRecipeData(stepName, stepType, stepId, recipeDataFolderId, key, recipeDataTypeId, description, label, units, tx)
    
    lowLimit = recipeData.get("lowLimit",0.0)
    targetValue = recipeData.get("targetValue",0.0)
    highLimit = recipeData.get("highLimit",0.0)

    ''' Insert a record into the SfcRecipeDataSQC '''
    SQL = "insert into SfcRecipeDataSQC (RecipeDataId, LowLimit, TargetValue, HighLimit) "\
        "values (%s, %s, %s, %s)"\
        % (str(recipeDataId), str(lowLimit), str(targetValue), str(highLimit))

    log.tracef(SQL)
    system.db.runUpdateQuery(SQL, tx=tx)
    log.tracef("   ...done inserting an input!")

    
def timer(stepName, stepType, stepId, recipeDataFolderId, recipeData, db, tx):
    key = recipeData.get("key","")
    log.infof("  Migrating a TIMER with key: %s for step: %s", key, stepName)
    description = recipeData.get("description","")
    label = recipeData.get("label","")
    units = recipeData.get("units","")
    recipeDataTypeId=fetchRecipeDataTypeId("Timer", db)
    
    recipeDataId = insertRecipeData(stepName, stepType, stepId, recipeDataFolderId, key, recipeDataTypeId, description, label, units, tx)
    
    # The time is the associated data is stored in some goofy format and is irrelevant anyway, the timer is always set at runtime.
    startTime = "01/01/1960 12:00:00"
    
    SQL = "insert into SfcRecipeDataTimer (RecipeDataId, StartTime) values (%d, '%s')" % (recipeDataId, startTime)
    log.tracef(SQL)
    system.db.runUpdateQuery(SQL, tx=tx)
    log.tracef("   ...done inserting a simple value!")    
    
def insertRecipeData(stepName, stepType, stepId, recipeDataFolderId, key, recipeDataTypeId, description, label, units, tx):
    if recipeDataFolderId < 0 or recipeDataFolderId == None:
        SQL = "insert into SfcRecipeData (stepId, RecipeDataKey, RecipeDataTypeId, Description, Label, Units) "\
            " values (?, ?, ?, ?, ?, ?)"
        log.tracef(SQL)
        recipeDataId = system.db.runPrepUpdate(SQL, [stepId, key, recipeDataTypeId, description, label, units], getKey=True, tx=tx)
    else:
        SQL = "insert into SfcRecipeData (stepId, RecipeDataKey, RecipeDataTypeId, Description, Label, Units, RecipeDataFolderId) "\
            " values (?, ?, ?, ?, ?, ?, ?)"
        log.tracef(SQL)
        recipeDataId = system.db.runPrepUpdate(SQL, [stepId, key, recipeDataTypeId, description, label, units, recipeDataFolderId], getKey=True, tx=tx)
    log.tracef("   ...inserted a record into SfcRecipeData with id: %d", recipeDataId)
    return recipeDataId

def convertValueType(valueType):
    if valueType == "int":
        valueType = "Integer"
    elif valueType == "float":
        valueType = "Float"
    elif valueType == "string":
        valueType = "String"
    elif valueType == "boolean":
        valueType = "Boolean"
    else:
        log.warnf("Substituting value type String for unexpected type <%s>" % (valueType))
        valueType = "String"

    return valueType