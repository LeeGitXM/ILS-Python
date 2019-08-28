'''
Created on Dec 17, 2015

@author: rforbes
'''

import system
from ils.sfc.gateway.api import getDatabaseName, getChartLogger, handleUnexpectedGatewayError, getStepProperty, getChartPath
from ils.sfc.recipeData.api import s88Set
from ils.sfc.common.constants import KEY_AND_ATTRIBUTE, RECIPE_LOCATION, SQL, STEP_NAME, NUMBER_OF_RECORDS
from ils.sfc.recipeData.api import substituteScopeReferences, s88DataExists, s88Get, s88Set, s88DataExists
    
def activate(scopeContext, stepProperties, state):
    try:
        chartScope = scopeContext.getChartScope()
        stepScope = scopeContext.getStepScope()
        chartPath = getChartPath(chartScope)
        stepName = getStepProperty(stepProperties, STEP_NAME)
        log = getChartLogger(chartScope)
        database = getDatabaseName(chartScope)
        recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION)
        keyAndAttribute = getStepProperty(stepProperties, KEY_AND_ATTRIBUTE)
        
        log.tracef("In %s.activate(), with chart: %s, step: %s", __name__, chartPath, stepName)
        
        sql = getStepProperty(stepProperties, SQL) 
        processedSql = substituteScopeReferences(chartScope, stepScope, sql)
        log.tracef("SQL: %s", processedSql)
        
        pds = system.db.runQuery(processedSql, database) # returns a PyDataSet
        log.tracef("...query returned %d records...", len(pds))
        
        stepScope[NUMBER_OF_RECORDS] = len(pds)
        
        vals = []
        for record in pds:
            vals.append(record[0])

        s88Set(chartScope, stepScope, keyAndAttribute, vals, recipeLocation)
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in rawQuery.py', log)
    finally:
        return True