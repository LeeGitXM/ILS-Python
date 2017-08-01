'''
Created on Dec 17, 2015

@author: rforbes
'''

import system
from ils.sfc.gateway.api import getDatabaseName, s88Set, getChartLogger, handleUnexpectedGatewayError, getStepProperty
from ils.sfc.common.constants import KEY, RECIPE_LOCATION, SQL
    
def activate(scopeContext, stepProperties, state):
    try:
        chartScope = scopeContext.getChartScope()
        stepScope = scopeContext.getStepScope()
        chartLogger = getChartLogger(chartScope)
        database = getDatabaseName(chartScope)
        sql = getStepProperty(stepProperties, SQL) 
        result = system.db.runQuery(sql, database) # returns a PyDataSet
        jsonResult = system.util.jsonEncode(result)
        recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
        key = getStepProperty(stepProperties, KEY) 
        s88Set(chartScope, stepScope, key, jsonResult, recipeLocation)
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in rawQuery.py', chartLogger)
    finally:
        return True