'''
Created on Dec 17, 2015

@author: rforbes
'''

from ils.sfc.gateway.util import getStepProperty,getRecipeScope, copyRowToDict, handleUnexpectedGatewayError
from ils.sfc.gateway.api import getDatabaseName, s88Get, getChartLogger
from system.ils.sfc.common.Constants import SQL, KEY, RESULTS_MODE, FETCH_MODE, KEY_MODE, UPDATE_OR_CREATE, STATIC, DYNAMIC
from ils.sfc.gateway.recipe import substituteScopeReferences
import system.db

def activate(scopeContext, stepProperties, state):
    
    try:
        chartScope = scopeContext.getChartScope()
        stepScope = scopeContext.getStepScope()
        logger = getChartLogger(chartScope)
        database = getDatabaseName(chartScope)
        sql = getStepProperty(stepProperties, SQL)
        processedSql = substituteScopeReferences(chartScope, stepScope, sql)
        dbRows = system.db.runQuery(processedSql, database).getUnderlyingDataset() 
        if dbRows.rowCount == 0:
            logger.error('No rows returned for query %s', processedSql)
            return
        simpleQueryProcessRows(scopeContext, stepProperties, dbRows)
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in simpleQuery.py', logger)
    finally:
        return True
    
def simpleQueryProcessRows(scopeContext, stepProperties, dbRows):
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    resultsMode = getStepProperty(stepProperties, RESULTS_MODE) # UPDATE or CREATE
    fetchMode = getStepProperty(stepProperties, FETCH_MODE) # SINGLE or MULTIPLE
    recipeLocation = getRecipeScope(stepProperties) 
    keyMode = getStepProperty(stepProperties, KEY_MODE) # STATIC or DYNAMIC
    key = getStepProperty(stepProperties, KEY) 
    create = (resultsMode == UPDATE_OR_CREATE)
    if keyMode == STATIC: # TODO: fetchMode must be SINGLE
        for rowNum in range(dbRows.rowCount):
            transferSimpleQueryData(chartScope, stepScope, key, recipeLocation, dbRows, rowNum, create)
    elif keyMode == DYNAMIC:
        for rowNum in range(dbRows.rowCount):
            dynamicKey = dbRows.getValueAt(rowNum,key)
            transferSimpleQueryData(chartScope, stepScope, dynamicKey, recipeLocation, dbRows, rowNum, create)

def transferSimpleQueryData(chartScope, stepScope, key, recipeLocation, dbRows, rowNum, create ):
    from system.ils.sfc import s88GetScope, s88ScopeChanged
    from system.util import jsonEncode
    if create:
        recipeScope = s88GetScope(chartScope, stepScope, recipeLocation)
        # create a structure like a deserialized Structure recipe data object
        structData = dict()
        recipeScope[key] = structData
        structData['class'] = 'Structure'
        structData['key'] = key
        valueData = dict()
        copyRowToDict(dbRows, rowNum, valueData, create)
        jsonValue = jsonEncode(valueData)
        # print 'key', key, 'jsonValue', jsonValue
        structData['value'] = jsonValue
        s88ScopeChanged(chartScope, recipeScope)     
    else:
        recipeData = s88Get(chartScope, stepScope, key, recipeLocation)
        copyRowToDict(dbRows, rowNum, recipeData, create)
