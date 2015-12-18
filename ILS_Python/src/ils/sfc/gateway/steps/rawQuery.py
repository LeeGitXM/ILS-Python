'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):
    from ils.sfc.gateway.util import getStepProperty
    from ils.sfc.gateway.api import getDatabaseName, s88Set
    from system.ils.sfc.common.Constants import SQL, RECIPE_LOCATION, KEY
    import system.db
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    database = getDatabaseName(chartScope)
    sql = getStepProperty(stepProperties, SQL) 
    result = system.db.runQuery(sql, database) # returns a PyDataSet
    jsonResult = system.util.jsonEncode(result)
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
    key = getStepProperty(stepProperties, KEY) 
    s88Set(chartScope, stepScope, key, jsonResult, recipeLocation)