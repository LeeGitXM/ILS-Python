'''
Created on Nov 30, 2016

@author: phassler

'''

import system, string
from ils.sfc.recipeData.core import fetchRecipeData, fetchRecipeDataRecord, setRecipeData, splitKey, fetchRecipeDataType, recipeDataExists, s88GetRecipeDataDS, \
    getStepUUID, getStepName, getPriorStep, getSuperiorStep, walkUpHieracrchy, copyRecipeDatum, fetchRecipeDataFromId, setRecipeDataFromId, getRecipeDataId, \
    fetchRecipeDataRecordFromRecipeDataId
from ils.sfc.gateway.api import getDatabaseName, readTag
from ils.common.units import convert
from ils.sfc.common.constants import TAG, CHART, STEP, LOCAL_SCOPE, PRIOR_SCOPE, SUPERIOR_SCOPE, PHASE_SCOPE, OPERATION_SCOPE, GLOBAL_SCOPE, CHART_RECIPE_SCOPE, \
    PHASE_STEP, OPERATION_STEP, UNIT_PROCEDURE_STEP
from ils.sfc.recipeData.constants import SIMPLE_VALUE

logger=system.util.getLogger("com.ils.sfc.recipeData.api")

def s88DataExists(chartProperties, stepProperties, keyAndAttribute, scope):
    logger.tracef("s88GetType(): %s - %s", keyAndAttribute, scope)
    db = getDatabaseName(chartProperties)
    if scope == CHART_RECIPE_SCOPE:
        scope, keyAndAttribute = getRecipeByReference(chartProperties, keyAndAttribute)
    stepUUID, stepName = s88GetStep(chartProperties, stepProperties, scope)
    logger.tracef("...the target step is: %s - %s", stepName, stepUUID)
    folder,key,attribute = splitKey(keyAndAttribute)
    exists = recipeDataExists(stepUUID, folder, key, attribute, db)
    return exists

def s88GetType(chartProperties, stepProperties, keyAndAttribute, scope):
    logger.tracef("s88GetType(): %s - %s", keyAndAttribute, scope)
    db = getDatabaseName(chartProperties)
    if scope == CHART_RECIPE_SCOPE:
        scope, keyAndAttribute = getRecipeByReference(chartProperties, keyAndAttribute)
    stepUUID, stepName = s88GetStep(chartProperties, stepProperties, scope)
    logger.tracef("...the target step is: %s - %s", stepName, stepUUID)
    folder,key,attribute = splitKey(keyAndAttribute)
    recipeDataType = fetchRecipeDataType(stepUUID, folder, key, attribute, db)
    return recipeDataType

def s88GetUnits(chartProperties, stepProperties, keyAndAttribute, scope):
    logger.tracef("s88Get(): %s - %s", keyAndAttribute, scope)
    db = getDatabaseName(chartProperties)
    if scope == CHART_RECIPE_SCOPE:
        scope, keyAndAttribute = getRecipeByReference(chartProperties, keyAndAttribute)
    stepUUID, stepName = s88GetStep(chartProperties, stepProperties, scope)
    logger.tracef("...the target step is: %s - %s", stepName, stepUUID)
    folder,key,attribute = splitKey(keyAndAttribute)
    val, units = fetchRecipeData(stepUUID, folder, key, attribute, db)
    logger.tracef("...fetched %s", str(val))
    return units

# Return a value only for a specific key, otherwise raise an exception.
def s88Get(chartProperties, stepProperties, keyAndAttribute, scope):
    logger.tracef("s88Get(): %s - %s", keyAndAttribute, scope)
    db = getDatabaseName(chartProperties)
    if scope == CHART_RECIPE_SCOPE:
        scope, keyAndAttribute = getRecipeByReference(chartProperties, keyAndAttribute)
    stepUUID, stepName = s88GetStep(chartProperties, stepProperties, scope)
    logger.tracef("...the target step is: %s - %s", stepName, stepUUID)
    folder, key,attribute = splitKey(keyAndAttribute)
    val, units = fetchRecipeData(stepUUID, folder, key, attribute, db)
    logger.tracef("...fetched %s", str(val))
    return val

def s88GetWithUnits(chartProperties, stepProperties, keyAndAttribute, scope, returnUnits):
    logger.tracef("s88Get(): %s - %s", keyAndAttribute, scope)
    db = getDatabaseName(chartProperties)
    if scope == CHART_RECIPE_SCOPE:
        scope, keyAndAttribute = getRecipeByReference(chartProperties, keyAndAttribute)
    stepUUID, stepName = s88GetStep(chartProperties, stepProperties, scope)
    logger.tracef("...the target step is: %s - %s", stepName, stepUUID)
    folder,key,attribute = splitKey(keyAndAttribute)
    val, fetchedUnits = fetchRecipeData(stepUUID, folder, key, attribute, db)
    logger.tracef("...fetched %s - %s", str(val), str(fetchedUnits))
    convertedValue = convert(fetchedUnits, string.upper(returnUnits), val, db)
    logger.tracef("...converted to %s", str(convertedValue))
    return convertedValue

# Return a value only for a specific key, otherwise raise an exception.
def s88GetFromStep(stepUUID, keyAndAttribute, db):
    logger.tracef("s88GetFromStep(): %s", keyAndAttribute)
    folder,key,attribute = splitKey(keyAndAttribute)
    val, units = fetchRecipeData(stepUUID, folder, key, attribute, db)
    logger.tracef("...fetched %s", str(val))
    return val

# This can be called from anywhere in Ignition.  It assumes that the chart path and stepname is stable
def s88GetFromName(chartPath, stepName, keyAndAttribute, db):
    logger.tracef("s88GetFromName(): geting %s from %s step %s", keyAndAttribute, chartPath, stepName)
    folder,key,attribute = splitKey(keyAndAttribute)
    stepUUID, stepId = s88GetStepFromName(chartPath, stepName, db)
    logger.tracef("...looking at step %s - %s", str(stepId), str(stepUUID))
    val, units = fetchRecipeData(stepUUID, folder, key, attribute, db)
    logger.tracef("...fetched %s", str(val))
    return val

# Return the UUID of the step  
def s88GetStep(chartProperties, stepProperties, scope):
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
        logger.errorf("Undefined scope: <%s>", scope)
        
    return -1, ""

def s88GetStepFromName(chartPath, stepName, db):
    SQL = "select StepUUID, StepId from SfcChart C, SfcStep S "\
        " where S.ChartId = C.ChartId and C.ChartPath = '%s' and S.StepName = '%s' " % (chartPath, stepName)
    pds = system.db.runQuery(SQL, database=db)
    if len(pds) == 0:
        raise ValueError, "Unable to find recipe data for %s - %s, chart/step not found" % (chartPath, stepName)
    if len(pds) > 1:
        raise ValueError, "Unable to find recipe data for %s - %s, multiple steps found" % (chartPath, stepName)
    record = pds[0]
    stepUUID = record["StepUUID"]
    stepId = record["StepId"]
    return stepUUID, stepId

# This can be called from anywhere in Ignition.  It assumes that the chart path and stepname is stable
def s88GetFromNameWithUnits(chartPath, stepName, keyAndAttribute, returnUnits, db):
    folder,key,attribute = splitKey(keyAndAttribute)
    stepUUID, stepId = s88GetStepFromName(chartPath, stepName, db)
    val, units = fetchRecipeData(stepUUID, folder, key, attribute, db)
    logger.tracef("...fetched %s", str(val))
    convertedValue = convert(units, returnUnits, val, db)
    logger.tracef("...converted to %s", str(convertedValue))
    return convertedValue

'''
For some reason I can't get the stupid wild card to work with the recipe data type.
So do an explicit test for the "%" and then run a different SQL command.
So they can't use the wild card and a string to get a partial match.
'''
def s88GetKeysForNamedBlock(chartPath, stepName, recipeDataType, db):
    logger.tracef("s88GetKeysForNamedBlock(): %s - %s", chartPath, stepName)
    if recipeDataType == "%":
        SQL = "select RecipeDataKey "\
            "from SfcRecipeData RD, SfcStep STEP, SfcChart CHART "\
            "where Chart.ChartPath = '%s' "\
            "and Step.StepName = '%s' "\
            "and STEP.ChartId = CHART.ChartId "\
            "and STEP.StepId = RD.StepId" % (chartPath, stepName) 
    else:
        SQL = "select RecipeDataKey "\
            "from SfcRecipeData RD, SfcStep STEP, SfcChart CHART, SfcRecipeDataType RDT "\
            "where Chart.ChartPath = '%s' "\
            "and Step.StepName = '%s' "\
            "and STEP.ChartId = CHART.ChartId "\
            "and RDT.RecipeDataType = '%s' "\
            "and RDT.RecipeDataTypeId = RD.RecipeDataTypeId "\
            "and STEP.StepId = RD.StepId" % (chartPath, stepName, recipeDataType)
    
    pds = system.db.runQuery(SQL, db)
    logger.tracef("...fetched %d rows", len(pds))
    
    keys = []
    for record in pds:
        key = record["RecipeDataKey"]
        keys.append(key)
        
    return keys
    
'''
Get the CSV as a list of text string for all of the recipe data for a step
'''
# Return a value only for a specific key, otherwise raise an exception.
def s88GetRecipeDataDatasetFromName(chartPath, stepName, recipeDataType, db=""):
    logger.tracef("s88GetRecipeDataDatasetFromName(): %s - %s", chartPath, stepName)

    SQL = "select StepUUID from SfcHierarchyView where ChartPath = '%s' and StepName = '%s'" % (chartPath, stepName)
    stepUUID = system.db.runScalarQuery(SQL, db)
    print "Fetching dataset for step: ", stepUUID
    ds = s88GetRecipeDataDS(stepUUID, recipeDataType, db)
    return ds
    
# Return a value only for a specific key, otherwise raise an exception.
def s88GetRecipeDataDataset(chartScope, stepScope, recipeDataType, scope):
    logger.tracef("s88GetCsv(): %s", scope)
    db = getDatabaseName(chartScope)
    stepUUID, stepName = s88GetStep(chartScope, stepScope, scope)    
    ds = s88GetRecipeDataDS(stepUUID, recipeDataType, db)
    return ds

# Return a value only for a specific key, otherwise raise an exception.
def s88GetRecord(stepUUID, key, db):
    logger.tracef("s88GetRecord(): %s", key)
    record = fetchRecipeDataRecord(stepUUID, key, db)
    logger.tracef("...fetched %s", str(record))
    return record

# Return a value only for a specific key, otherwise raise an exception.
def s88GetRecordFromId(recipeDataId, recipeDataType, db):
    logger.tracef("s88GetRecordFromId(): %d - %s", recipeDataId, recipeDataType)
    record = fetchRecipeDataRecordFromRecipeDataId(recipeDataId, recipeDataType, db)
    logger.tracef("...fetched %s", str(record))
    return record

# This is the most popular API which should be used to access recipe data that lives in the call hierarchy of a 
# running chart.
def s88Set(chartProperties, stepProperties, keyAndAttribute, value, scope):
    logger.tracef("s88Set(): <%s> - <%s> - <%s>",  scope, keyAndAttribute,str(value))
    db = getDatabaseName(chartProperties)
    if scope == CHART_RECIPE_SCOPE:
        print "Found an indirect reference..."
        scope, keyAndAttribute = getRecipeByReference(chartProperties, keyAndAttribute)
    stepUUID, stepName = s88GetStep(chartProperties, stepProperties, scope)
    logger.tracef("...the target step is: %s - %s", stepName, stepUUID)
    folder,key,attribute = splitKey(keyAndAttribute)
    setRecipeData(stepUUID, folder, key, attribute, value, db)

def s88SetWithUnits(chartProperties, stepProperties,  keyAndAttribute, value, scope, units):
    logger.tracef("s88SetWithUnits(): %s - %s - %s", keyAndAttribute, scope, str(value))
    db = getDatabaseName(chartProperties)
    stepUUID, stepName = s88GetStep(chartProperties, stepProperties, scope)
    logger.tracef("...the target step is: %s - %s", stepName, stepUUID)
    folder, key,attribute = splitKey(keyAndAttribute)
    setRecipeData(stepUUID, folder, key, attribute, value, db, units)
    
def s88SetFromStep(stepUUID, keyAndAttribute, value, db):
    logger.tracef("s88SetFromStep(): %s - %s", keyAndAttribute, str(value))
    folder,key,attribute = splitKey(keyAndAttribute)
    setRecipeData(stepUUID, folder, key, attribute, value, db)
    
def s88SetFromStepWithUnits(stepUUID, keyAndAttribute, value, db, units):
    logger.tracef("s88SetFromStepWithUnits(): %s - %s - %s", keyAndAttribute, str(value), units)
    folder,key,attribute = splitKey(keyAndAttribute)
    setRecipeData(stepUUID, folder, key, attribute, value, db, units)
    
# This can be called from anywhere in Ignition.  It assumes that the chart path and stepname is stable
def s88SetFromName(chartPath, stepName, keyAndAttribute, value, db):
    logger.tracef("s88SetFromName(): %s - %s, %s: %s", chartPath, stepName, keyAndAttribute, str(value))
    folder,key,attribute = splitKey(keyAndAttribute)
    stepUUID, stepId = s88GetStepFromName(chartPath, stepName, db)
    setRecipeData(stepUUID, folder, key, attribute, value, db)
    
def s88SetFromNameWithUnits(chartPath, stepName, keyAndAttribute, value, units, db):
    logger.tracef("s88SetFromName(): %s - %s, %s: %s", chartPath, stepName, keyAndAttribute, str(value))
    folder,key,attribute = splitKey(keyAndAttribute)
    stepUUID, stepId = s88GetStepFromName(chartPath, stepName, db)
    setRecipeData(stepUUID, folder, key, attribute, value, db, units)
    
def s88CopyRecipeDatum(sourceUUID, sourceKey, targetUUID, targetKey, db):
    copyRecipeDatum(sourceUUID, sourceKey, targetUUID, targetKey, db)
    
'''
These APIs provide an optimized set of methods intended for use by long-running steps that update the same recipe data records each time through.
'''
# Return the Recipe Data Id, which is the primary key for recipe data objects  of the step  
def s88GetRecipeDataId(chartProperties, stepProperties, key, scope):
    db = getDatabaseName(chartProperties)
    logger.tracef("Getting step for scope %s...", scope)
    
    ''' I don't care about the attribute, but I need one to use splitKey, so add one and throw it away '''
    folder,key,attribute = splitKey(key + ".value")
    scope.lower()
    
    if scope == LOCAL_SCOPE:
        stepUUID = getStepUUID(stepProperties)
        recipeDataId, recipeDataType, units = getRecipeDataId(stepUUID, folder, key, db)
        return recipeDataId, recipeDataType
    
    elif scope == PRIOR_SCOPE:
        stepUUID, stepName = getPriorStep(chartProperties, stepProperties)
        ''' Not sure why this isn't completed '''
        return stepUUID, stepName
    
    elif scope == SUPERIOR_SCOPE:
        stepUUID, stepName = getSuperiorStep(chartProperties)
        recipeDataId, recipeDataType, units = getRecipeDataId(stepUUID, folder, key, db)
        return recipeDataId, recipeDataType
    
    elif scope == PHASE_SCOPE:
        stepUUID, stepName = walkUpHieracrchy(chartProperties, PHASE_STEP)   
        recipeDataId, recipeDataType, units = getRecipeDataId(stepUUID, folder, key, db)
        return recipeDataId, recipeDataType
    
    elif scope == OPERATION_SCOPE:
        stepUUID, stepName = walkUpHieracrchy(chartProperties, OPERATION_STEP)     
        recipeDataId, recipeDataType, units = getRecipeDataId(stepUUID, folder, key, db)
        return recipeDataId, recipeDataType
    
    elif scope == GLOBAL_SCOPE:
        stepUUID, stepName = walkUpHieracrchy(chartProperties, UNIT_PROCEDURE_STEP)     
        recipeDataId, recipeDataType, units = getRecipeDataId(stepUUID, folder, key, db)
        return recipeDataId, recipeDataType
        
    else:
        logger.errorf("Undefined scope: %s", scope)
        
    return -1, ""

def s88GetRecipeDataIdFromStep(stepUUID, key, db):
    ''' I don't care about the attribute, but I need one to use splitKey, so add one and throw it away '''
    folder,key,attribute = splitKey(key + ".value")
    recipeDataId, recipeDataType, units = getRecipeDataId(stepUUID, folder, key, db)
    return recipeDataId, recipeDataType

# Return a value for a specific key using the recipe data id.  This is intended for long-running steps that update the same recipe data object each iteration.
def s88GetFromId(recipeDataId, recipeDataType, attribute, db, units="", arrayIndex=0, rowIndex=0, columnIndex=0):
    logger.tracef("s88GetRecipeDataValue(): %d - %s - %s", recipeDataId, recipeDataType, attribute)
    val = fetchRecipeDataFromId(recipeDataId, recipeDataType, attribute, units, arrayIndex, rowIndex, columnIndex, db)
    logger.tracef("...fetched %s", str(val))
    return val

# Return a value for a specific key using the recipe data id.  This is intended for long-running steps that update the same recipe data object each iteration.
def s88SetFromId(recipeDataId, recipeDataType, attribute, value, db, units="", targetUnits="", arrayIndex=0, rowIndex=0, columnIndex=0):
    logger.tracef("s88GetRecipeDataValue(): %d - %s - %s", recipeDataId, recipeDataType, attribute)
    setRecipeDataFromId(recipeDataId, recipeDataType, attribute, value, units, targetUnits, arrayIndex, rowIndex, columnIndex, db)

'''
These next few APIs are used to facilitate a number of steps sprinkled throughout the Vistalon recipe that
store and the fetch various recipe configurations.  The idea is that before shutting down we save the configuration
so that we can start it up the same way.
'''
def stashRecipeDataValue(rxConfig, recipeDataKey, recipeDataAttribute, recipeDataValue, database):
    print "TODO Stashing has not been implemented!"

def fetchStashedRecipeData(rxConfig, database):
    logger.tracef("Fetching stashed recipe data for %s...", rxConfig)
    SQL = "select RecipeDataKey, RecipeDataAttribute, RecipeDataValue "\
        "from SfcRecipeDataStash "\
        "where RxConfiguration = '%s' "\
        "order by RecipeDataKey" % (rxConfig)
    pds = system.db.runQuery(SQL, database)
    return pds

def fetchStashedRecipeDataValue(rxConfig, recipeDataKey, recipeDataAttribute, database):
    logger.tracef("Fetching %s.%s for %s...", recipeDataKey, recipeDataAttribute, rxConfig)
    SQL = "select RecipeDataValue "\
        "from SfcRecipeDataStash "\
        "where RxConfiguration = '%s' and RecipeDataKey = '%s' and RecipeDataAttribute = '%s' "\
        "order by RecipeDataKey" % (rxConfig, recipeDataKey, recipeDataAttribute)
    recipeDataValue = system.db.runScalarQuery(SQL, database)
    return recipeDataValue

def clearStashedRecipeData(rxConfig, database):
    logger.tracef("Clearing %s", rxConfig)
    SQL = "delete from SfcRecipeDataStash where RxConfigurastion = '%s'" % (rxConfig)
    rows = system.db.runUpdateQuery(SQL, database)
    logger.tracef("   ...deleted %d rows", rows)
    
def parseBracketedScopeReference(bracketedRef):
    '''
    Break a bracked reference into location and key--e.g. {local:selected-emp.val} gets
    broken into 'local' and 'selected-emp.val'
    '''   
    firstDotIndex = bracketedRef.index('.')
    location = bracketedRef[1 : firstDotIndex].strip()
    key = bracketedRef[firstDotIndex + 1 : len(bracketedRef) - 1].strip()
    return location, key

def findBracketedScopeReference(string):
    '''
     Find the first bracketed reference in the string, e.g. {local:selected-emp.val}
     or return None if not found
     '''
    lbIndex = string.find('{')
    rbIndex = string.find('}')
    firstDotIndex = string.find('.', lbIndex)
    if lbIndex != -1 and rbIndex != -1 and firstDotIndex != -1 and rbIndex > firstDotIndex:
        return string[lbIndex : rbIndex+1]
    else:
        return None

'''
Substitute for scope variable references in text strings, e.g. '{local:selected-emp.value}'
This makes a text string dynamic by updating recipe data references.
'''
def substituteScopeReferences(chartProperties, stepProperties, sql):

    # really wish Python had a do-while loop...
    while True:
        ref = findBracketedScopeReference(sql)
        if ref != None:
            location, key = parseBracketedScopeReference(ref)
            location = location.lower()
            if location == TAG:
                value = readTag(chartProperties, key)
            elif location == CHART:
                value = chartProperties.get(key, "<not found>")
            elif location == STEP:
                value = stepProperties.get(key, "<not found>")
            else:
                try:
                    value = s88Get(chartProperties, stepProperties, key, location)
                except:
                    value = "<Error: %s.%s not found>" % (location, key)
            sql = sql.replace(ref, str(value))
        else:
            break
    return sql

def getRecipeByReference(chartScope, keyAndAttribute):
    scopeAndKey = chartScope.get(keyAndAttribute, "")
    logger.tracef("Resolving an indirect reference: <%s>", scopeAndKey)
    scope = scopeAndKey[0:scopeAndKey.find(".")]
    key = scopeAndKey[scopeAndKey.find(".")+1:]
    logger.tracef("...the final scope and key are: <%s> and <%s>", scope, key)
    return scope, key

'''
Walk up the chart Hierarchy finding the topmost chart, the root, for this chart.
This uses the hierarchy from the database, not the chart scope structure.
This is handy when starting a chart from the designer.
'''
def s88GetRootForChart(chartPath, db):
    from ils.sfc.recipeData.hierarchyWithBrowser import fetchHierarchy
    
    SQL = "select chartId from sfcChart where chartPath = '%s'" % (chartPath)
    chartId = system.db.runScalarQuery(SQL, db)
    print "The chart Id is: ", chartId
    if chartId == None:
        logger.errorf("Error: Unable to find a chart id for chart path <%s>", chartPath)
        return "Not Found"
    
    hierarchyPDS = fetchHierarchy(False, db)
    
    foundParent = True
    while foundParent:
        foundParent = False
        print "Looking for the parent for %s ..." % (chartPath)
        for record in hierarchyPDS:
            if chartId == record["ChildChartId"]:
                chartId = record["ChartId"]
                chartPath = record["ChartPath"]
                foundParent = True
                break

    print "Found root: ", chartPath
    return chartPath, chartId

'''
Utilities for dealing with folders
'''
def s88CopyFolderValues(chart, step, fromFolderKey, fromScope, toFolderKey, toScope, recursive, db):
    logger.errorf("*******************************************************")
    logger.errorf("* %s.s88CopyFolderValues NEEDS TO BE IMPLEMENTED", __name__)
    logger.errorf("*******************************************************")
    
    