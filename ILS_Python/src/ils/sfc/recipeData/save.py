'''
Created on Jul 28, 2019

@author: phass
'''

import system, os, string
import xml.etree.ElementTree as ET
from ils.sfc.recipeData.hierarchyWithBrowser import fetchHierarchy, getChildren
from ils.sfc.recipeData.core import fetchStepTypeIdFromFactoryId, fetchStepIdFromUUID, fetchChartIdFromChartPath, fetchStepIdFromChartIdAndStepName,\
        fetchValueTypeId, fetchOutputTypeId, fetchRecipeDataTypeId
from ils.common.config import getDatabaseClient
from ils.common.cast import toBit, isFloat
from ils.common.error import catchError, notifyError

log=system.util.getLogger("com.ils.sfc.recipeData.save")


def storeToDatabase(chartPath, chartXML):
    log.infof("***************  PYTHON  *******************")
    log.infof("In %s.storeToDatabase()", __name__)
    
    db = getDatabaseClient()
    tx = system.db.beginTransaction(database=db, timeout=86400000)    # timeout is one day
    
    try:
        log.tracef("The incoming chart XML is: %s", chartXML)
        chartId = fetchChartIdFromChartPath(chartPath, tx)
        root = ET.fromstring(chartXML)
        steps = parseXML(root)

        print "**********  PROCESSING STEPS **************"
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

'''
This is similar to a method of the same name in structureManager.
The main difference is that we don't care about references to another chart.
'''    
def parseXML(root):
    steps = []
    
    for step in root.findall("step"):
        steps = parseStep(step, steps)
            
    for parallel in root.findall("parallel"):
        print "Found a parallel..."
        for step in parallel.findall("step"):
            steps = parseStep(step, steps)

    print "========================"
    print "     steps: ", steps
    print "========================"
    return steps

def parseStep(step, steps):
    print "==================="
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
    print "Found a step: ", stepDict

    return steps
    
def processRecipeData(chartId, step, db, tx):
    print str(step)
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
    
    log.tracef("Processing step %s - %s - %s - %s", str(stepId), stepName, stepType, str(recipeData))
    
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
        
    for k in myDict.keys():
        recipeList = myDict.get(k)
        for recipeData in recipeList:
            log.tracef("Processing Recipe: %s", str(recipeData))
            
            recipeDataType = recipeData.get("recipeDataType", None)
            log.tracef("  Type: %s", recipeDataType)
            
            parentFolder = recipeData.get("parent")
        
            if parentFolder == None:
                recipeDataFolderId = None
            else:
                recipeDataFolderId = -1
            
            if string.upper(recipeDataType) == "SIMPLE VALUE":
                simpleValue(stepId, recipeDataFolderId, recipeData, db, tx)
            elif string.upper(recipeDataType) == "INPUT":
                inputRecipeData(stepId, recipeDataFolderId, recipeData, db, tx)
            elif string.upper(recipeDataType) == "ARRAY":
                arrayRecipeData(stepId, recipeDataFolderId, recipeData, db, tx)
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
    recipeDataTypeId=fetchRecipeDataTypeId("Input", db)
    
    recipeDataId = insertRecipeData(stepId, recipeDataFolderId, key, recipeDataTypeId, description, label, units, tx)
    
    valueType = recipeData.get("valueType","String")
    valueTypeId = fetchValueTypeId(valueType, db)
    
    defaultValue = getDefaultValue(valueType)
    pvValueId = insertRecipeValue(key, recipeDataId, defaultValue, valueType, tx)
    targetValueId = insertRecipeValue(key, recipeDataId, defaultValue, valueType, tx)
    
    SQL = "insert into SfcRecipeDataInput (RecipeDataId, ValueTypeId, Tag, PVValueId, TargetValueId) values (%d, %d, '%s', %d, %d)" % (recipeDataId, valueTypeId, tag, pvValueId, targetValueId)
    system.db.runUpdateQuery(SQL, tx=tx)

    log.tracef("   ...done inserting an input!")
    
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
        
    log.tracef("   ...done inserting an input!")


def insertRecipeData(stepId, recipeDataFolderId, key, recipeDataTypeId, description, label, units, tx):
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
            log.info("--Overriding False for a float to 0.0--")
            val = 0.0
        elif str(val) == "True":
            log.info("--Overriding True for a float to 1.0--")
            val = 1.0
        SQL = "insert into SfcRecipeDataValue (RecipeDataId, FloatValue) values (?,?)"
    elif valueType == "Integer":
        SQL = "insert into SfcRecipeDataValue (RecipeDataId, IntegerValue) values (?,?)"
    elif valueType == "String":
        '''  I think that single quotes will already be escaped (by the recipe data internalizer) when we get this far '''
#        val = '"' + val[1:len(val)-1] + '"'
#        print "New Val: <%s>", val
        SQL = "insert into SfcRecipeDataValue (RecipeDataId, StringValue) values (?,?)"
        print "SQL: ", SQL
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