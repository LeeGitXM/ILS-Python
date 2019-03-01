'''
Created on Dec 17, 2015

@author: rforbes
'''

import system
from ils.sfc.gateway.api import getDatabaseName, getChartLogger, handleUnexpectedGatewayError, getStepProperty,copyRowToDict
from ils.sfc.common.constants import SQL, KEY, RESULTS_MODE, FETCH_MODE, KEY_MODE, UPDATE, UPDATE_OR_CREATE, STATIC, DYNAMIC, RECIPE_LOCATION, SINGLE
from ils.sfc.recipeData.api import substituteScopeReferences, s88DataExists
from ils.sfc.recipeData.api import s88Get, s88Set, s88DataExists

def activate(scopeContext, stepProperties, state):
    
    try:
        chart = scopeContext.getChartScope()
        step = scopeContext.getStepScope()
        logger = getChartLogger(chart)
        database = getDatabaseName(chart)
        fetchMode = getStepProperty(stepProperties, FETCH_MODE) # SINGLE or MULTIPLE
        resultsMode = getStepProperty(stepProperties, RESULTS_MODE) # UPDATE or CREATE
        recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
        keyMode = getStepProperty(stepProperties, KEY_MODE) # STATIC or DYNAMIC
        key = getStepProperty(stepProperties, KEY) 
    
        sql = getStepProperty(stepProperties, SQL)
        processedSql = substituteScopeReferences(chart, step, sql)
        logger.tracef("SQL: %s", processedSql)
        
        if fetchMode == SINGLE:
            val = system.db.runScalarQuery(processedSql, database)
            
            if keyMode == STATIC:
                recordExists = s88DataExists(chart, step, key, recipeLocation)
                if not(recordExists) and resultsMode == UPDATE:
                    handleUnexpectedGatewayError(chart, step, "Error: key <%s.%s> does not exist" % (recipeLocation, key), logger)
                    return
                if not(recordExists) and resultsMode == UPDATE_OR_CREATE:
                    print "Create it"
                    
                s88Set(chart, step, key, val, recipeLocation)
            else:
                handleUnexpectedGatewayError(chart, step, "Error: Dynamic key is not supported in single fetch mode", logger)
                return
        else:
            
            pds = system.db.runQuery(processedSql, database) 
            if len(pds) == 0:
                logger.error('No rows returned for query %s', processedSql)
                return
            logger.tracef("...returned %d rows", len(pds))
            simpleQueryProcessRows(scopeContext, stepProperties, pds)
    except:
        handleUnexpectedGatewayError(chart, step, 'Unexpected error in simpleQuery.py', logger)
    finally:
        return True
    
def simpleQueryProcessRows(scopeContext, stepProperties, pds):
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    resultsMode = getStepProperty(stepProperties, RESULTS_MODE) # UPDATE or CREATE
    
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
    keyMode = getStepProperty(stepProperties, KEY_MODE) # STATIC or DYNAMIC
    key = getStepProperty(stepProperties, KEY) 
    create = (resultsMode == UPDATE_OR_CREATE)

    if keyMode == STATIC: # TODO: fetchMode must be SINGLE
        for rowNum in range(pds.rowCount):
            transferSimpleQueryData(chartScope, stepScope, key, recipeLocation, pds, rowNum, create)
    elif keyMode == DYNAMIC:
        for rowNum in range(pds.rowCount):
            dynamicKey = pds.getValueAt(rowNum,key)
            transferSimpleQueryData(chartScope, stepScope, dynamicKey, recipeLocation, pds, rowNum, create)

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
