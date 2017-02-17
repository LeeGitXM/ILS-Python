'''
Created on Nov 30, 2016

@author: phassler
'''

import system, string
from ils.common.cast import toBit

# Recipe Data Scopes
LOCAL_SCOPE = "local"
PRIOR_SCOPE = "prior"
SUPERIOR_SCOPE = "superior"
PHASE_SCOPE = "phase"
OPERATION_SCOPE = "operation"
GLOBAL_SCOPE = "global"

# Recipe data step types (I'm not sure where these are used)
PHASE_STEP = "Phase"
OPERATION_STEP = "Operation"
UNIT_PROCEDURE_STEP = "Global"

# Recipe data types
ARRAY = "Array"
OUTPUT = "Output"
SIMPLE_VALUE = "Simple Value"
TIMER = "Timer"

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
    
    scope.lower()
    
    if scope == LOCAL_SCOPE:
        stepUUID = getStepUUID(stepProperties)
        stepName = getStepName(stepProperties)
        return stepUUID, stepName
    
    elif scope == PRIOR_SCOPE:
        stepUUID, stepName = getPriorStep(chartProperties, stepProperties)
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

'''
This is only called from a transition.  The SFC framework passes the PRIOR step's properties
in stepProperties.
'''
def getPriorStep(chartProperties, stepProperties):
    logger.trace("Getting the prior step UUID and Name...")
    priorName = stepProperties.get(STEP_NAME, None) 
    priorUUID= stepProperties.get(STEP_NAME, None) 
    return priorUUID, priorName

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

def fetchRecipeData(stepUUID, key, attribute, db):
    logger.tracef("Fetching %s.%s from %s", key, attribute, stepUUID)
    
    # Separate the key from the array index if there is an array index
    attribute, arrayIndex = checkForArrayReference(attribute)
        
    SQL = "select RECIPEDATAID, STEPUUID, RECIPEDATAKEY, RECIPEDATATYPE, LABEL, DESCRIPTION, UNITS "\
        " from SfcRecipeDataView where stepUUID = '%s' and RecipeDataKey = '%s' " % (stepUUID, key) 
    pds = system.db.runQuery(SQL, db)
    if len(pds) == 0:
        logger.errorf("Error the key was not found")
        raise ValueError, "Key <%s> was not found for step %s" % (key, stepUUID)
    
    if len(pds) > 1:
        logger.errorf("Error multiple records were found")
        raise ValueError, "Multiple records were found for key <%s> was not found for step %s" % (key, stepUUID)
    
    record = pds[0]
    recipeDataId = record["RECIPEDATAID"]
    recipeDataType = record["RECIPEDATATYPE"]
    logger.tracef("...the recipe data tyoe is: %s for id: %d", recipeDataType, recipeDataId)
    
    # These attributes are common to all recipe data classes
    if attribute in ["DESCRIPTION","UNITS","LABEL"]:
        print "Fetching a common attribute..."
        val = record[attribute]
    
    elif recipeDataType == SIMPLE_VALUE:
        SQL = "select VALUETYPE, FLOATVALUE, INTEGERVALUE, STRINGVALUE, BOOLEANVALUE from SfcRecipeDataSimpleValueView where RecipeDataId = %s" % (recipeDataId)
        pds = system.db.runQuery(SQL, db)
        record = pds[0]
        
        if attribute in ["VALUETYPE"]:
            val = record[attribute]
        elif attribute == "VALUE":
            valueType = record['VALUETYPE']
            val = record["%sVALUE" % string.upper(valueType)]
            logger.tracef("Fetched the value: %s", str(val))
        else:
            raise ValueError, "Unsupported attribute: %s for a simple value recipe data" % (attribute)
    
    elif recipeDataType == TIMER:
        SQL = "select STARTTIME from SfcRecipeDataTimerView where RecipeDataId = %s" % (recipeDataId)
        pds = system.db.runQuery(SQL, db)
        record = pds[0]
        
        if attribute in ["STARTTIME"]:
            val = record[attribute]
        elif attribute == "RUNTIME":
            startTime = record["STARTTIME"]
            runTimeMinutes = system.date.minutesBetween(startTime, system.date.now())
            val = runTimeMinutes
            logger.tracef("Fetched the value: %s", str(val))
        else:
            raise ValueError, "Unsupported attribute: %s for a simple value recipe data" % (attribute)
    
    elif recipeDataType == OUTPUT:
        SQL = "select TAG, VALUETYPE, OUTPUTTYPE, DOWNLOAD, DOWNLOADSTATUS, ERRORCODE, ERRORTEXT, TIMING, "\
            "MAXTIMING, ACTUALTIMING, ACTUALDATETIME, OUTPUTFLOATVALUE, OUTPUTINTEGERVALUE, OUTPUTSTRINGVALUE, OUTPUTBOOLEANVALUE, "\
            "TARGETFLOATVALUE, TARGETINTEGERVALUE, TARGETSTRINGVALUE, TARGETBOOLEANVALUE, "\
            "PVFLOATVALUE, PVINTEGERVALUE, PVSTRINGVALUE, PVBOOLEANVALUE, "\
            "PVMONITORACTIVE, PVMONITORSTATUS, WRITECONFIRM, WRITECONFIRMED "\
            "from SfcRecipeDataOutputView where RecipeDataId = %s" % (recipeDataId)
        pds = system.db.runQuery(SQL, db)
        record = pds[0]
        valueType = string.upper(record["VALUETYPE"])
        
        if attribute in ["TAG","VALUETYPE","OUTPUTTYPE","DOWNLOAD","DOWNLOADSTATUS","ERRORCODE","ERRORTEXT","TIMING","MAXTIMING",\
                         "ACTUALTIMING","ACTUALDATETIME","PVMONITORACTIVE","PVMONITORSTATUS","WRITECONFIRM","WRITECONFIRMED"]:
            val = record[attribute]
        elif attribute == "OUTPUTVALUE":
            theAttribute = "OUTPUT%sVALUE" % (valueType)
            val = record[theAttribute]
        elif attribute == "TARGETVALUE":
            theAttribute = "TARGET%sVALUE" % (valueType)
            val = record[theAttribute]
        elif attribute == "PVVALUE":
            theAttribute = "PV%sVALUE" % (valueType)
            val = record[theAttribute]
        else:
            raise ValueError, "Unsupported attribute: %s for an output recipe data" % (attribute)
    
    elif recipeDataType == ARRAY:
        if attribute == "VALUE":
            if arrayIndex == None:
                val = []
                SQL = "select VALUETYPE, ARRAYINDEX, FLOATVALUE, INTEGERVALUE, STRINGVALUE, BOOLEANVALUE "\
                    " from SfcRecipeDataArrayView A, SfcRecipeDataArrayElementView E where A.RecipeDataId = E.RecipeDataId "\
                    " and E.RecipeDataId = %d order by ARRAYINDEX" % (recipeDataId)
                pds = system.db.runQuery(SQL, db)
                for record in pds:
                    valueType = record['VALUETYPE']
                    aVal = record["%sVALUE" % string.upper(valueType)]
                    val.append(aVal)
                logger.tracef("Fetched the whole array: %s", str(val))
            else:
                SQL = "select VALUETYPE, FLOATVALUE, INTEGERVALUE, STRINGVALUE, BOOLEANVALUE "\
                    " from SfcRecipeDataArrayView A, SfcRecipeDataArrayElementView E where A.RecipeDataId = E.RecipeDataId "\
                    " and E.RecipeDataId = %d and ArrayIndex = %d" % (recipeDataId, arrayIndex)
                pds = system.db.runQuery(SQL, db)
                record = pds[0]
                valueType = record['VALUETYPE']
                val = record["%sVALUE" % string.upper(valueType)]
                logger.tracef("Fetched the value: %s", str(val))
                
        else:
            raise ValueError, "Unsupported attribute: %s for an array recipe data" % (attribute)
    
    else:
        raise ValueError, "Unsupported recipe data type: %s" % (recipeDataType)
    
    return val

def setRecipeData(stepUUID, key, attribute, val, db):
    logger.tracef("Setting recipe data value for step: stepUUID: %s, key: %s, attribute: %s, value: %s", stepUUID, key, attribute, val)
    
    # Separate the key from the array index if there is an array index
    attribute, arrayIndex = checkForArrayReference(attribute)
    
    SQL = "select * from SfcRecipeDataView where stepUUID = '%s' and RecipeDataKey = '%s' " % (stepUUID, key) 
    pds = system.db.runQuery(SQL, db)
    if len(pds) == 0:
        logger.errorf("Error the key was not found")
        raise ValueError, "Key <%s> was not found for step %s" % (key, stepUUID)
    
    if len(pds) > 1:
        logger.errorf("Error multiple records were found")
        raise ValueError, "Multiple records were found for key <%s> was not found for step %s" % (key, stepUUID)
    
    record = pds[0]
    recipeDataId = record["RecipeDataId"]
    recipeDataType = record["RecipeDataType"]
    logger.tracef("...the recipe data type is: %s for id: %d", recipeDataType, recipeDataId)
    
    if attribute in ['DESCRIPTION', 'UNITS', 'LABEL']:
        SQL = "update SfcRecipeData set %s = '%s' where recipeDataId = %s" % (attribute, val, recipeDataId)
        rows = system.db.runUpdateQuery(SQL, db)
        logger.tracef('...updated %d records in SfcRecipeData', rows)
    
    elif recipeDataType == SIMPLE_VALUE:
        if attribute in ["VALUETYPE"]:
            valueTypeId = fetchValueTypeId(val, db)
            SQL = "update SfcRecipeDataSimpleValue set ValueTypeId=%d where recipeDataId = %s" % (valueTypeId, recipeDataId)
            rows = system.db.runUpdateQuery(SQL, db)
            logger.tracef('...updated %d simple value recipe data records', rows)
        else:
            SQL = "select * from SfcRecipeDataSimpleValueView where RecipeDataId = %s" % (recipeDataId)
            pds = system.db.runQuery(SQL, db)
            record = pds[0]
            valueType = record['ValueType']
            valueId = record['ValueId']
            if valueType == "String":
                SQL = "update SfcRecipeDataValue set %sValue = '%s' where ValueId = %s" % (valueType, val, valueId)
            else:
                SQL = "update SfcRecipeDataValue set %sValue = %s where ValueId = %s" % (valueType, val, valueId)
            rows = system.db.runUpdateQuery(SQL, db)
            logger.tracef('...updated %d simple value recipe data records', rows)
    
    elif recipeDataType == OUTPUT:
        if attribute in ['TAG', 'DOWNLOADSTATUS', 'ERRORCODE', 'ERRORTEXT', 'PVMONITORSTATUS']:
            SQL = "update SfcRecipeDataOutput set %s = '%s' where recipeDataId = %s" % (attribute, val, recipeDataId)
        elif attribute in ['DOWNLOAD', 'PVMONITORACTIVE', 'WRITECONFIRM', 'WRITECONFIRMED']:
            bitVal = toBit(val)
            SQL = "update SfcRecipeDataOutput set %s = %s where recipeDataId = %s" % (attribute, bitVal, recipeDataId)
        elif attribute in ['TIMING', 'MAXTIMING']:
            SQL = "update SfcRecipeDataOutput set %s = %s where recipeDataId = %s" % (attribute, val, recipeDataId)
        elif attribute in ['OUTPUTVALUE','PVVALUE','TARGETVALUE']:
            attrName="%sID" % (attribute)
            SQL = "select ValueType, %s from SfcRecipeDataOutputView where RecipeDataId = %s" % (attrName, recipeDataId)
            print SQL
            pds = system.db.runQuery(SQL, db)
            if len(pds) <> 1:
                raise ValueError, "Unable to find the value type for Output recipe data"
            record = pds[0]
            valueType = record["ValueType"]
            valueId = record[attrName]
            theAttribute = "%sValue" % (valueType)
    
            if valueType == 'String':
                SQL = "update SfcRecipeDataValue set %s = '%s' where valueId = %s" % (theAttribute, val, valueId)
            else:
                SQL = "update SfcRecipeDataValue set %s = %s where valueId = %s" % (theAttribute, val, valueId)
            print SQL
            rows = system.db.runUpdateQuery(SQL, db)
            logger.tracef('...updated %d value records', rows)

        elif attribute in ['VALUETYPE']:
            valueTypeId = fetchValueTypeId(val, db)
            SQL = "update SfcRecipeDataOutput set ValueTypeId = %i where recipeDataId = %s" % (valueTypeId, recipeDataId)
        elif attribute in ['OUTPUTTYPE']:
            outputTypeId = fetchOutputTypeId(val, db)
            SQL = "update SfcRecipeDataOutput set OutputTypeId = %i where recipeDataId = %s" % (outputTypeId, recipeDataId)
        else:
            logger.errorf("Unsupported attribute <%s> for output recipe data", attribute)
            raise ValueError, "Unsupported attribute <%s> for output recipe data" % (attribute)
            
        rows = system.db.runUpdateQuery(SQL, db)
        logger.tracef('...updated %d output recipe data records', rows)
    
    elif recipeDataType == TIMER:
        if attribute in ['STARTTIME']:
            SQL = "update SfcRecipeDataTimer set StartTime = '%s' where recipeDataId = %s" % (val, recipeDataId)
            rows = system.db.runUpdateQuery(SQL, db)
            logger.tracef('...updated %d timer recipe data records', rows)
        else:
            logger.errorf("Unsupported attribute <%s> for timer recipe data", attribute)
            raise ValueError, "Unsupported attribute <%s> for timer recipe data" % (attribute)
        
    
    elif recipeDataType == ARRAY:
        if arrayIndex == None:
            raise ValueError, "Array Recipe data must specify an index - %s - %s" % (key, attribute)
        
        # Get the value type from the SfcRecipeDataArray table.
        SQL = "select * from SfcRecipeDataArrayView where RecipeDataId = %s" % (recipeDataId)
        pds = system.db.runQuery(SQL, db)
        record = pds[0]
        valueType = record['ValueType']
        
        # Now fetch the Value Id of the specific element of the array
        SQL = "select valueId from SfcRecipeDataArrayElement where RecipeDataId = %s and ArrayIndex = %s" % (str(recipeDataId), str(arrayIndex))
        valueId = system.db.runScalarQuery(SQL, db)
        
        if valueType == "String":
            SQL = "update SfcRecipeDataValue set %sValue = '%s' where ValueId = %d" % (valueType, val, valueId)
        else:
            SQL = "update SfcRecipeDataValue set %sValue = %s where ValueId = %d" % (valueType, val, valueId)

        rows = system.db.runUpdateQuery(SQL, db)
        logger.tracef('...updated %d array value recipe data records', rows)
        
    else:
        logger.errorf("Unsupported recipe data type: %s", record["RecipeDataType"])
        raise ValueError, "Unsupported recipe data type: %s" % (recipeDataType)

# Separate the key from the array index if there is an array index
def checkForArrayReference(attribute):
    arrayIndex = None
    if attribute.find("[") > 0:
        logger.tracef("There is an array index...")
        arrayIndex = attribute[attribute.find("[")+1:len(attribute)-1]
        arrayIndex = int(arrayIndex)
        attribute = attribute[:attribute.find("[")]
    return attribute, arrayIndex
        
def fetchOutputTypeId(val, db):
    SQL = "select OutputTypeId from SfcRecipeDataOutputType where OutputType = '%s'" % (val)
    outputTypeId = system.db.runScalarQuery(SQL, db)
    return outputTypeId

def fetchValueTypeId(val, db):
    SQL = "select ValueTypeId from SfcValueType where ValueType = '%s'" % (val)
    valueTypeId = system.db.runScalarQuery(SQL, db)
    return valueTypeId

def fetchRecipeDataTypeId(val, db):
    SQL = "select RecipeDataTypeId from SfcRecipeDataType where RecipeDataType = '%s'" % (val)
    recipeDataTypeId = system.db.runScalarQuery(SQL, db)
    return recipeDataTypeId

def getChartUUID(chartProperties):
    return chartProperties.get("chartUUID", "-1")

def getStepUUID(stepProperties):
    return stepProperties.get("id", "-1")

def getStepName(stepProperties):
    return stepProperties.get(STEP_NAME, "")

# This handles a simple "key.attribute" notation, but does not handle folder reference or arrays
def splitKey(keyAndAttribute):
    tokens = keyAndAttribute.split(".")
    if len(tokens) < 2:
        txt = "Recipe access failed while attempting to split the key and attribute because there were not enough tokens: <%s> " % (keyAndAttribute)
        raise ValueError, txt
    key = string.upper(tokens[0])
    attribute = string.upper(tokens[1])
    return key, attribute

def fetchStepTypeIdFromFactoryId(factoryId, tx):
    SQL = "select StepTypeId from SfcStepType where FactoryId = '%s'" % (factoryId)
    stepTypeId = system.db.runScalarQuery(SQL, tx=tx)
    
    if stepTypeId < 0:
        print "Step %s does not exist, iserting it..." % (factoryId)
        SQL = "Insert into SfcStepType (StepType, FactoryId) values ('%s','%s')" % (factoryId, factoryId)
        stepTypeId = system.db.runUpdateQuery(SQL, tx=tx, getKey=True)
        print "...inserted into SfcSteptype with id: ", stepTypeId

    return stepTypeId

def fetchChartIdFromChartPath(chartPath, tx):
    SQL = "select chartId from SfcChart where ChartPath = '%s'" % (chartPath)
    chartId = system.db.runScalarQuery(SQL, tx=tx)
    return chartId

def fetchStepIdFromUUID(stepUUID, tx):
    SQL = "select stepId from SfcStep where StepUUID = '%s'" % (stepUUID)
    stepId = system.db.runScalarQuery(SQL, tx=tx)
    return stepId
    