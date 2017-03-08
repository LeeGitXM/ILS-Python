'''
Created on Nov 30, 2016

@author: phassler
'''

import system, string
from ils.common.cast import toBit
from ils.common.util import formatDateTime
from ils.sfc.common.constants import START_TIMER, STOP_TIMER, PAUSE_TIMER, RESUME_TIMER, CLEAR_TIMER, \
    TIMER_CLEARED, TIMER_STOPPED, TIMER_RUNNING, TIMER_PAUSED, \
    LOCAL_SCOPE, PRIOR_SCOPE, SUPERIOR_SCOPE, PHASE_SCOPE, OPERATION_SCOPE, GLOBAL_SCOPE, \
    PHASE_STEP, OPERATION_STEP, UNIT_PROCEDURE_STEP
from com.jidesoft.utils import AccumulativeRunnable

# Recipe data types
ARRAY = "Array"
INPUT = "Input"
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
    priorUUID= stepProperties.get(STEP_UUID, None) 
    logger.tracef("...returning %s and %s", priorUUID, priorName)
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
    if attribute in ["DESCRIPTION","UNITS","LABEL","RECIPEDATATYPE"]:
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
        SQL = "select STARTTIME, STOPTIME, TIMERSTATE, CUMULATIVEMINUTES from SfcRecipeDataTimer where RecipeDataId = %s" % (recipeDataId)
        pds = system.db.runQuery(SQL, db)
        record = pds[0]
        
        if attribute in ["CUMULATIVEMINUTES", "STARTTIME", "STOPTIME", "TIMERSTATE"]:
            val = record[attribute]
        elif attribute in ["RUNTIME", "ELAPSEDMINUTES"]:
            timerState = record["TIMERSTATE"]
            if timerState in ['NULL', None, 'Cleared']:
                val = 0
            elif timerState in [TIMER_STOPPED, TIMER_PAUSED]:
                startTime = record["STARTTIME"]
                stopTime = record['STOPTIME']
                cumulativeMinutes = record['CUMULATIVEMINUTES']
                runTimeMinutes = cumulativeMinutes + system.date.secondsBetween(startTime, stopTime) / 60.0
                val = runTimeMinutes
            elif timerState in [TIMER_RUNNING]:
                startTime = record["STARTTIME"]
                cumulativeMinutes = record['CUMULATIVEMINUTES']
                now = system.date.now()
                runTimeMinutes = cumulativeMinutes + system.date.secondsBetween(startTime, now) / 60.0
                val = runTimeMinutes
            elif timerState in [TIMER_CLEARED]:
                val = 0.0

        else:
            raise ValueError, "Unsupported attribute: %s for a simple value recipe data" % (attribute)
        
        logger.tracef("Fetched the value: %s", str(val))
        
    elif recipeDataType == INPUT:
        SQL = "select TAG, VALUETYPE, ERRORCODE, ERRORTEXT, RECIPEDATATYPE, "\
            "TARGETFLOATVALUE, TARGETINTEGERVALUE, TARGETSTRINGVALUE, TARGETBOOLEANVALUE, "\
            "PVFLOATVALUE, PVINTEGERVALUE, PVSTRINGVALUE, PVBOOLEANVALUE, "\
            "PVMONITORACTIVE, PVMONITORSTATUS "\
            "from SfcRecipeDataInputView where RecipeDataId = %s" % (recipeDataId)
        pds = system.db.runQuery(SQL, db)
        record = pds[0]
        valueType = string.upper(record["VALUETYPE"])
        
        if attribute in ["TAG","VALUETYPE","ERRORCODE","ERRORTEXT","PVMONITORACTIVE","PVMONITORSTATUS"]:
            val = record[attribute]
        elif attribute == "TARGETVALUE":
            theAttribute = "TARGET%sVALUE" % (valueType)
            val = record[theAttribute]
        elif attribute == "PVVALUE":
            theAttribute = "PV%sVALUE" % (valueType)
            val = record[theAttribute]
        else:
            raise ValueError, "Unsupported attribute: %s for an output recipe data" % (attribute)
    
    elif recipeDataType == OUTPUT:
        SQL = "select TAG, VALUETYPE, OUTPUTTYPE, DOWNLOAD, DOWNLOADSTATUS, ERRORCODE, ERRORTEXT, TIMING, RECIPEDATATYPE, "\
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

def fetchRecipeDataRecord(stepUUID, key, db):
    logger.tracef("Fetching %s from %s", key, stepUUID)
        
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
    if recipeDataType == SIMPLE_VALUE:
        SQL = "select DESCRIPTION, LABEL, UNITS, VALUETYPE, RECIPEDATATYPE, FLOATVALUE, INTEGERVALUE, STRINGVALUE, BOOLEANVALUE from SfcRecipeDataSimpleValueView where RecipeDataId = %s" % (recipeDataId)
    
    elif recipeDataType == TIMER:
        SQL = "select DESCRIPTION, LABEL, UNITS, RECIPEDATATYPE, STARTTIME, STOPTIME, TIMERSTATE, CUMULATIVEMINUTES from SfcRecipeDataTimerView where RecipeDataId = %s" % (recipeDataId)
        
    elif recipeDataType == INPUT:
        SQL = "select DESCRIPTION, LABEL, UNITS, TAG, VALUETYPE, ERRORCODE, ERRORTEXT, RECIPEDATATYPE, PVMONITORACTIVE, PVMONITORSTATUS, "\
            "TARGETFLOATVALUE, TARGETINTEGERVALUE, TARGETSTRINGVALUE, TARGETBOOLEANVALUE, "\
            "PVFLOATVALUE, PVINTEGERVALUE, PVSTRINGVALUE, PVBOOLEANVALUE "\
            "from SfcRecipeDataInputView where RecipeDataId = %s" % (recipeDataId)
    
    elif recipeDataType == OUTPUT:
        SQL = "select DESCRIPTION, LABEL, UNITS, TAG, VALUETYPE, OUTPUTTYPE, DOWNLOAD, DOWNLOADSTATUS, ERRORCODE, ERRORTEXT, TIMING, RECIPEDATATYPE, "\
            "MAXTIMING, ACTUALTIMING, ACTUALDATETIME, PVMONITORACTIVE, PVMONITORSTATUS, SETPOINTSTATUS,  WRITECONFIRM, WRITECONFIRMED, "\
            "OUTPUTFLOATVALUE, OUTPUTINTEGERVALUE, OUTPUTSTRINGVALUE, OUTPUTBOOLEANVALUE, "\
            "TARGETFLOATVALUE, TARGETINTEGERVALUE, TARGETSTRINGVALUE, TARGETBOOLEANVALUE, "\
            "PVFLOATVALUE, PVINTEGERVALUE, PVSTRINGVALUE, PVBOOLEANVALUE "\
            "from SfcRecipeDataOutputView where RecipeDataId = %s" % (recipeDataId)
    
    elif recipeDataType == ARRAY:
        # This really doesn't work for an array, have some work to do...
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

        raise ValueError, "Unsupported operation for an array recipe data"
    
    else:
        raise ValueError, "Unsupported recipe data type: %s" % (recipeDataType)
    
    
    pds = system.db.runQuery(SQL, db)
    if len(pds) <> 1:
        raise ValueError, "%d rows were returned when exactly 1 was expected" % (len(pds))

    record = pds[0]
    return record


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
            
    elif recipeDataType == INPUT:
        if attribute in ['TAG', 'ERRORCODE', 'ERRORTEXT', 'PVMONITORSTATUS']:
            SQL = "update SfcRecipeDataInput set %s = '%s' where recipeDataId = %s" % (attribute, str(val), recipeDataId)
        elif attribute in ['PVMONITORACTIVE']:
            bitVal = toBit(val)
            SQL = "update SfcRecipeDataInput set %s = %s where recipeDataId = %s" % (attribute, bitVal, recipeDataId)
        elif attribute in ['PVVALUE','TARGETVALUE']:
            attrName="%sID" % (attribute)
            SQL = "select ValueType, %s from SfcRecipeDataInputView where RecipeDataId = %s" % (attrName, recipeDataId)
            print SQL
            pds = system.db.runQuery(SQL, db)
            if len(pds) <> 1:
                raise ValueError, "Unable to find the value type for Input recipe data"
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
            SQL = "update SfcRecipeDataInput set ValueTypeId = %i where recipeDataId = %s" % (valueTypeId, recipeDataId)
        else:
            txt = "Unsupported attribute <%s> for input recipe data" % (attribute)
            logger.errorf(txt)
            raise ValueError, txt
            
        rows = system.db.runUpdateQuery(SQL, db)
        logger.tracef('...updated %d input recipe data records', rows)

    
    elif recipeDataType == OUTPUT:
        if string.upper(str(val)) == "NULL" and attribute not in ['OUTPUTVALUE','PVVALUE','TARGETVALUE']:
            SQL = "update SfcRecipeDataOutput set %s = NULL where recipeDataId = %s" % (attribute, recipeDataId)
        elif attribute in ['TAG', 'DOWNLOADSTATUS', 'ERRORCODE', 'ERRORTEXT', 'PVMONITORSTATUS', 'ACTUALDATETIME', 'SETPOINTSTATUS']:
            SQL = "update SfcRecipeDataOutput set %s = '%s' where recipeDataId = %s" % (attribute, str(val), recipeDataId)
        elif attribute in ['DOWNLOAD', 'PVMONITORACTIVE', 'WRITECONFIRM', 'WRITECONFIRMED']:
            bitVal = toBit(val)
            SQL = "update SfcRecipeDataOutput set %s = %s where recipeDataId = %s" % (attribute, bitVal, recipeDataId)
        elif attribute in ['TIMING', 'MAXTIMING', 'ACTUALTIMING']:
            SQL = "update SfcRecipeDataOutput set %s = %s where recipeDataId = %s" % (attribute, val, recipeDataId)
        elif attribute in ['OUTPUTVALUE','PVVALUE','TARGETVALUE']:
            attrName="%sID" % (attribute)
            SQL = "select ValueType, %s from SfcRecipeDataOutputView where RecipeDataId = %s" % (attrName, recipeDataId)
            logger.trace(SQL)
            pds = system.db.runQuery(SQL, db)
            if len(pds) <> 1:
                raise ValueError, "Unable to find the value type for Output recipe data"
            record = pds[0]
            valueType = record["ValueType"]
            valueId = record[attrName]
            theAttribute = "%sValue" % (valueType)
    
            if valueType == 'String' and val <> string.upper(str(val)):
                SQL = "update SfcRecipeDataValue set %s = '%s' where valueId = %s" % (theAttribute, val, valueId)
            else:
                SQL = "update SfcRecipeDataValue set %s = %s where valueId = %s" % (theAttribute, val, valueId)
            logger.trace(SQL)
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
        if attribute in ['COMMAND']:
            now = system.date.now()
            now = formatDateTime(now, format='MM/dd/yy HH:mm:ss')
            val=val.upper()
            if val == PAUSE_TIMER.upper():
                logger.trace("Pausing timer...")
                SQL = "update SfcRecipeDataTimer set StopTime = '%s', TimerState = '%s', CumulativeMinutes = 0.0 where RecipeDataId = %d" % (now, TIMER_PAUSED, recipeDataId)
            elif val == START_TIMER.upper():
                logger.trace("Starting timer...")
                SQL = "update SfcRecipeDataTimer set StartTime = '%s', StopTime = NULL, TimerState = '%s', CumulativeMinutes = 0.0 where RecipeDataId = %d" % (now, TIMER_RUNNING, recipeDataId)
            elif val == RESUME_TIMER.upper():
                logger.trace("Resuming timer...")
                SQL = "select * from sfcRecipeDataTimerView where RecipeDataId = %d" % (recipeDataId)
                pds = system.db.runQuery(SQL, db)
                record = pds[0]
                cumulativeMinutes = record["CumulativeMinutes"]
                startTime = record['StartTime']
                stopTime = record['StopTime']
                
                if stopTime == None or startTime == None:
                    cumulativeMinutes = 0.0
                else:
                    cumulativeMinutes = cumulativeMinutes + system.date.secondsBetween(startTime, stopTime) / 60.0
                
                SQL = "update SfcRecipeDataTimer set StartTime = '%s', StopTime = NULL, TimerState = '%s', CumulativeMinutes = %f where RecipeDataId = %d" % (now, TIMER_RUNNING, cumulativeMinutes, recipeDataId)
            elif val == CLEAR_TIMER.upper():
                logger.trace("Clearing timer...")
                SQL = "update SfcRecipeDataTimer set StartTime = NULL, StopTime = NULL, TimerState = '%s', CumulativeMinutes = 0.0 where RecipeDataId = %d" % (TIMER_CLEARED, recipeDataId)
            elif val == STOP_TIMER.upper():
                logger.trace("Stopping timer...")
                SQL = "update SfcRecipeDataTimer set StopTime = '%s', TimerState = '%s', CumulativeMinutes = 0.0 where RecipeDataId = %d" % (now, TIMER_STOPPED, recipeDataId)
            else:
                raise ValueError, "Unsupported timer command <%s> for timer recipe data" % (val)

            logger.trace(SQL)
            rows = system.db.runUpdateQuery(SQL, db)
            logger.tracef('...updated %d timer records', rows)
        
#            SQL = "update SfcRecipeDataTimer set StartTime = '%s' where recipeDataId = %s" % (val, recipeDataId)
#            rows = system.db.runUpdateQuery(SQL, db)
#            logger.tracef('...updated %d timer recipe data records', rows)
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
    