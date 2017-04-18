# Stub for ils.sfc.recipeData.api.py

from ils.sfc.recipeData.core import getTargetStep, getTargetStepFromName, fetchRecipeData, fetchRecipeDataRecord, setRecipeData, splitKey
from ils.sfc.gateway.api import getDatabaseName

import system
logger=system.util.getLogger("com.ils.sfc.recipeData.api")

# Return a value only for a specific key, otherwise raise an exception.
def s88Get(chartScope, stepScope, keyAndAttribute, scope):
    logger.tracef("s88Get(): %s - %s", keyAndAttribute, scope)
    db = getDatabaseName(chartScope)
    stepUUID, stepName = getTargetStep(chartScope, stepScope, scope)
    logger.tracef("...the target step is: %s - %s", stepName, stepUUID)
    key,attribute = splitKey(keyAndAttribute)
    val = fetchRecipeData(stepUUID, key, attribute, db)
    logger.tracef("...fetched %s", str(val))
    return val

# Return a value only for a specific key, otherwise raise an exception.
def s88GetFromStep(stepUUID, keyAndAttribute, db):
    logger.tracef("s88GetFromStep(): %s", keyAndAttribute)
    key,attribute = splitKey(keyAndAttribute)
    val = fetchRecipeData(stepUUID, key, attribute, db)
    logger.tracef("...fetched %s", str(val))
    return val

# This can be called from anywhere in Ignition.  It assumes that the chart path and stepname is stable
def s88GetFromName(chartPath, stepName, keyAndAttribute, db):
    key,attribute = splitKey(keyAndAttribute)
    stepUUID = getTargetStepFromName(chartPath, stepName, db)
    val = fetchRecipeData(stepUUID, key, attribute, db)
    logger.tracef("...fetched %s", str(val))
    return val

def s88GetKeysForNamedBlock(chartPath, stepName, recipeDataType, db):
    logger.tracef("s88GetKeysForNamedBlock(): %s - %s", chartPath, stepName)
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
    keys=[]
    for record in pds:
        keys.append(record["RecipeDataKey"])
    logger.tracef("...fetched %s", str(keys))
    return keys


# Return a value only for a specific key, otherwise raise an exception.
def s88GetRecord(stepUUID, key, db):
    logger.tracef("s88GetRecord(): %s", key)
    record = fetchRecipeDataRecord(stepUUID, key, db)
    logger.tracef("...fetched %s", str(record))
    return record

def s88GetTargetStepUUID(chartScope, stepScope, scope):
    logger.tracef("s88GetTargetStep(): %s", scope)
    stepUUID, stepName = getTargetStep(chartScope, stepScope, scope)
    logger.tracef("...the target step is: %s - %s", stepName, stepUUID)
    return stepUUID

# This is the most popular API which should be used to access recipe data that lives in the call hierarchy of a 
# running chart.
def s88Set(chartScope, stepScope, keyAndAttribute, value, scope):
    logger.tracef("s88Set(): %s - %s - %s", keyAndAttribute, scope, str(value))
    db = getDatabaseName(chartScope)
    stepUUID, stepName = getTargetStep(chartScope, stepScope, scope)
    logger.tracef("...the target step is: %s - %s", stepName, stepUUID)
    key,attribute = splitKey(keyAndAttribute)
    setRecipeData(stepUUID, key, attribute, value, db)
    
def s88SetFromStep(stepUUID, keyAndAttribute, value, db):
    logger.tracef("s88SetFromStep(): %s - %s - %s", keyAndAttribute, str(value))
    key,attribute = splitKey(keyAndAttribute)
    setRecipeData(stepUUID, key, attribute, value, db)
    
# This can be called from anywhere in Ignition.  It assumes that the chart path and stepname is stable
def s88SetFromName(chartPath, stepName, keyAndAttribute, value, db):
    logger.tracef("s88SetFromName(): %s - %s, %s: %s", chartPath, stepName, keyAndAttribute, str(value))
    key,attribute = splitKey(keyAndAttribute)
    stepUUID = getTargetStepFromName(chartPath, stepName, db)
    setRecipeData(stepUUID, key, attribute, value, db)

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
    