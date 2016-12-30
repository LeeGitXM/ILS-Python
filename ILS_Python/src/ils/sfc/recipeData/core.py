'''
Created on Nov 30, 2016

@author: phassler
'''

import system
LOCAL_SCOPE = "local"
SUPERIOR_SCOPE = "superior"
PHASE_SCOPE = "phase"
OPERATION_SCOPE = "operation"
GLOBAL_SCOPE = "global"

PHASE_STEP = "Phase"
OPERATION_STEP = "Operation"
UNIT_PROCEDURE_STEP = "Unit Procedure"

SIMPLE_VALUE = "Simple Value"

def getTargetStep(chartUUID, stepUUID, scope, db):
    
    if scope == LOCAL_SCOPE:
        return stepUUID

    elif scope == SUPERIOR_SCOPE:
        superiorStep = fetchSuperiorStep(chartUUID, db)
        stepUUID = superiorStep["StepUUID"]
        return stepUUID
    
    elif scope == PHASE_SCOPE:
        phaseStep = walkUpHieracrchy(chartUUID, PHASE_STEP, db)
        stepUUID = phaseStep["StepUUID"]       
        return stepUUID
    
    elif scope == OPERATION_SCOPE:
        operationStep = walkUpHieracrchy(chartUUID, OPERATION_STEP, db)
        stepUUID = operationStep["StepUUID"]       
        return stepUUID
    
    elif scope == GLOBAL_SCOPE:
        unitProcedureStep = walkUpHieracrchy(chartUUID, UNIT_PROCEDURE_STEP, db)
        stepUUID = unitProcedureStep["StepUUID"]       
        return stepUUID
        
    else:
        print "Undefined scope: ", scope
        
    return -1 

def walkUpHieracrchy(chartUUID, stepType, db):
    thisStepType = ""
    while thisStepType <> stepType:
        print "Fetching step superior to chart: ", chartUUID
        superiorStep = fetchSuperiorStep(chartUUID, db)
        thisStepType = superiorStep["StepType"]
        chartUUID = superiorStep["ChartUUID"]
    return superiorStep

def fetchSuperiorStep(chartUUID, db):
    SQL = "select * from SfcHierarchyView where childChartUUID = '%s'" % (chartUUID)
    pds = system.db.runQuery(SQL, db)
    superiorStep=pds[0]
    return superiorStep

def fetchRecipeData(stepUUID, key, attribute, db):
    SQL = "select * from SfcRecipeDataView where stepUUID = '%s' and RecipeDataKey = '%s' " % (stepUUID, key) 
    pds = system.db.runQuery(SQL, db)
    if len(pds) == 0:
        print "Error the key was not found"
        return -1
    
    if len(pds) > 1:
        print "Error multiple records were found"
        return -1
    
    record = pds[0]
    recipeDataId = record["RecipeDataId"]
    if record["RecipeDataType"]  == SIMPLE_VALUE:
        SQL = "select * from SfcRecipeDataSimpleValueView where RecipeDataId = '%s'" % (recipeDataId)
        pds = system.db.runQuery(SQL, db)
        record = pds[0]
        dataType = record['DataType']
        val = record["%sValue" % dataType]
    
    return val

def getChartUUID(chartProperties):
    chartUUID = chartProperties.get("chartUUID", "-1")
    return chartUUID

def getStepUUID(stepProperties):
    stepUUID = stepProperties.get("stepUUID", "-1")
    return stepUUID

# This handles a simple "key.attribute" notation, but does not handle folder reference or arrays
def splitKey(keyAndAttribute):
    tokens = keyAndAttribute.split(".")
    key = tokens[0]
    attribute = tokens[1]
    return key, attribute

def fetchStepTypeIdFromFactoryId(factoryId, database):
    SQL = "select StepTypeId from SfcStepType where FactoryId = '%s'" % (factoryId)
    stepTypeId = system.db.runScalarQuery(SQL, db=database)
    return stepTypeId

def fetchChartIdFromChartPath(chartPath, database):
    SQL = "select chartId from SfcChart where ChartPath = '%s'" % (chartPath)
    chartId = system.db.runScalarQuery(SQL, db=database)
    return chartId
    