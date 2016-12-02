from ils.sfc.recipeData.core import getTargetStep, fetchRecipeData, getChartUUID, getStepUUID, splitKey

#def s88Get(chartProperties, stepProperties, valuePath, location):
def s88Get(chartProperties, stepProperties, keyAndAttribute, scope):
    print "In s88Get"
    chartUUID = getChartUUID(chartProperties)
    stepUUID = getStepUUID(stepProperties)
    db = ""
    targetStep = getTargetStep(chartUUID, stepUUID, scope, db)
    key,attribute = splitKey(keyAndAttribute)
    val = fetchRecipeData(targetStep, key, attribute, db)
    return val

#def s88Set(chartProperties, stepProperties, valuePath, value, location):
def s88Set(chartProperties, stepProperties, keyAttribute, value, scope):
    print "In s88Set"
    