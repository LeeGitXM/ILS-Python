'''
Created on Jan 9, 2017

@author: phass
'''

import system, string, time
import xml.etree.ElementTree as ET
from ils.common.error import catch
from ils.common.cast import toBit
from ils.sfc.recipeData.core import fetchValueTypeId, fetchOutputTypeId, fetchRecipeDataTypeId, fetchStepIdFromUUID
from ils.common.config import getTagProvider
from com.sun.org.apache.xalan.internal.xslt import Process
log = system.util.getLogger("com.ils.sfc.python.recipeDataMigrator")

def migrateChart(chartPath, resourceId, chartResourceAsXML, db):

    provider = getTagProvider()
    migrationEnabled = system.tag.read("[%s]Configuration/SFC/sfcMigrationEnabled" % (provider)).value
    if not(migrationEnabled):
        log.tracef("Recipe Data migration is disabled!")
        return
    
    log.infof("***************")
    log.infof("Migrating a charts recipe data(PYTHON) (%s-%s) ...", chartPath, str(resourceId))
    log.infof("***************")
    
    # This runs immediately after the chart hierarchy analysis which has a number of database transactions.  Give those time to get
    # committed to the database.  This only runs in designer during migration, so we are not super concerned about performance.
    time.sleep(5)
        
    log.tracef(chartResourceAsXML)
    
    log.tracef("parsing the tree...")
    root = ET.fromstring(chartResourceAsXML)
    
    try:
        tx = system.db.beginTransaction(db)
        
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
        
        system.db.commitTransaction(tx)
        system.db.closeTransaction(tx)
    except:
        errorTxt = catch("Migrating Recipe Data - rolling back transactions")
        log.errorf(errorTxt)
        system.db.rollbackTransaction(tx)
        system.db.closeTransaction(tx)

def processStep(step, db, tx):
    log.tracef("==============")
            
    stepName = step.get("name")
    stepUUID = step.get("id")
    stepId = fetchStepIdFromUUID(stepUUID, tx)
    stepType = step.get("factory-id")
    log.tracef("Found a step %s - %s - %s- %d....", stepName, stepType, stepUUID, stepId)
    
    SQL = "delete from SfcRecipeData where StepId = %d" % stepId
    log.tracef(SQL)
    rows=system.db.runUpdateQuery(SQL, tx=tx)
    log.tracef("...Deleted %d rows from SfcRecipeData", rows)
    
    for associatedData in step.findall('associated-data'):

        # This looks a lot like a dictionary of dictionaries
#        log.tracef("  Raw Text:            %s", associatedData.text)
        
        # The associated data is a text string that looks like a dictionary.  Python can convert it but is a little picky about some format things
        txt=associatedData.text
        txt = string.replace(txt, "null","\"\"")
        txt = string.replace(txt, "false","False")
        txt = string.replace(txt, "true","True")
#        log.tracef("  Converted Text:      %s", txt)
        myDict = eval(txt)
        log.tracef("  Dictionary:          %s", str(myDict))
        
        for k in myDict.keys():
            recipeData = myDict.get(k)
            recipeDataType = getRecipeDataTypeFromAssociatedData(recipeData)
            
            if recipeDataType == "Output":
                output(stepName, stepType, stepId, recipeData, db, tx)
            elif recipeDataType == "Value":
                simpleValue(stepName, stepType, stepId, recipeData, db, tx)
            elif recipeDataType == "Timer":
                timer(stepName, stepType, stepId, recipeData, db, tx)

            elif recipeDataType == None:
                log.trace("Skipping a NULL value")
            else:
                raise ValueError, "Unexpected type of recipe data: %s" % recipeDataType
    
def getRecipeDataTypeFromAssociatedData(recipeData):
    try:
        recipeDataType = recipeData.get("class", None)
    except:
        recipeDataType = None
        
    return recipeDataType

def simpleValue(stepName, stepType, stepId, recipeData, db, tx):
    key = recipeData.get("key","")
    log.infof("Migrating a SIMPLE VALUE with key: %s for step: %s", key, stepName)
    description = recipeData.get("description","")
    label = recipeData.get("label","")
    units = recipeData.get("units","")
    recipeDataTypeId=fetchRecipeDataTypeId("Simple Value", db)
    
    recipeDataId = insertRecipeData(stepName, stepType, stepId, key, recipeDataTypeId, description, label, units, tx)
    
    valueType = recipeData.get("valueType","String")
    valueType = convertValueType(valueType)
    valueTypeId = fetchValueTypeId(valueType, db)
    val = recipeData.get("value", None)
    
    if valueType == "Float":
        SQL = "insert into SfcRecipeDataSimpleValue (RecipeDataId, ValueTypeId, FloatValue) values (%d, %d, %s)" % (recipeDataId, valueTypeId, str(val))
    elif valueType == "Integer":
        SQL = "insert into SfcRecipeDataSimpleValue (RecipeDataId, ValueTypeId, IntegerValue) values (%d, %d, %s)" % (recipeDataId, valueTypeId, str(val))
    elif valueType == "String":
        SQL = "insert into SfcRecipeDataSimpleValue (RecipeDataId, ValueTypeId, StringValue) values (%d, %d, '%s')" % (recipeDataId, valueTypeId, str(val))
    else:
        errorTxt = "Unknown value type: %s" % str(valueType)
        raise ValueError, errorTxt
    
    log.tracef(SQL)
    system.db.runUpdateQuery(SQL, tx=tx)
    log.tracef("   ...done inserting a simple value!")

def output(stepName, stepType, stepId, recipeData, db, tx):
    key = recipeData.get("key","")
    log.infof("Migrating an OUTPUT with key: %s for step: %s", key, stepName)
    log.tracef("  Dictionary: %s", str(recipeData))
    description = recipeData.get("description","")
    label = recipeData.get("label","")
    units = recipeData.get("units","")
    recipeDataTypeId=fetchRecipeDataTypeId("Output", db)

    recipeDataId = insertRecipeData(stepName, stepType, stepId, key, recipeDataTypeId, description, label, units, tx)
    
    outputType = recipeData.get("outputType","Setpoint")
    outputTypeId = fetchOutputTypeId(outputType, db)
    
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
    
    SQL = "insert into SfcRecipeDataOutput (RecipeDataId, ValueTypeId, OutputTypeId, Tag, Download, Timing, MaxTiming, OutputValue, TargetValue, WriteConfirm) "\
        "values (%d, %d, %d, '%s', %s, %s, %s, %s, %s, %s)"\
        % (recipeDataId, valueTypeId, outputTypeId, tag, str(download), str(timing), str(maxTiming), str(outputValue), str(targetValue), str(writeConfirm))

    log.tracef(SQL)
    system.db.runUpdateQuery(SQL, tx=tx)
    log.tracef("   ...done inserting an output!")
    
def timer(stepName, stepType, stepId, recipeData, db, tx):
    key = recipeData.get("key","")
    log.infof("Migrating a TIMER with key: %s for step: %s", key, stepName)
    description = recipeData.get("description","")
    label = recipeData.get("label","")
    units = recipeData.get("units","")
    recipeDataTypeId=fetchRecipeDataTypeId("Timer", db)
    
    recipeDataId = insertRecipeData(stepName, stepType, stepId, key, recipeDataTypeId, description, label, units, tx)
    
    # The time is the associated data is stored in some goofy format and is irrelevant anyway, the timer is always set at runtime.
    startTime = "01/01/1960 12:00:00"
    
    SQL = "insert into SfcRecipeDataTimer (RecipeDataId, StartTime) values (%d, '%s')" % (recipeDataId, startTime)
    log.tracef(SQL)
    system.db.runUpdateQuery(SQL, tx=tx)
    log.tracef("   ...done inserting a simple value!")    
    
def insertRecipeData(stepName, stepType, stepId, key, recipeDataTypeId, description, label, units, tx):
    SQL = "insert into SfcRecipeData (stepId, RecipeDataKey, RecipeDataTypeId, Description, Label, Units) "\
        " values ('%s', '%s', %d, '%s', '%s', '%s')" % (stepId, key, recipeDataTypeId, description, label, units)
    log.tracef(SQL)
    recipeDataId = system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
    log.tracef("   ...inserted a record into SfcRecipeData with id: %d", recipeDataId)
    return recipeDataId

def convertValueType(valueType):
    if valueType == "int":
        valueType = "Integer"
    elif valueType == "float":
        valueType = "Float"
    elif valueType == "string":
        valueType = "String"
    else:
        log.warnf("Substituting value type String for unexpected type <%s>" % (valueType))
        valueType = "String"

    return valueType