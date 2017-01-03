'''
Created on Nov 30, 2016

@author: phassler
'''

import system, string

# Recipe Data Scopes
LOCAL_SCOPE = "local"
SUPERIOR_SCOPE = "superior"
PHASE_SCOPE = "phase"
OPERATION_SCOPE = "operation"
GLOBAL_SCOPE = "global"

# Recipe data step types (I'm not sure where these are used)
PHASE_STEP = "Phase"
OPERATION_STEP = "Operation"
UNIT_PROCEDURE_STEP = "Global"

# Recipe data types
SIMPLE_VALUE = "Simple Value"

# Constants used to navigate and interrogate the chart scope property dictionary
ENCLOSING_STEP_SCOPE_KEY = "enclosingStep"
PARENT = "parent"
S88_LEVEL = "s88Level"
STEP_UUID = 'id'
STEP_NAME = 'name'

logger=system.util.getLogger("com.ils.sfc.recipeData.core")

# Return the UUID of the step  
def getTargetStep(chartProperties, stepProperties, scope):
    logger.tracef("Getting target step for scope %s...", scope)
    
    if scope == LOCAL_SCOPE:
        stepUUID = getStepUUID(stepProperties)
        stepName = getStepName(stepProperties)
        return stepUUID, stepName
    
    elif scope == SUPERIOR_SCOPE:
        stepUUID, stepName = getSuperiorStep(chartProperties)
        return stepUUID, stepName
    
    elif scope == PHASE_SCOPE:
        stepUUID, stepName = walkUpHieracrchy(chartProperties, PHASE_STEP)   
        return stepUUID, stepName
    
    elif scope == OPERATION_SCOPE:
        stepUUID, stepName = walkUpHieracrchy(chartProperties, OPERATION_STEP)     
        return stepUUID, stepName
    
    elif scope == GLOBAL_SCOPE:
        stepUUID, stepName = walkUpHieracrchy(chartProperties, UNIT_PROCEDURE_STEP)     
        return stepUUID, stepName
        
    else:
        logger.errorf("Undefined scope: %s", scope)
        
    return -1 


def walkUpHieracrchy(chartProperties, stepType):
    logger.trace("Walking up the hierarchy looking for %s" % (stepType))
    thisStepType = ""
    RECURSION_LIMIT = 100
    i = 1
    while thisStepType == None or string.upper(thisStepType) <> string.upper(stepType):
        i = i + 1
        if chartProperties.get(ENCLOSING_STEP_SCOPE_KEY, None) != None:
            enclosingStepScope = chartProperties.get(ENCLOSING_STEP_SCOPE_KEY, None) 
            logger.trace("  The enclosing step scope is: %s" % (str(enclosingStepScope)))
            superiorUUID = enclosingStepScope.get(STEP_UUID, None)
            superiorName = enclosingStepScope.get(STEP_NAME, None)
            thisStepType = enclosingStepScope.get(S88_LEVEL)
            
            chartProperties = chartProperties.get(PARENT)
            logger.trace("  The superior step: %s - %s - %s" % (superiorUUID, superiorName, thisStepType))
        else:
            print "Throw an error here - we are at the top"
            return None, None
        
        if i > RECURSION_LIMIT:
            logger.error("***** HIT A RECURSION PROBLEM ****")
            return None, None
        
    return superiorUUID, superiorName
       

def getSuperiorStep(chartProperties):
    logger.trace("Getting the superior step...")
    if chartProperties.get(ENCLOSING_STEP_SCOPE_KEY, None) != None:
        enclosingStepScope = chartProperties.get(ENCLOSING_STEP_SCOPE_KEY, None) 
        logger.trace("  The enclosing step scope is: %s" % ( str(enclosingStepScope) ))
        superiorUUID = enclosingStepScope.get(STEP_UUID, None)
        superiorName = enclosingStepScope.get(STEP_NAME, None)
        logger.trace("  The superior step is %s - %s " % (superiorName, superiorUUID))
    else:
        print "Throw an error here - we are at the top"
        superiorUUID = None
    
    return superiorUUID, superiorName
    

# Get the S88 level of the step superior to this chart.  The chart that is encapsulated under an operation is operation scope.
def getEnclosingStepScope(chartScope):
    enclosingScope = "foo"
    
    if chartScope.get(ENCLOSING_STEP_SCOPE_KEY, None) != None:
        print "Found an enclosing step"
        parentChartScope = getSubScope(chartScope, PARENT)
        parentIsRoot = getSubScope(parentChartScope, PARENT) == None
        enclosingStepScope = getSubScope(chartScope, ENCLOSING_STEP_SCOPE_KEY)            
        scopeIdentifier = enclosingStepScope.get(S88_LEVEL)
        if scopeIdentifier <> None:
            enclosingScope = scopeIdentifier
        elif parentIsRoot:
            enclosingScope = "global"
    else:
        # There is no enclosing scope at the very top, scope only starts when we get under a unit procedure
        enclosingScope = None

    return enclosingScope   


def getSubScope(scope, key):
    print "Getting %s out of %s" % (scope, str(key))
    subScope = scope.get(key, None)
    print "The sub scope is: ", subScope
    return subScope
    

'''
def getTargetStepOLD(chartPath, stepUUID, scope, db):
    logger.tracef("Getting target step for %s - %s", chartPath, scope)
    
    if scope == LOCAL_SCOPE:
        return stepUUID

    elif scope == SUPERIOR_SCOPE:
        superiorStep = fetchSuperiorStepOLD(chartPath, db)
        stepUUID = superiorStep["StepUUID"]
        return stepUUID
    
    elif scope == PHASE_SCOPE:
        phaseStep = walkUpHieracrchyOLD(chartPath, PHASE_STEP, db)
        stepUUID = phaseStep["StepUUID"]       
        return stepUUID
    
    elif scope == OPERATION_SCOPE:
        operationStep = walkUpHieracrchyOLD(chartPath, OPERATION_STEP, db)
        stepUUID = operationStep["StepUUID"]       
        return stepUUID
    
    elif scope == GLOBAL_SCOPE:
        unitProcedureStep = walkUpHieracrchyOLD(chartPath, UNIT_PROCEDURE_STEP, db)
        stepUUID = unitProcedureStep["StepUUID"]       
        return stepUUID
        
    else:
        logger.errorf("Undefined scope: %s", scope)
        
    return -1 

def walkUpHieracrchyOLD(chartPath, stepType, db):
    thisStepType = ""
    while thisStepType <> stepType:
        logger.tracef("Fetching step superior to chart: %s", chartPath)
        superiorStep = fetchSuperiorStep(chartPath, db)
        thisStepType = superiorStep["StepType"]
        chartPath = superiorStep["ChartPath"]
    return superiorStep

def fetchSuperiorStepOLD(chartPath, db):
    logger.tracef("Fetching the step superior to %s", chartPath)
    SQL = "select * from SfcHierarchyView where childChartPath = '%s'" % (chartPath)
    pds = system.db.runQuery(SQL, db)
    logger.tracef("...fetched %d records...", len(pds))
    superiorStep=pds[0]
    return superiorStep
'''

def fetchRecipeData(stepUUID, key, attribute, db):
    SQL = "select * from SfcRecipeDataView where stepUUID = '%s' and RecipeDataKey = '%s' " % (stepUUID, key) 
    pds = system.db.runQuery(SQL, db)
    if len(pds) == 0:
        logger.errorf("Error the key was not found")
        return -1
    
    if len(pds) > 1:
        logger.errorf("Error multiple records were found")
        return -1
    
    record = pds[0]
    recipeDataId = record["RecipeDataId"]
    if record["RecipeDataType"] == SIMPLE_VALUE:
        SQL = "select DESCRIPTION, UNITS, ValueType, FLOATVALUE, INTEGERVALUE, STRINGVALUE, BOOLEANVALUE from SfcRecipeDataSimpleValueView where RecipeDataId = %s" % (recipeDataId)
        pds = system.db.runQuery(SQL, db)
        record = pds[0]
        
        if attribute in ["DESCRIPTION","UNITS"]:
            val = record[attribute]
        elif attribute == "VALUE":
            valueType = record['ValueType']
            val = record["%sVALUE" % string.upper(valueType)]
        else:
            logger.errorf("Unsupported attribute: %s for simple value recipe data", attribute)
    else:
        logger.errorf("Unsupported recipe data type: %s", record["RecipeDataType"])
    
    return val

def setRecipeData(stepUUID, key, attribute, val, db):
    logger.tracef("Setting recipe data value for step: stepUUID: %s, key: %s, attribute: %s, value: %s", stepUUID, key, attribute, val)
    SQL = "select * from SfcRecipeDataView where stepUUID = '%s' and RecipeDataKey = '%s' " % (stepUUID, key) 
    pds = system.db.runQuery(SQL, db)
    if len(pds) == 0:
        logger.errorf("Error the key was not found")
        return -1
    
    if len(pds) > 1:
        logger.errorf("Error multiple records were found")
        return -1
    
    record = pds[0]
    recipeDataId = record["RecipeDataId"]
    if record["RecipeDataType"] == SIMPLE_VALUE:
        SQL = "select * from SfcRecipeDataSimpleValueView where RecipeDataId = %s" % (recipeDataId)
        pds = system.db.runQuery(SQL, db)
        record = pds[0]
        valueType = record['ValueType']
        if valueType == "String":
            SQL = "update SfcRecipeDataSimpleValue set %sValue = '%s' where recipeDataId = %s" % (valueType, val, recipeDataId)
        else:
            SQL = "update SfcRecipeDataSimpleValue set %sValue = %s where recipeDataId = %s" % (valueType, val, recipeDataId)
        rows = system.db.runUpdateQuery(SQL, db)
        logger.tracef('Updated %d simple value recipe data records', rows)
    else:
        logger.errorf("Unsupported recipe data type: %s", record["RecipeDataType"])
    


def getChartUUID(chartProperties):
    return chartProperties.get("chartUUID", "-1")

def getStepUUID(stepProperties):
    return stepProperties.get("stepUUID", "-1")

def getStepName(stepProperties):
    return stepProperties.get(STEP_NAME, "")

# This handles a simple "key.attribute" notation, but does not handle folder reference or arrays
def splitKey(keyAndAttribute):
    tokens = keyAndAttribute.split(".")
    key = string.upper(tokens[0])
    attribute = string.upper(tokens[1])
    return key, attribute

def fetchStepTypeIdFromFactoryId(factoryId, database):
    SQL = "select StepTypeId from SfcStepType where FactoryId = '%s'" % (factoryId)
    stepTypeId = system.db.runScalarQuery(SQL, db=database)
    return stepTypeId

def fetchChartIdFromChartPath(chartPath, database):
    SQL = "select chartId from SfcChart where ChartPath = '%s'" % (chartPath)
    chartId = system.db.runScalarQuery(SQL, db=database)
    return chartId
    