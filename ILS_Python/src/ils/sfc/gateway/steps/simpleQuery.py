'''
Created on Dec 17, 2015

@author: rforbes
'''

import system, string
from ils.sfc.gateway.api import getDatabaseName, getChartLogger, handleUnexpectedGatewayError, handleExpectedGatewayError, getStepProperty,copyRowToDict,\
    getChartPath
from ils.sfc.common.constants import SQL, KEY, RESULTS_MODE, FETCH_MODE, KEY_MODE, UPDATE, UPDATE_OR_CREATE, STATIC, DYNAMIC, RECIPE_LOCATION, SINGLE, STEP_NAME, CLASS_TO_CREATE
from ils.sfc.recipeData.api import substituteScopeReferences, s88DataExists, s88Get, s88Set, s88DataExists, s88GetStep
from ils.sfc.recipeData.core import getStepIdFromUUID
from ils.sfc.recipeData.createApi import createDynamicRecipe

def activate(scopeContext, stepProperties, state):
    
    try: 
        chartScope = scopeContext.getChartScope()
        stepScope = scopeContext.getStepScope()
        chartPath = getChartPath(chartScope)
        stepName = getStepProperty(stepProperties, STEP_NAME)
        log = getChartLogger(chartScope)
        log.tracef("In %s.activate(), with chart: %s, step: %s", __name__, chartPath, stepName)
        database = getDatabaseName(chartScope)
        
        fetchMode = getStepProperty(stepProperties, FETCH_MODE) # SINGLE or MULTIPLE
        resultsMode = getStepProperty(stepProperties, RESULTS_MODE) # UPDATE or CREATE
        recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
        keyMode = getStepProperty(stepProperties, KEY_MODE) # STATIC or DYNAMIC
        classToCreate = getStepProperty(stepProperties, CLASS_TO_CREATE)

        ''' Validate the configuration '''
        if not(resultsMode == UPDATE or resultsMode == UPDATE_OR_CREATE):
            txt = "ERROR: Illegal RESULTS mode: <%s>, legal values are %s or %s" % (resultsMode, UPDATE, UPDATE_OR_CREATE)
            handleExpectedGatewayError(chartScope, stepName, txt, log)
            return
    
        sql = getStepProperty(stepProperties, SQL)
        processedSql = substituteScopeReferences(chartScope, stepScope, sql)
        log.tracef("SQL: %s", processedSql)
        log.tracef("Fetch mode: %s, Key mode: %s, Results mode: %s", fetchMode, keyMode, resultsMode)
        
        if fetchMode == SINGLE:    
            pds = system.db.runQuery(processedSql, database)
            
            if len(pds) == 0:
                txt = "Query did not return any rows, %s" % (processedSql)
                handleExpectedGatewayError(chartScope, stepName, txt, log)
                return
            
            if len(pds) > 1:
                txt = "Query return %d rows when configured in SINGLE fetch mode, %s" % (len(pds), processedSql)
                handleExpectedGatewayError(chartScope, stepName, txt, log)
                return
            
            ds = system.dataset.toDataSet(pds)
            columnNames = ds.getColumnNames()
            log.tracef("The columns are: %s", columnNames)
            
            if keyMode == STATIC:
                key = getStepProperty(stepProperties, KEY)
                attr = columnNames[0]
                log.tracef("The static key is %s", key)
            else:
                key = ds.getValueAt(0, 0)
                attr = columnNames[1]
                print "The dynamic key is: %s" % (str(key))

            ''' I need an attribute, even if we are returning multiple values, in order to call dataEists. '''
            keyAndAttr = key + "." + attr

            recordExists = s88DataExists(chartScope, stepScope, keyAndAttr, recipeLocation)
            if not(recordExists) and resultsMode == UPDATE:
                txt = "The recipe data with key <%s> does not exist at scope: %s for a static simple query" % (keyAndAttr, recipeLocation)
                handleExpectedGatewayError(chartScope, stepName, txt, log)
                return
            
            if not(recordExists) and resultsMode == UPDATE_OR_CREATE:
                log.tracef("**** Create a Recipe data entry ***")
                stepUUID, stepName, crap = s88GetStep(chartScope, stepScope, recipeLocation, "foo.value")
                stepId = getStepIdFromUUID(stepUUID, database)
                recipeDataId = createDynamicRecipe(stepId, classToCreate, key, database)
                log.tracef("Created new recipe data %s with id: %d", classToCreate, recipeDataId)
        
            i = 0
            for columnName in columnNames: 
                val = ds.getValueAt(0, i)
                log.tracef("%s: %s", columnName, val)
                
                if keyMode == DYNAMIC and i == 0:
                    log.tracef("...skipping the key...")
                else:    
                    keyAndAttr = key + "." + columnName
                    log.tracef("keyAndAttr: %s", keyAndAttr)
                    s88Set(chartScope, stepScope, keyAndAttr, val, recipeLocation)
                
                i = i + 1
        else:
            ''' MULTIPLE RECORDS '''
            if keyMode == STATIC:
                txt = "Invalid step configuration!  A query that returns multiple rows MUST specify a dynamic key!"
                handleExpectedGatewayError(chartScope, stepName, txt, log)
                return
                
            pds = system.db.runQuery(processedSql, database)
            log.infof("%s returned %d records  *** MULTIPLE RECORDS ***", processedSql, len(pds))
            
            if len(pds) == 0:
                log.warnf("A Query that was defined to return multiple rows did not return any, this may or may not be an error! %s" % (processedSql))
                return

            ds = system.dataset.toDataSet(pds)
            columnNames = ds.getColumnNames()
            print "The columns are: ", columnNames
            
            
            for row in range(ds.getRowCount()):
                print "----------------------------"
                print "Handling record #%d" % (row)
                key = ds.getValueAt(row, 0)
                print "Raw Key: ", key
                key = string.replace(key, ".", "_")
                print "Modified Key: ", key
                attr = columnNames[1]
                print "The dynamic key is: %s" % (str(key))

                ''' I need an attribute, even if we are returning multiple values, in order to call dataEists. '''
                keyAndAttr = key + "." + attr
    
                recordExists = s88DataExists(chartScope, stepScope, keyAndAttr, recipeLocation)
                if not(recordExists) and resultsMode == UPDATE:
                    txt = "The recipe data with key <%s> does not exist at scope: <%s> for a static simple query" % (keyAndAttr, recipeLocation)
                    handleExpectedGatewayError(chartScope, stepName, txt, log)
                    return
                
                if not(recordExists) and resultsMode == UPDATE_OR_CREATE:
                    print "**** Create a Recipe data entity ***"
                    stepUUID, stepName, crap = s88GetStep(chartScope, stepScope, recipeLocation, "foo.value")
                    stepId = getStepIdFromUUID(stepUUID, database)
                    recipeDataId = createDynamicRecipe(stepId, classToCreate, key, database)
                    print "Created new recipe data with id: ", recipeDataId
            
#                log.tracef("   Fetched value: %s", str(val))
                i = 0
                for columnName in columnNames: 
                    val = ds.getValueAt(row, i)
                    print "%s: %s" % (columnName, val)
                    keyAndAttr = key + "." + columnName
                    print "Setting keyAndAttr: %s to %s" % (keyAndAttr, str(val))
                    s88Set(chartScope, stepScope, keyAndAttr, val, recipeLocation)
                    
                    i = i + 1
            

    except:
        log.errorf("**** CAUGHT AN UNEXPECTED ERROR ****")
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in simpleQuery.py', log)
    finally:
        return True
    