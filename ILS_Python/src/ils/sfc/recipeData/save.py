'''
Created on Jul 28, 2019

@author: phass

This module deals with storing recipe data that is stored internally in the SFCs into
the database.  
'''

import system, string
import xml.etree.ElementTree as ET
from ils.sfc.recipeData.core import fetchChartIdFromChartPath, fetchStepIdFromChartIdAndStepName, fetchValueTypeId, fetchOutputTypeId, fetchRecipeDataTypeId
from ils.common.config import getDatabaseClient
from ils.common.cast import toBit, isFloat
from ils.common.error import catchError

from ils.log import getLogger
log =getLogger(__name__)

def storeToDatabase(chartPath, chartXML):
    '''
    This gets called once for each chart.
    '''
    log.infof("***************  PYTHON  *******************")
    log.infof("In %s.storeToDatabase(), saving recipe data for chart: %s", __name__, chartPath)
    
    db = getDatabaseClient()
    tx = system.db.beginTransaction(database=db, timeout=86400000)    # timeout is one day
    
    try:
        log.tracef("The incoming chart XML for %s is: %s", chartPath, chartXML)
        chartId = fetchChartIdFromChartPath(chartPath, tx)
        log.tracef("...the chart id is: %d", chartId)
        root = ET.fromstring(chartXML)
        steps = parseXML(root)

        for step in steps:
            processRecipeData(chartId, step, db, tx)

        log.tracef("Committing and closing the transaction.")        
        system.db.commitTransaction(tx)
        system.db.closeTransaction(tx)

    except:
        errorTxt = catchError("Saving recipe data - rolling back database transactions")
        log.errorf(errorTxt)
        system.db.rollbackTransaction(tx)
        system.db.closeTransaction(tx)
        raise Exception("Save Recipe Data Exception: %s", errorTxt)
    
    return chartXML

'''
This is similar to a method of the same name in structureManager.
The main difference is that we don't care about references to another chart.
'''    
def parseXML(root):
    steps = []
    
    for step in root.findall("step"):
        steps = parseStep(step, steps)
            
    for parallel in root.findall("parallel"):
        log.tracef("Found a parallel...")
        for step in parallel.findall("step"):
            steps = parseStep(step, steps)

    log.tracef("========================")
    log.tracef("     steps: %s", str(steps))
    log.tracef("========================")
    return steps


def parseStep(step, steps):
    log.tracef("===================")
    stepId = step.get("id")
    stepName = step.get("name")
    stepType = step.get("factory-id")
    recipeData = ""
    
    for associatedData in step.findall('associated-data'):
        # This looks a lot like a dictionary of dictionaries
        log.tracef("  Raw Text:            %s", str(associatedData.text))
        recipeData = str(associatedData.text)
    
    stepDict = {"id": stepId, "name": stepName, "type": stepType, 'recipeData': recipeData}
    steps.append(stepDict)
    log.tracef("Found a step: %s", str(stepDict))
    return steps


def processRecipeData(chartId, step, db, tx):
    log.tracef(str(step))
    stepUUID = step.get("id")
    stepName = step.get("name")
    stepType = step["type"]
    recipeData = step["recipeData"]
    
    '''
    I've gone back and forth on whether to use the UUID or the chart Path (chartId) / stepName to get the step Id.
    ChartId and StepId are both database indexes.  Both have some issues.  IA totally controls the UUID and I can easily get duplicates
    by copying blocks or importing blocks.  It seems like IA only assigns a UUID when a block is created from the palette.
    I think stepName is maybe not rigorously enforced - I think we could control this by our own validation - so I will use stepName! 
    '''
    stepId = fetchStepIdFromChartIdAndStepName(chartId, stepName, tx)
    log.tracef("Id for step UUID <%s> is %s", stepUUID, str(stepId))
    
    log.infof("  Processing step %s - %s - %s", str(stepId), stepName, stepType)
    log.tracef("    Recipe Data: %s", str(recipeData))
    
    if recipeData in ["", None]:
        log.tracef("...has no recipe data...")
        return
        
    '''
    The associated data is a text string that looks like a dictionary.  
    Python can convert it but is a little picky about some format things
    '''
    recipeData = string.replace(recipeData, "null","\"\"")
    recipeData = string.replace(recipeData, "false","False")
    recipeData = string.replace(recipeData, "true","True")
    
    myDict = system.util.jsonDecode(recipeData)
    folders = {}
        
    for k in myDict.keys():
        recipeList = myDict.get(k)
        
        ''' Process folders first, we need to build the entire folder tree before we can put recipe data into a folder '''
        newRecipeList = []
        for recipeData in recipeList:
            if  type(recipeData) <> dict:
                print "Found recipe data that somehow is not a dictionary (recipe data type: %s for step %s)" % (type(recipeData), stepName)
            else:
                recipeDataType = recipeData.get("recipeDataType", None)
                if string.upper(recipeDataType) == "FOLDER":
                    key = recipeData.get("recipeDataKey","")
                    path = recipeData.get("path", "")
                    description = recipeData.get("description","")
                    label = recipeData.get("label","")
                    
                    log.infof("      Folder: %s", str(key))
                    
                    if path in [None, ""]:
                        parentFolderId = None
                        newPath = key
                    else:
                        parentFolderId = folders[path]
                        newPath = path + "/" + key
                    
                    folderId = insertFolderData(stepId, parentFolderId, key, description, label, tx)
                    folders[newPath] = folderId
                    
                else:
                    newRecipeList.append(recipeData)
            
        log.tracef(" --- DONE WITH FOLDERS ---")
        log.tracef("Folder Dictionary: %s", str(folders))
        log.tracef(" --- PROCESSING RECIPE DATA ---")
        
        for recipeData in newRecipeList:
            if  type(recipeData) == dict:
                log.tracef("Processing Recipe: %s", str(recipeData))
                
                recipeDataType = recipeData.get("recipeDataType", None)
                key = recipeData.get("recipeDataKey","")
                path = recipeData.get("path")
                
                log.infof("      %s: %s %s", recipeDataType, path, key)
            
                if path in [None, ""]:
                    recipeDataFolderId = None
                else:
                    recipeDataFolderId = folders[path]
                
                if string.upper(recipeDataType) == "SIMPLE VALUE":
                    simpleValue(stepId, recipeDataFolderId, recipeData, db, tx)
                elif string.upper(recipeDataType) == "INPUT":
                    inputRecipeData(stepId, recipeDataFolderId, recipeData, db, tx)
                elif string.upper(recipeDataType) == "OUTPUT":
                    outputRecipeData(stepId, recipeDataFolderId, recipeData, db, tx)
                elif string.upper(recipeDataType) == "OUTPUT RAMP":
                    outputRampRecipeData(stepId, recipeDataFolderId, recipeData, db, tx)
                elif string.upper(recipeDataType) == "ARRAY":
                    arrayRecipeData(stepId, recipeDataFolderId, recipeData, db, tx)
                elif string.upper(recipeDataType) == "MATRIX":
                    matrixRecipeData(stepId, recipeDataFolderId, recipeData, db, tx)
                elif string.upper(recipeDataType) == "RECIPE":
                    recipeRecipeData(stepId, recipeDataFolderId, recipeData, db, tx)
                elif string.upper(recipeDataType) == "TIMER":
                    timerRecipeData(stepId, recipeDataFolderId, recipeData, db, tx)
                elif string.upper(recipeDataType) == "SQC":
                    sqcRecipeData(stepId, recipeDataFolderId, recipeData, db, tx)
                else:
                    log.errorf("Unsupported recipe data type: >>>> %s <<<<", recipeDataType)
            

def simpleValue(stepId, recipeDataFolderId, recipeData, db, tx):
    key = recipeData.get("recipeDataKey","")
    val = recipeData.get("value", None)
    log.tracef("  Saving a SIMPLE VALUE with key: %s, value: <%s>", key, val)
    description = recipeData.get("description","")
    label = recipeData.get("label","")
    units = recipeData.get("units","")
    recipeDataTypeId=fetchRecipeDataTypeId("Simple Value", db)
    
    recipeDataId = insertRecipeData(stepId, recipeDataFolderId, key, recipeDataTypeId, description, label, units, tx)
    
    valueType = recipeData.get("valueType","String")
    valueTypeId = fetchValueTypeId(valueType, db)
    valueId = insertRecipeValue(key, recipeDataId, val, valueType, tx)
    
    SQL = "insert into SfcRecipeDataSimpleValue (RecipeDataId, ValueTypeId, ValueId) values (%d, %d, %d)" % (recipeDataId, valueTypeId, valueId)
    
    system.db.runUpdateQuery(SQL, tx=tx)
    log.tracef("   ...done inserting a simple value!")


def inputRecipeData(stepId, recipeDataFolderId, recipeData, db, tx):
    key = recipeData.get("recipeDataKey","")
    log.tracef("  Saving an INPUT with key: %s", key)
    description = recipeData.get("description","")
    label = recipeData.get("label","")
    units = recipeData.get("units","")
    tag = recipeData.get("tag", "")
    
    recipeDataType = recipeData.get("recipeDataType", None)
    recipeDataTypeId=fetchRecipeDataTypeId(recipeDataType, db)
    
    recipeDataId = insertRecipeData(stepId, recipeDataFolderId, key, recipeDataTypeId, description, label, units, tx)
    
    valueType = recipeData.get("valueType","String")
    valueTypeId = fetchValueTypeId(valueType, db)
    
    defaultValue = getDefaultValue(valueType)
    pvValueId = insertRecipeValue(key, recipeDataId, defaultValue, valueType, tx)
    targetValueId = insertRecipeValue(key, recipeDataId, defaultValue, valueType, tx)
    
    SQL = "insert into SfcRecipeDataInput (RecipeDataId, ValueTypeId, Tag, PVValueId, TargetValueId) values (%d, %d, '%s', %d, %d)" % (recipeDataId, valueTypeId, tag, pvValueId, targetValueId)
    
    system.db.runUpdateQuery(SQL, tx=tx)
    log.tracef("   ...done inserting an input!")


def outputRecipeData(stepId, recipeDataFolderId, recipeData, db, tx):
    key = recipeData.get("recipeDataKey","")
    log.tracef("  Saving an OUTPUT with key: %s", key)
    description = recipeData.get("description","")
    label = recipeData.get("label","")
    units = recipeData.get("units","")
    tag = recipeData.get("tag", "")
    download = recipeData.get("download", 0)
    timing = recipeData.get("timing", 0.0)
    maxTiming = recipeData.get("maxTiming", 0.0)
    outputValue = recipeData.get("outputValue", None)
    writeConfirm = recipeData.get("writeConfirm", None)
    
    recipeDataType = recipeData.get("recipeDataType", None)
    recipeDataTypeId=fetchRecipeDataTypeId(recipeDataType, db)
    
    recipeDataId = insertRecipeData(stepId, recipeDataFolderId, key, recipeDataTypeId, description, label, units, tx)
    
    valueType = recipeData.get("valueType","String")
    valueTypeId = fetchValueTypeId(valueType, db)
    
    outputType = recipeData.get("outputType","Setpoint")
    outputTypeId = fetchOutputTypeId(outputType, db)
    
    defaultValue = getDefaultValue(valueType)
    outputValueId = insertRecipeValue(key, recipeDataId, outputValue, valueType, tx)
    pvValueId = insertRecipeValue(key, recipeDataId, defaultValue, valueType, tx)
    targetValueId = insertRecipeValue(key, recipeDataId, defaultValue, valueType, tx)
    
    SQL = "insert into SfcRecipeDataOutput (RecipeDataId, ValueTypeId, OutputTypeId, Tag, Download, Timing, MaxTiming, OutputValueId, PVValueId, TargetValueId, WriteConfirm) "\
        "values (%d, %d, %d, '%s', %d, %f, %f, %d, %d, %d, %d)" % \
        (recipeDataId, valueTypeId, outputTypeId, tag, download, timing, maxTiming, outputValueId, pvValueId, targetValueId, writeConfirm)
        
    system.db.runUpdateQuery(SQL, tx=tx)
    log.tracef("   ...done inserting an output!")
    return recipeDataId


def outputRampRecipeData(stepId, recipeDataFolderId, recipeData, db, tx):
    '''
    An output ramp has everything that an output has plus two additional fields in SfcRecipeDataOutputRamp
    '''
    recipeDataId = outputRecipeData(stepId, recipeDataFolderId, recipeData, db, tx)
    
    rampTimeMinutes = recipeData.get("rampTimeMinutes", 0.0)
    updateFrequencySeconds = recipeData.get("updateFrequencySeconds", 0.0)
    
    SQL = "insert into SfcRecipeDataOutputRamp (RecipeDataId, RampTimeMinutes, UpdateFrequencySeconds) "\
        "values (%d, %f, %f)" %  (recipeDataId, rampTimeMinutes, updateFrequencySeconds)
        
    system.db.runUpdateQuery(SQL, tx=tx)
    log.tracef("   ...done inserting an output ramp!")
    
    
def recipeRecipeData(stepId, recipeDataFolderId, recipeData, db, tx):
    key = recipeData.get("recipeDataKey","")
    log.tracef("  Saving a RECIPE with key: %s", key)
    description = recipeData.get("description","")
    label = recipeData.get("label","")
    units = recipeData.get("units","")
    presentationOrder = recipeData.get("presentationOrder",0)
    storeTag = recipeData.get("storeTag","")
    compareTag = recipeData.get("compareTag","")
    modeAttribute = recipeData.get("modeAttribute","")
    modeValue = recipeData.get("modeValue","")
    changeLevel = recipeData.get("changeLevel","")
    recommendedValue = recipeData.get("recommendedValue","")
    lowLimit = recipeData.get("lowLimit","")
    highLimit = recipeData.get("highLimit","")

    recipeDataType = recipeData.get("recipeDataType", None)
    recipeDataTypeId=fetchRecipeDataTypeId(recipeDataType, db)
    
    recipeDataId = insertRecipeData(stepId, recipeDataFolderId, key, recipeDataTypeId, description, label, units, tx)
    
    SQL = "insert into SfcRecipeDataRecipe (RecipeDataId, PresentationOrder, StoreTag, CompareTag, ModeAttribute, ModeValue, ChangeLevel, RecommendedValue, LowLimit, HighLimit) "\
        "values (%d, %d, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % \
        (recipeDataId, presentationOrder, storeTag, compareTag, modeAttribute, modeValue, changeLevel, recommendedValue, lowLimit, highLimit)

    system.db.runUpdateQuery(SQL, tx=tx)
    log.tracef("   ...done inserting a recipe!")


def sqcRecipeData(stepId, recipeDataFolderId, recipeData, db, tx):
    key = recipeData.get("recipeDataKey","")
    log.tracef("  Saving a SQC with key: %s", key)
    description = recipeData.get("description","")
    label = recipeData.get("label","")
    units = recipeData.get("units","")
    lowLimit = recipeData.get("lowLimit",0.0)
    targetValue = recipeData.get("targetValue",0.0)
    highLimit = recipeData.get("highLimit",0.0)

    recipeDataType = recipeData.get("recipeDataType", None)
    recipeDataTypeId=fetchRecipeDataTypeId(recipeDataType, db)
    
    recipeDataId = insertRecipeData(stepId, recipeDataFolderId, key, recipeDataTypeId, description, label, units, tx)
    
    SQL = "insert into SfcRecipeDataSQC (RecipeDataId, LowLimit, TargetValue, HighLimit) values (%d, %f, %f, %f)" % \
        (recipeDataId, lowLimit, targetValue, highLimit)

    system.db.runUpdateQuery(SQL, tx=tx)
    log.tracef("   ...done inserting an SQC record!")


def timerRecipeData(stepId, recipeDataFolderId, recipeData, db, tx):
    key = recipeData.get("recipeDataKey","")
    log.tracef("  Saving a TIMER with key: %s", key)
    description = recipeData.get("description","")
    label = recipeData.get("label","")
    units = recipeData.get("units","")

    recipeDataType = recipeData.get("recipeDataType", None)
    recipeDataTypeId=fetchRecipeDataTypeId(recipeDataType, db)
    
    recipeDataId = insertRecipeData(stepId, recipeDataFolderId, key, recipeDataTypeId, description, label, units, tx)
    
    SQL = "insert into SfcRecipeDataTimer (RecipeDataId) values (%d)" % (recipeDataId)
    system.db.runUpdateQuery(SQL, tx=tx)
    log.tracef("   ...done inserting a timer!")
    
    
def arrayRecipeData(stepId, recipeDataFolderId, recipeData, db, tx):
    key = recipeData.get("recipeDataKey","")
    log.tracef("  Saving an ARRAY with key: %s", key)
    description = recipeData.get("description","")
    label = recipeData.get("label","")
    units = recipeData.get("units","")
    
    indexKey = recipeData.get("indexKey","")
    indexKeyId = fetchIndexKeyId(indexKey, db)

    recipeDataTypeId=fetchRecipeDataTypeId("Array", db)
    
    recipeDataId = insertRecipeData(stepId, recipeDataFolderId, key, recipeDataTypeId, description, label, units, tx)
    
    valueType = recipeData.get("valueType","String")
    valueTypeId = fetchValueTypeId(valueType, db)
    
    ''' Insert a record into SfcRecipeDataArray '''
    if indexKeyId == None:
        SQL = "insert into SfcRecipeDataArray (RecipeDataId, ValueTypeId) values (%d, %d)" % (recipeDataId, valueTypeId)
    else:
        SQL = "insert into SfcRecipeDataArray (RecipeDataId, ValueTypeId, IndexKeyId) values (%d, %d, %d)" % (recipeDataId, valueTypeId, indexKeyId)
    system.db.runUpdateQuery(SQL, tx=tx)
    
    ''' Insert the values '''
    vals = recipeData.get("vals",[])
    idx = 0
    for val in vals:
        valueId = insertRecipeValue(key, recipeDataId, val, valueType, tx)
        idx = idx + 1
        SQL = "insert into SfcRecipeDataArrayElement (RecipeDataId, ArrayIndex, ValueId) values (%d, %d, %d)" % (recipeDataId, idx, valueId)
        system.db.runUpdateQuery(SQL, tx=tx)
        log.tracef("      ...inserted value %s with index %d", str(val), idx)
        
    log.tracef("   ...done inserting an array!")
    
    
def matrixRecipeData(stepId, recipeDataFolderId, recipeData, db, tx):
    key = recipeData.get("recipeDataKey","")
    log.tracef("  Saving a MATRIX with key: %s", key)
    description = recipeData.get("description","")
    label = recipeData.get("label","")
    units = recipeData.get("units","")
    rows = recipeData.get("rows", 0)
    columns = recipeData.get("columns", 0)
    
    rowIndexKey = recipeData.get("rowIndexKey","")
    rowIndexKeyId = fetchIndexKeyId(rowIndexKey, db)
    
    columnIndexKey = recipeData.get("columnIndexKey","")
    columnIndexKeyId = fetchIndexKeyId(columnIndexKey, db)

    recipeDataTypeId=fetchRecipeDataTypeId("Matrix", db)
    
    recipeDataId = insertRecipeData(stepId, recipeDataFolderId, key, recipeDataTypeId, description, label, units, tx)
    
    valueType = recipeData.get("valueType","Float")
    valueTypeId = fetchValueTypeId(valueType, db)
    
    ''' Insert a record into SfcRecipeDataMatrix '''
    colTxt = ""
    valTxt = ""
    if rowIndexKeyId <> None:
        colTxt = ", RowIndexKeyId"
        valTxt = ", %d" % (rowIndexKeyId)
                         
    if columnIndexKeyId <> None:
        colTxt = colTxt + ", ColumnIndexKeyId"
        valTxt = valTxt + ", %d" % (columnIndexKeyId)

    SQL = "insert into SfcRecipeDataMatrix(RecipeDataId, ValueTypeId, rows, columns %s) values (%d, %d, %d, %d %s)" % (colTxt, recipeDataId, valueTypeId, rows, columns, valTxt)
    log.tracef("SQL: %s", SQL)
    system.db.runUpdateQuery(SQL, tx=tx)
    
    ''' Insert the values '''
    vals = recipeData.get("vals",[])
    idx = 0
    rowIdx = 0
    columnIdx = 0
    for val in vals:
        valueId = insertRecipeValue(key, recipeDataId, val, valueType, tx)
        SQL = "insert into SfcRecipeDataMatrixElement (RecipeDataId, RowIndex, ColumnIndex, ValueId) values (%d, %d, %d, %d)" % (recipeDataId, rowIdx, columnIdx, valueId)
        
        columnIdx = columnIdx + 1
        
        if columnIdx >= columns:
            columnIdx = 0
            rowIdx = rowIdx + 1

        print "Inserted Matrix value: ", SQL
        system.db.runUpdateQuery(SQL, tx=tx)
        log.tracef("      ...inserted value %s with index %d", str(val), idx)
        
    log.tracef("   ...done inserting a matrix!")


def insertRecipeData(stepId, recipeDataFolderId, key, recipeDataTypeId, description, label, units, tx):
    if recipeDataFolderId < 0 or recipeDataFolderId == None:
        SQL = "insert into SfcRecipeData (stepId, RecipeDataKey, RecipeDataTypeId, Description, Label, Units) values (?, ?, ?, ?, ?, ?)"
        log.tracef(SQL)
        recipeDataId = system.db.runPrepUpdate(SQL, [stepId, key, recipeDataTypeId, description, label, units], getKey=True, tx=tx)
    else:
        SQL = "insert into SfcRecipeData (stepId, RecipeDataKey, RecipeDataTypeId, Description, Label, Units, RecipeDataFolderId) values (?, ?, ?, ?, ?, ?, ?)"
        log.tracef(SQL)
        recipeDataId = system.db.runPrepUpdate(SQL, [stepId, key, recipeDataTypeId, description, label, units, recipeDataFolderId], getKey=True, tx=tx)
    log.tracef("   ...inserted a record into SfcRecipeData with id: %d", recipeDataId)
    return recipeDataId


def insertFolderData(stepId, parentFolderId, key, description, label, tx):
    if parentFolderId < 0 or parentFolderId == None:
        SQL = "insert into SfcRecipeDataFolder (stepId, RecipeDataKey, Description, Label) values (?, ?, ?, ?)"
        log.tracef(SQL)
        folderId = system.db.runPrepUpdate(SQL, [stepId, key, description, label], getKey=True, tx=tx)
    else:
        SQL = "insert into SfcRecipeDataFolder (stepId, RecipeDataKey, Description, Label, ParentRecipeDataFolderId) values (?, ?, ?, ?, ?)"
        log.tracef(SQL)
        folderId = system.db.runPrepUpdate(SQL, [stepId, key, description, label, parentFolderId], getKey=True, tx=tx)
    
    log.tracef("   ...inserted a record into SfcRecipeDataFolder with id: %d", folderId)
    return folderId


def insertRecipeValue(key, recipeDataId, val, valueType, tx):
    if val in ["NO-VALUE", "****"]:
        val = "NULL"
        
    '''
    Just because they said it was a float, doesn't mean it is a float!
    If they said it was a float but I can't convert it to a float, then change the type to a string
    '''
    if valueType == "Float" and val <> "NULL":
        if not(isFloat(val)):
            valueType = "String"
            log.warnf("  Overriding the datatype for key <%s> because the value <%s> could not be converted to a float", key, str(val))
    
    if valueType == "Float":
        if str(val) == "False":
            log.warnf("--Overriding False for a float to 0.0--")
            val = 0.0
        elif str(val) == "True":
            log.warnf("--Overriding True for a float to 1.0--")
            val = 1.0
        elif val in ["NULL", None, "None"]:
            log.warbf("--Overriding NULL for a float to 0.0--")
            val = 0.0
        SQL = "insert into SfcRecipeDataValue (RecipeDataId, FloatValue) values (?,?)"
        
    elif valueType == "Integer":
        if val in ["NULL", None, "None"]:
            log.warnf("--Overriding NULL for an integer to 0.0--")
            val = 0.0
        SQL = "insert into SfcRecipeDataValue (RecipeDataId, IntegerValue) values (?,?)"
    
    elif valueType == "String":
        '''  I think that single quotes will already be escaped (by the recipe data internalizer) when we get this far '''
#        val = '"' + val[1:len(val)-1] + '"'
#        print "New Val: <%s>", val
        SQL = "insert into SfcRecipeDataValue (RecipeDataId, StringValue) values (?,?)"
    
    elif valueType == "Boolean":
        val=toBit(val)
        SQL = "insert into SfcRecipeDataValue (RecipeDataId, BooleanValue) values (?,?)"
    
    else:
        errorTxt = "Unknown value type: %s" % str(valueType)
        raise ValueError, errorTxt
    
    log.tracef(SQL)
    valueId=system.db.runPrepUpdate(SQL, [recipeDataId, val], getKey=True, tx=tx)
    return valueId


def getDefaultValue(valueType):
    '''
    When inserting recipe data, there may need to be dummy values used as placeholders.
    The value doesn't matter but the type does!
    '''
    if string.upper(valueType) == "FLOAT":
        val = 0.0
    elif string.upper(valueType) == "INTEGER":
        val = 0
    elif string.upper(valueType) == "STRING":
        val = ""
    elif string.upper(valueType) == "BOOLEAN":
        val = 0
        
    return val


def fetchIndexKeyId(indexKey, db):
    SQL = "select KeyId from SfcRecipeDataKeyMaster where KeyName = '%s' " % (indexKey)
    idx = system.db.runScalarQuery(SQL, db)
    return idx