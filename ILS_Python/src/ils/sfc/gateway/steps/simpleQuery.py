'''
Created on Dec 17, 2015

@author: rforbes
'''

import system
from ils.sfc.gateway.api import getDatabaseName, getChartLogger, handleUnexpectedGatewayError, handleExpectedGatewayError, getStepProperty,copyRowToDict,\
    getChartPath
from ils.sfc.common.constants import SQL, KEY, RESULTS_MODE, FETCH_MODE, KEY_MODE, UPDATE, UPDATE_OR_CREATE, STATIC, DYNAMIC, RECIPE_LOCATION, SINGLE, STEP_NAME
from ils.sfc.recipeData.api import substituteScopeReferences, s88DataExists
from ils.sfc.recipeData.api import s88Get, s88Set, s88DataExists

def activate(scopeContext, stepProperties, state):
    
    try: 
        print "==============================================================="
        print "ScopeContext: ", str(scopeContext)
        chartScope = scopeContext.getChartScope()
        print "ChartScope: ", str(chartScope)
        stepScope = scopeContext.getStepScope()
        print "StepScope: ", stepScope
        chartPath = getChartPath(chartScope)
        stepName = getStepProperty(stepProperties, STEP_NAME)
        log = getChartLogger(chartScope)
        log.tracef("In %s.activate(), with chart: %s, step: %s", __name__, chartPath, stepName)
        database = getDatabaseName(chartScope)
        fetchMode = getStepProperty(stepProperties, FETCH_MODE) # SINGLE or MULTIPLE
        resultsMode = getStepProperty(stepProperties, RESULTS_MODE) # UPDATE or CREATE
        recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
        keyMode = getStepProperty(stepProperties, KEY_MODE) # STATIC or DYNAMIC
        
        ''' Validate the configuration '''
        if not(resultsMode == UPDATE or resultsMode == UPDATE_OR_CREATE):
            txt = "ERROR: Illegal RESULTS mode: <%s>, legal values are %s or %s" % (resultsMode, UPDATE, UPDATE_OR_CREATE)
            log.errorf(txt)
            handleExpectedGatewayError(chartScope, stepName, txt, log)
            return
                
        key = getStepProperty(stepProperties, KEY) 
    
        sql = getStepProperty(stepProperties, SQL)
        processedSql = substituteScopeReferences(chartScope, stepScope, sql)
        log.tracef("SQL: %s", processedSql)
        log.tracef("Fetch mode: %s, Key mode: %s, Results mode: %s", fetchMode, keyMode, resultsMode)
        
        if fetchMode == SINGLE:

            if keyMode == STATIC:
                val = system.db.runScalarQuery(processedSql, database)
                log.tracef("   Fetched value: %s", str(val))
            
                recordExists = s88DataExists(chartScope, stepScope, key, recipeLocation)
                if not(recordExists) and resultsMode == UPDATE:
                    log.errorf("ERROR: The recipe data with key <%s> does not exist at scope: %s for a static simple query", key, recipeLocation)
                    handleExpectedGatewayError(chartScope, stepName, "Error executing a Simple Query step, Fetch mode: <%s>, Key mode: <%s>. Key <%s.%s> does not exist" % (fetchMode, keyMode, recipeLocation, key), log)
                    return
                if not(recordExists) and resultsMode == UPDATE_OR_CREATE:
                    print "Create it"
                    
                s88Set(chartScope, stepScope, key, val, recipeLocation)
            
            elif keyMode == DYNAMIC:
                pds = system.db.runQuery(processedSql, database)
                if len(pds) == 0:
                    log.errorf("ERROR: The static record with key <%s> does not exist at scope: %s", key, recipeLocation)
                    handleExpectedGatewayError(chartScope, stepName, "Error executing a Simple Query step, Fetch mode: <%s>, Key mode: <%s>. Key <%s.%s> does not exist" % (fetchMode, keyMode, recipeLocation, key), log)
                    return
                record = pds[0]
                key = record[0]
                val = record[1]
                log.tracef("   Fetched key: %s, value: %s", str(key), str(val))
                
                if key.find(".value") < 0:
                    key = "%s.value" % (key)
            
                if resultsMode == UPDATE:
                    recordExists = s88DataExists(chartScope, stepScope, key, recipeLocation)
                    if not(recordExists) and resultsMode == UPDATE:
                        log.errorf("ERROR: The recipe data with key <%s> does not exist at scope: %s for a dynamic simple query in update mode", key, recipeLocation)
                        handleExpectedGatewayError(chartScope, stepName, "Error executing a Simple Query step, Fetch mode: <%s>, Key mode: <%s>, ResultsMode: <%s>. Key <%s.%s> does not exist" % (fetchMode, keyMode, resultsMode, recipeLocation, key), log)
                        return
                    s88Set(chartScope, stepScope, key, val, recipeLocation)
                elif resultsMode == UPDATE_OR_CREATE:
                    print "CRAP"

            else:
                handleExpectedGatewayError(chartScope, stepName, "Error executing a Simple Query step, Fetch mode: <%s>, Key mode: <%s>. Illegal key mode" % (fetchMode, keyMode), log)
                return
        else:
            
            pds = system.db.runQuery(processedSql, database) 
            if len(pds) == 0:
                log.error('No rows returned for query %s', processedSql)
                return
            log.tracef("...returned %d rows", len(pds))
            simpleQueryProcessRows(scopeContext, stepProperties, pds)
    except:
        print "**** CAUGHT AN UNEXPECTED ERROR ****"
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in simpleQuery.py', log)
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
