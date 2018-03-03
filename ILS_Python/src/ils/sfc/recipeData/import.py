'''
Created on Feb 17, 2018

@author: phass
'''

import xml.etree.ElementTree as ET
import sys, system, string, traceback
from ils.migration.common import lookupOPCServerAndScanClass
from ils.migration.common import lookupHDAServer
from ils.common.database import getUnitId
from ils.common.database import getPostId
from ils.common.database import lookup
from ils.common.cast import toBit
from ils.common.config import getDatabaseClient
log=system.util.getLogger("com.ils.sfc.import")

def importRecipeDataCallback(event):
    db = getDatabaseClient()
    filename = system.file.openFile(".xml")
    if filename != None:
        importRecipeData(filename, db)

def importRecipeData(filename, db):
    log.infof("In %s.importRecipeData()", __name__)
    tree = ET.parse(filename)
    root = tree.getroot()
    
    stepTypes = loadStepTypes(db)
    recipeDataTypes = loadRecipeDataTypes(db)
    valueTypes = loadValueTypes(db)
    outputTypes = loadOutputTypes(db)
    
    '''
    The import file is a list of charts, it does not contain the hierarchy.  The import is flat, i.e, not nested.
    Before we import, we need to delete.  Hopefully there are enough cascade deletes that all we have to do is delete the chart
    and the steps and recipe data will follow.
    '''
    
    txId = system.db.beginTransaction(db)
    
    rows = 0
    for chart in root.findall("chart"):
        chartPath = chart.get("chartPath")

        log.tracef("Deleting Chart: %s", chartPath)
        SQL = "delete from SfcChart where chartPath = '%s'" % chartPath
        r = system.db.runUpdateQuery(SQL, tx=txId)
        rows = rows + r
    
    system.db.commitTransaction(txId)
    log.infof("Deleted %d charts and their associated steps and recipe data", rows) 
   
    '''
    Now insert charts, steps, and recipe data
    '''
    
    for chart in root.findall("chart"):
        chartPath = chart.get("chartPath")
        chartId = insertChart(chartPath, txId)
        
        for step in chart.findall("step"):
            stepName = step.get("stepName")
            stepUUID = step.get("stepUUID")
            stepType = step.get("stepType")
            stepTypeId = stepTypes.get(stepType, -99)
            stepId = insertStep(chartId, stepUUID, stepName, stepTypeId, txId)
            
            for recipe in step.findall("recipe"):
                recipeDataType = recipe.get("recipeDataType")
                recipeDataTypeId = recipeDataTypes.get(recipeDataType, -99)
                recipeDataKey = recipe.get("recipeDataKey")
                label = recipe.get("label")
                description = recipe.get("description")
                
                if recipeDataType == "Simple Value":
                    valueType = recipe.get("valueType")
                    valueTypeId = valueTypes.get(valueType, -99)
                    val = recipe.get("value")
                    units = recipe.get("units", "")
                    recipeDataId = insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, units, txId)
                    insertSimpleRecipeData(recipeDataId, valueType, valueTypeId, val, txId)
                
                elif recipeDataType in ["Output", "Output Ramp"]:
                    valueType = recipe.get("valueType")
                    valueTypeId = valueTypes.get(valueType, -99)
                    val = recipe.get("value")
                    units = recipe.get("units", "")
                    outputType = recipe.get("outputType", "")
                    outputTypeId = outputTypes.get(outputType, -99)
                    tag = recipe.get("tag", "")
                    download = recipe.get("download", "True")
                    timing = recipe.get("timing", "0.0")
                    maxTiming = recipe.get("maxTiming", "0.0")
                    writeConfirm = recipe.get("writeConfirm", "True")
                    
                    recipeDataId = insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, units, txId)
                    insertOutputRecipeData(recipeDataId, valueType, valueTypeId, outputType, outputTypeId, tag, download, timing, maxTiming, val, writeConfirm, txId)
                    
                    if recipeDataType == "Output Ramp":
                        rampTimeMinutes = recipe.get("rampTimeMinutes", "0.0")
                        updateFrequencySeconds = recipe.get("updateFrequencySeconds", "0.0")
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
      
                elif recipeDataType == "Timer":
                    units = recipe.get("units", "")
                    recipeDataId = insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, units, txId)
                    insertTimerRecipeData(recipeDataId, txId)
                    
                else:
                    print "**** Unsupported Recipe Data Type: %s ****" % (recipeDataType)
                    
    system.db.commitTransaction(txId)
    system.db.closeTransaction(txId)

def insertChart(chartPath, txId):
    log.tracef("Inserting chart: %s...", chartPath)
    SQL = "insert into SfcChart (ChartPath) values ('%s')" % (chartPath)
    chartId = system.db.runUpdateQuery(SQL, tx=txId, getKey=True)
    log.tracef("...inserted chart with id: %d", chartId)
    return chartId

def insertStep(chartId, stepUUID, stepName, stepTypeId, txId):
    log.tracef("   Inserting step: %s - type: %d...", stepName, stepTypeId)
    SQL = "insert into SfcStep (StepUUID, StepName, StepTypeId, ChartId) values ('%s', '%s', %s, %s)" % (stepUUID, stepName, str(stepTypeId), str(chartId))
    stepId = system.db.runUpdateQuery(SQL, tx=txId, getKey=True)
    log.tracef("      ...inserted step with id: %d", stepId)
    return stepId

def insertRecipeData(stepId, key, recipeDataType, recipeDataTypeId, label, description, units, txId):
    log.tracef("      Inserting recipe data:  %s - %s...", key, recipeDataType)
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
    log.tracef("          Inserting an Output recipe data...")
    outputValueId = insertRecipeDataValue(valueType, val, txId)
    targetValueId = insertRecipeDataValue(valueType, 0.0, txId)
    pvValueId = insertRecipeDataValue(valueType, 0.0, txId)
    SQL = "insert into SfcRecipeDataOutput (recipeDataId, valueTypeId, outputTypeId, tag, download, timing, maxTiming, outputValueId, targetValueId, pvValueId, writeConfirm) "\
        "values (%d, %d, %d, '%s', '%s', %s, %s, %d, %d, %d, '%s')" % \
        (recipeDataId, valueTypeId, outputTypeId, tag, download, str(timing), str(maxTiming), outputValueId, targetValueId, pvValueId, writeConfirm)
    system.db.runUpdateQuery(SQL, tx=txId)

def insertOutputRampRecipeData(recipeDataId, rampTimeMinutes, updateFrequencySeconds, txId):
    log.tracef("          Inserting an Output Ramp recipe data...")
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
    log.tracef("          Inserting a simple Value...")
    valueId = insertRecipeDataValue(valueType, val, txId)
    SQL = "insert into SfcRecipeDataArrayElement (recipeDataId, arrayIndex, ValueId) values (%d, %d, %d)" % (recipeDataId, int(arrayIndex), valueId)
    system.db.runUpdateQuery(SQL, tx=txId)
    
def insertTimerRecipeData(recipeDataId, txId):
    log.tracef("          Inserting a Timer...")
    SQL = "insert into SfcRecipeDataTimer (recipeDataId) values (%d)" % (recipeDataId)
    system.db.runUpdateQuery(SQL, tx=txId)
    
def insertRecipeDataValue(valueType, val, txId):
    log.tracef("        Inserting a recipe data value (type: %s, value: %s)...", valueType, val)
    
    if valueType == "String":
        SQL = "insert into SfcRecipeDataValue (StringValue) values ('%s')" % (val)
    elif valueType == "Integer":
        SQL = "insert into SfcRecipeDataValue (IntegerValue) values (%d)" % (int(val))
    elif valueType == "Float":
        SQL = "insert into SfcRecipeDataValue (FloatValue) values (%f)" % (float(val))
    elif valueType == "Boolean":
        SQL = "insert into SfcRecipeDataValue (BooleanValue) values ('%s')" % (val)
    
    print SQL
    valueId = system.db.runUpdateQuery(SQL, tx=txId, getKey=True)
    return valueId

''' -----------------------------------------------------
    Generic utilities
    ----------------------------------------------------- '''

def loadStepTypes(db):
    SQL = "select StepTypeId, StepType from SfcStepType"
    pds = system.db.runQuery(SQL, db)
    
    stepTypes = {}
    for record in pds:
        stepTypes[record["StepType"]] = record["StepTypeId"]
    
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
        valueTypes[record["ValueType"]] = record["ValueTypeId"]
    
    return valueTypes

def insertIndexKey(indexKey, txId):
    SQL = "select ValueTypeId, ValueType from SfcValueType"
    pds = system.db.runQuery(SQL, tx=txId)
    
    valueTypes = {}
    for record in pds:
        valueTypes[record["ValueType"]] = record["ValueTypeId"]
    
    return valueTypes