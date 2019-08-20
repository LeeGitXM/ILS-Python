'''
Created on Nov 30, 2016

@author: phassler

'''

import system, string
from ils.sfc.recipeData.core import fetchRecipeData, fetchRecipeDataRecord, setRecipeData, splitKey, fetchRecipeDataType, recipeDataExists, s88GetRecipeDataDS, \
    getStepUUID, getStepName, getPriorStep, getSuperiorStep, walkUpHieracrchy, copyRecipeDatum, fetchRecipeDataFromId, setRecipeDataFromId, getRecipeDataId, \
    fetchRecipeDataRecordFromRecipeDataId, getFolderForStep, copyFolderValues, getStepId
from ils.sfc.recipeData.core import getDatabaseName, readTag, getProviderName
from ils.common.units import convert
from ils.sfc.common.constants import TAG, CHART, STEP, LOCAL_SCOPE, PRIOR_SCOPE, SUPERIOR_SCOPE, PHASE_SCOPE, OPERATION_SCOPE, GLOBAL_SCOPE, REFERENCE_SCOPE, \
    PHASE_STEP, OPERATION_STEP, UNIT_PROCEDURE_STEP
from ils.queue.constants import QUEUE_WARNING, QUEUE_ERROR

logger=system.util.getLogger("com.ils.sfc.recipeData.api")

def s88CheckPV(chartProperties, stepProperties, key, toleranceKey, scope):
    ''' Check that the desired setpoint (from recipe), the actual setpoint, and the actual PV are within tolerance.  '''
    ''' Returns   success, var-failure, Tag Read Error, pv-failure, sp-failure  ''' 

    logger.tracef("In %s.s88CheckPV() checking %s...", __name__, key)
 
    provider = getProviderName(chartProperties)
    tagName = s88Get(chartProperties, stepProperties, key + ".tag", scope)
    tagName = "[%s]%s" % (provider, tagName)
    logger.tracef("Checking if %s exists...", tagName)
    tagExists = system.tag.exists(tagName)
    if not(tagExists):
        raise ValueError, "Unable to locate an output variable named <%s>" % (tagName)
        return "var-failure"

    spDesired = s88Get(chartProperties, stepProperties, key + ".outputValue", scope)

    tagPaths = ["%s/sp/value" % (tagName), "%s/value" % (tagName)]
    logger.tracef("Reading current values from: %s", str(tagPaths))
    qvs = system.tag.readAll(tagPaths) 
    if not(qvs[0].quality.isGood() and qvs[1].quality.isGood()):
        return "Tag Read Error"

    sp = qvs[0].value
    pv = qvs[1].value

    tolerance = s88Get(chartProperties, stepProperties, toleranceKey + ".value", scope) 

    ''' We have found all of the required data '''

    logger.tracef("Desired Setpoint: %f, Current Setpoint: %f, PV: %f, Tolerance: %f", spDesired, sp, pv, tolerance)

    if (abs(spDesired - sp) < 0.1):
        if abs(spDesired - pv) < abs(tolerance):
            status =  "success"
        else:
            status = "pv-failure"

    else:
        ''' The actual SP of does not match the desired SP '''
        status = "sp-failure"
    
    return status


def s88DataExists(chartProperties, stepProperties, keyAndAttribute, scope):
    scope = scope.lower()
    logger.tracef("s88DataExists(): %s - %s", keyAndAttribute, scope)
    db = getDatabaseName(chartProperties)
    if scope == REFERENCE_SCOPE:
        scope, keyAndAttribute = getRecipeByReference(chartProperties, keyAndAttribute)
    stepId, stepName, keyAndAttribute = s88GetStep(chartProperties, stepProperties, scope, keyAndAttribute, db)
    logger.tracef("...the target step is: %s - %d", stepName, stepId)
    folder,key,attribute = splitKey(keyAndAttribute)
    exists = recipeDataExists(stepId, folder, key, attribute, db)
    return exists

def s88GetType(chartProperties, stepProperties, keyAndAttribute, scope):
    scope = scope.lower()
    logger.tracef("s88GetType(): %s - %s", keyAndAttribute, scope)
    db = getDatabaseName(chartProperties)
    if scope == REFERENCE_SCOPE:
        scope, keyAndAttribute = getRecipeByReference(chartProperties, keyAndAttribute)
    stepId, stepName, keyAndAttribute = s88GetStep(chartProperties, stepProperties, scope, keyAndAttribute, db)
    logger.tracef("...the target step is: %s - %d", stepName, stepId)
    folder,key,attribute = splitKey(keyAndAttribute)
    recipeDataType = fetchRecipeDataType(stepId, folder, key, attribute, db)
    return recipeDataType

def s88GetUnits(chartProperties, stepProperties, keyAndAttribute, scope):
    scope = scope.lower()
    logger.tracef("s88Get(): %s - %s", keyAndAttribute, scope)
    db = getDatabaseName(chartProperties)
    if scope == REFERENCE_SCOPE:
        scope, keyAndAttribute = getRecipeByReference(chartProperties, keyAndAttribute)
    stepId, stepName, keyAndAttribute = s88GetStep(chartProperties, stepProperties, scope, keyAndAttribute, db)
    logger.tracef("...the target step is: %s - %d", stepName, stepId)
    folder,key,attribute = splitKey(keyAndAttribute)
    val, units = fetchRecipeData(stepId, folder, key, attribute, db)
    logger.tracef("...fetched %s", str(val))
    return units

# Return a value only for a specific key, otherwise raise an exception.
def s88Get(chartProperties, stepProperties, keyAndAttribute, scope):
    scope = scope.lower()
    logger.tracef("s88Get(): %s - %s", keyAndAttribute, scope)
    db = getDatabaseName(chartProperties)
    if scope == REFERENCE_SCOPE:
        scope, keyAndAttribute = getRecipeByReference(chartProperties, keyAndAttribute)
    stepId, stepName, keyAndAttribute = s88GetStep(chartProperties, stepProperties, scope, keyAndAttribute, db)
    logger.tracef("...the target step is: %s - %d", stepName, stepId)
    folder, key, attribute = splitKey(keyAndAttribute)
    val, units = fetchRecipeData(stepId, folder, key, attribute, db)
    logger.tracef("...fetched %s", str(val))
    return val

def s88GetWithUnits(chartProperties, stepProperties, keyAndAttribute, scope, returnUnits):
    scope = scope.lower()
    logger.tracef("s88Get(): %s - %s", keyAndAttribute, scope)
    db = getDatabaseName(chartProperties)
    if scope == REFERENCE_SCOPE:
        scope, keyAndAttribute = getRecipeByReference(chartProperties, keyAndAttribute)
    stepId, stepName, keyAndAttribute = s88GetStep(chartProperties, stepProperties, scope, keyAndAttribute, db)
    logger.tracef("...the target step is: %s - %d", stepName, stepId)
    folder,key,attribute = splitKey(keyAndAttribute)
    val, fetchedUnits = fetchRecipeData(stepId, folder, key, attribute, db)
    logger.tracef("...fetched %s - %s", str(val), str(fetchedUnits))
    convertedValue = convert(fetchedUnits, string.upper(returnUnits), val, db)
    logger.tracef("...converted to %s", str(convertedValue))
    return convertedValue

# Return a value only for a specific key, otherwise raise an exception.
def s88GetFromStep(stepId, keyAndAttribute, db):
    logger.tracef("s88GetFromStep(): %s", keyAndAttribute)
    folder,key,attribute = splitKey(keyAndAttribute)
    val, units = fetchRecipeData(stepId, folder, key, attribute, db)
    logger.tracef("...fetched %s", str(val))
    return val

# This can be called from anywhere in Ignition.  It assumes that the chart path and stepname is stable
def s88GetFromName(chartPath, stepName, keyAndAttribute, db):
    logger.tracef("s88GetFromName(): geting %s from %s step %s", keyAndAttribute, chartPath, stepName)
    folder,key,attribute = splitKey(keyAndAttribute)
    stepId = s88GetStepFromName(chartPath, stepName, db)
    logger.tracef("...looking at step %s - %d", str(stepId), stepId)
    val, units = fetchRecipeData(stepId, folder, key, attribute, db)
    logger.tracef("...fetched %s", str(val))
    return val

# Return the stepId of the step, the stepName, the key and attribute.
def s88GetStep(chartProperties, stepProperties, scope, keyAndAttribute, db):
    scope = scope.lower()
    logger.tracef("Getting target step for scope: %s, key: %s...", scope, keyAndAttribute)
    
    ''' If the scope is reference, then analyze the keyAndAttribute, which should be a chart skope variable '''
    if scope == REFERENCE_SCOPE:
        scope, keyAndAttribute = getRecipeByReference(chartProperties, keyAndAttribute)
        logger.tracef("...the recipe data reference is: %s - %s", scope, keyAndAttribute)
    
    if scope == LOCAL_SCOPE:
        chartPath = chartProperties.get("chartPath", None)
        stepName = getStepName(stepProperties)
        logger.tracef("The local chart and step are: %s - %s", chartPath, stepName)
        stepId = getStepId(chartPath, stepName, db)
        return stepId, stepName, keyAndAttribute
    
    elif scope == PRIOR_SCOPE:
        chartPath, stepName = getPriorStep(chartProperties, stepProperties)
        stepId = getStepId(chartPath, stepName, db)
        return stepId, stepName, keyAndAttribute
    
    elif scope == SUPERIOR_SCOPE:
        chartPath, stepName = getSuperiorStep(chartProperties)
        stepId = getStepId(chartPath, stepName, db)
        return stepId, stepName, keyAndAttribute
    
    elif scope == PHASE_SCOPE:
        chartPath, stepName = walkUpHieracrchy(chartProperties, PHASE_STEP)
        stepId = getStepId(chartPath, stepName, db)
        return stepId, stepName, keyAndAttribute
    
    elif scope == OPERATION_SCOPE:
        chartPath, stepName = walkUpHieracrchy(chartProperties, OPERATION_STEP)
        stepId = getStepId(chartPath, stepName, db)
        return stepId, stepName, keyAndAttribute
    
    elif scope == GLOBAL_SCOPE:
        chartPath, stepName = walkUpHieracrchy(chartProperties, UNIT_PROCEDURE_STEP)
        stepId = getStepId(chartPath, stepName, db)
        return stepId, stepName, keyAndAttribute
        
    else:
        logger.errorf("Undefined scope: <%s>", scope)
        
    return -1, "", ""

def s88GetStepFromName(chartPath, stepName, db):
    SQL = "select StepId from SfcChart C, SfcStep S "\
        " where S.ChartId = C.ChartId and C.ChartPath = '%s' and S.StepName = '%s' " % (chartPath, stepName)
    pds = system.db.runQuery(SQL, database=db)
    if len(pds) == 0:
        raise ValueError, "Unable to find recipe data for %s - %s, chart/step not found" % (chartPath, stepName)
    if len(pds) > 1:
        raise ValueError, "Unable to find recipe data for %s - %s, multiple steps found" % (chartPath, stepName)
    record = pds[0]
    stepId = record["StepId"]
    return stepId

# This can be called from anywhere in Ignition.  It assumes that the chart path and stepname is stable
def s88GetFromNameWithUnits(chartPath, stepName, keyAndAttribute, returnUnits, db):
    folder,key,attribute = splitKey(keyAndAttribute)
    stepId = s88GetStepFromName(chartPath, stepName, db)
    val, units = fetchRecipeData(stepId, folder, key, attribute, db)
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

    SQL = "select stepId from SfcHierarchyView where ChartPath = '%s' and StepName = '%s'" % (chartPath, stepName)
    stepId = system.db.runScalarQuery(SQL, db)
    print "Fetching dataset for step: ", stepId
    ds = s88GetRecipeDataDS(stepId, recipeDataType, db)
    return ds
    
# Return a value only for a specific key, otherwise raise an exception.
def s88GetRecipeDataDataset(chartScope, stepScope, recipeDataType, scope):
    scope = scope.lower()
    logger.tracef("s88GetCsv(): %s", scope)
    db = getDatabaseName(chartScope)
    keyAndAttribute = ""
    stepId, stepName, keyAndAttribute = s88GetStep(chartScope, stepScope, scope, keyAndAttribute, db)    
    ds = s88GetRecipeDataDS(stepId, recipeDataType, db)
    return ds

# Return a value only for a specific key, otherwise raise an exception.
def s88GetRecord(stepId, key, db):
    logger.tracef("s88GetRecord(): %s", key)
    
    tokens = key.split(".")
    if len(tokens) > 1:
        folder = key[:key.rfind(".")]
        key = key[key.rfind(".")+1:]
        folderId = getFolderForStep(stepId, folder, db)
        logger.tracef("<%s>.<%s>", folder, key)
    else:
        folderId = None
    
    record = fetchRecipeDataRecord(stepId, folderId, key, db)
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
    scope = scope.lower()
    logger.tracef("s88Set(): <%s> - <%s> - <%s>",  scope, keyAndAttribute,str(value))
    db = getDatabaseName(chartProperties)
    if scope == REFERENCE_SCOPE:
        scope, keyAndAttribute = getRecipeByReference(chartProperties, keyAndAttribute)
    stepId, stepName, keyAndAttribute = s88GetStep(chartProperties, stepProperties, scope, keyAndAttribute, db)
    logger.tracef("...the target step is: %s - %s", stepName, str(stepId))
    folder,key,attribute = splitKey(keyAndAttribute)
    setRecipeData(stepId, folder, key, attribute, value, db)

def s88SetWithUnits(chartProperties, stepProperties,  keyAndAttribute, value, scope, units):
    scope = scope.lower()
    logger.tracef("s88SetWithUnits(): %s - %s - %s", keyAndAttribute, scope, str(value))
    db = getDatabaseName(chartProperties)
    if scope == REFERENCE_SCOPE:
        scope, keyAndAttribute = getRecipeByReference(chartProperties, keyAndAttribute)
    stepId, stepName, keyAndAttribute = s88GetStep(chartProperties, stepProperties, scope, keyAndAttribute, db)
    logger.tracef("...the target step is: %s - %d", stepName, stepId)
    folder, key,attribute = splitKey(keyAndAttribute)
    setRecipeData(stepId, folder, key, attribute, value, db, units)

def s88SetFromStep(stepId, keyAndAttribute, value, db):
    logger.tracef("s88SetFromStep(): %s - %s", keyAndAttribute, str(value))
    folder,key,attribute = splitKey(keyAndAttribute)
    setRecipeData(stepId, folder, key, attribute, value, db)
    
def s88SetFromStepWithUnits(stepId, keyAndAttribute, value, db, units):
    logger.tracef("s88SetFromStepWithUnits(): %s - %s - %s", keyAndAttribute, str(value), units)
    folder,key,attribute = splitKey(keyAndAttribute)
    setRecipeData(stepId, folder, key, attribute, value, db, units)
    
# This can be called from anywhere in Ignition.  It assumes that the chart path and stepname is stable
def s88SetFromName(chartPath, stepName, keyAndAttribute, value, db):
    logger.tracef("s88SetFromName(): %s - %s, %s: %s", chartPath, stepName, keyAndAttribute, str(value))
    folder,key,attribute = splitKey(keyAndAttribute)
    stepId = s88GetStepFromName(chartPath, stepName, db)
    setRecipeData(stepId, folder, key, attribute, value, db)
    
def s88SetFromNameWithUnits(chartPath, stepName, keyAndAttribute, value, units, db):
    logger.tracef("s88SetFromName(): %s - %s, %s: %s", chartPath, stepName, keyAndAttribute, str(value))
    folder,key,attribute = splitKey(keyAndAttribute)
    stepId = s88GetStepFromName(chartPath, stepName, db)
    setRecipeData(stepId, folder, key, attribute, value, db, units)

    
'''
These APIs provide an optimized set of methods intended for use by long-running steps that update the same recipe data records each time through.
'''
# Return the Recipe Data Id, which is the primary key for recipe data objects  of the step  
def s88GetRecipeDataId(chartProperties, stepProperties, key, scope):
    scope = scope.lower()
    db = getDatabaseName(chartProperties)
    logger.tracef("Getting step for scope <%s>...", scope)
    
    # Added 3/9/19
    if scope == REFERENCE_SCOPE:
        scope, key = getRecipeByReference(chartProperties, key)
    
    ''' I don't care about the attribute, but I need one to use splitKey, so add one and throw it away '''
    folder,key,attribute = splitKey(key + ".value")
    if folder == "":
        folderAndKey = key
    else:
        folderAndKey = folder + "." + key
    
    if scope == LOCAL_SCOPE:
        chartPath = chartProperties.get("chartPath", None)
        stepName = getStepName(stepProperties)
        logger.tracef("The local chart and step are: %s - %s", chartPath, stepName)
        stepId = getStepId(chartPath, stepName, db)
        recipeDataId, recipeDataType, units = getRecipeDataId(stepId, folderAndKey, db)
        return recipeDataId, recipeDataType
    
    elif scope == PRIOR_SCOPE:
        chartPath, stepName = getPriorStep(chartProperties, stepProperties)
        stepId = getStepId(chartPath, stepName, db)
        recipeDataId, recipeDataType, units = getRecipeDataId(stepId, folderAndKey, db)
        return recipeDataId, recipeDataType
    
    elif scope == SUPERIOR_SCOPE:
        stepId, stepName = getSuperiorStep(chartProperties)
        recipeDataId, recipeDataType, units = getRecipeDataId(stepId, folderAndKey, db)
        return recipeDataId, recipeDataType
    
    elif scope == PHASE_SCOPE:
        chartPath, stepName = walkUpHieracrchy(chartProperties, PHASE_STEP)
        stepId = getStepId(chartPath, stepName, db)   
        recipeDataId, recipeDataType, units = getRecipeDataId(stepId, folderAndKey, db)
        return recipeDataId, recipeDataType
    
    elif scope == OPERATION_SCOPE:
        chartPath, stepName = walkUpHieracrchy(chartProperties, OPERATION_STEP)
        stepId = getStepId(chartPath, stepName, db)   
        recipeDataId, recipeDataType, units = getRecipeDataId(stepId, folderAndKey, db)
        return recipeDataId, recipeDataType
    
    elif scope == GLOBAL_SCOPE:
        chartPath, stepName = walkUpHieracrchy(chartProperties, UNIT_PROCEDURE_STEP)
        stepId = getStepId(chartPath, stepName, db)     
        recipeDataId, recipeDataType, units = getRecipeDataId(stepId, folderAndKey, db)
        return recipeDataId, recipeDataType
        
    else:
        logger.errorf("Undefined scope: %s", scope)
        
    return -1, ""

def s88GetRecipeDataIdFromStep(stepId, key, db):
#    ''' I don't care about the attribute, but I need one to use splitKey, so add one and throw it away '''
#    folder,key,attribute = splitKey(key + ".value")
    recipeDataId, recipeDataType, units = getRecipeDataId(stepId, key, db)
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
def substituteScopeReferences(chartProperties, stepProperties, txt):

    # really wish Python had a do-while loop...
    while True:
        ref = findBracketedScopeReference(txt)
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
            txt = txt.replace(ref, str(value))
        else:
            break
    return txt

def getRecipeByReference(chartScope, keyAndAttribute):
    #TODO Figure out how to make this case insensitive - everything else is case insensitive w/ recipe data
    scopeAndKey = chartScope.get(keyAndAttribute, "")
    logger.tracef("Resolving an indirect reference: <%s>", scopeAndKey)
    scope = scopeAndKey[0:scopeAndKey.find(".")]
    key = scopeAndKey[scopeAndKey.find(".")+1:]
    logger.tracef("...the final scope and key are: <%s> and <%s>", scope, key)
    return scope.lower(), key.lower()

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

    
def s88CopyRecipeDatum(sourceUUID, sourceKey, targetUUID, targetKey, db):
    logger.tracef("In %s.s88CopyRecipeDatum() copying recipe datum from %s.%s to %s.%s", __name__, sourceUUID, sourceKey, targetUUID, targetKey)
    copyRecipeDatum(sourceUUID, sourceKey, targetUUID, targetKey, db)
    
'''
Utilities for dealing with folders
'''
def s88CopyFolderValues(fromChartPath, fromStepName, fromFolder, toChartPath, toStepName, toFolder, recursive, category, db):
    logger.tracef("Copying recipe data from %s-%s-%s to %s-%s-%s", fromChartPath, fromStepName, fromFolder, toChartPath, toStepName, toFolder)
     
    fromStepId = s88GetStepFromName(fromChartPath, fromStepName, db)
    logger.tracef("...fromStepId: %s", str(fromStepId))
    
    toStepId = s88GetStepFromName(toChartPath, toStepName, db)
    logger.tracef("...toStepId: %s", str(toStepId))
    
    copyFolderValues(fromChartPath, fromStepName, fromStepId, fromFolder, toChartPath, toStepName, toStepId, toFolder, recursive, category, db)

'''
This is provided to get behind the scenes in an acceptable way.  It is useful when accessing elements of an array recipe data in a library task where 
the key is passed by reference.
'''
 #TODO Delete this   
def s88GetStepUUIDFolderKeyAttribute(chartProperties, stepProperties, keyAndAttribute, scope):
    stepId, folder, key, attribute = s88GetStepIdFolderKeyAttribute(chartProperties, stepProperties, keyAndAttribute, scope)
    return stepId, folder, key, attribute


def s88GetStepIdFolderKeyAttribute(chartProperties, stepProperties, keyAndAttribute, scope):
    scope = scope.lower()
    db = getDatabaseName(chartProperties)
    if scope == REFERENCE_SCOPE:
        scope, keyAndAttribute = getRecipeByReference(chartProperties, keyAndAttribute)
    stepId, stepName, keyAndAttribute = s88GetStep(chartProperties, stepProperties, scope, keyAndAttribute, db)
    folder,key,attribute = splitKey(keyAndAttribute)
    return stepId, folder, key, attribute

def getKeyedIndex(keyName, keyValue, db):
    ''' A convenient way to get the index into the array once you already have the entire array '''
    from ils.sfc.recipeData.core import getKeyedIndex as getKeyedIndexFromCore
    keyIndex = getKeyedIndexFromCore(keyName, keyValue, db)
    return keyIndex 
    