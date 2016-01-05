'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):
    from ils.sfc.gateway.util import dictToString, getStepProperty, createFilepath, sendMessageToClient
    from ils.sfc.gateway.api import getChartLogger, getProject
    from system.ils.sfc.common.Constants import RECIPE_LOCATION, PRINT_FILE, VIEW_FILE, DATA, FILEPATH
    from ils.sfc.gateway.recipe import browseRecipeData
    # extract property values
    chartScope = scopeContext.getChartScope()
    logger = getChartLogger(chartScope)
    stepScope = scopeContext.getStepScope()
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
    printFile = getStepProperty(stepProperties, PRINT_FILE) 
    viewFile = getStepProperty(stepProperties, VIEW_FILE) 
        
    # get the data at the given location
    recipeData = browseRecipeData(chartScope, stepScope, recipeLocation)
    dataText = dictToString(recipeData)
    if chartScope == None:
        logger.error("data for location " + recipeLocation + " not found")
    # write the file
    filepath = createFilepath(chartScope, stepProperties, True)
    fp = open(filepath, 'w')
    fp.write(dataText)
    fp.close()
    
    # send message to client for view/print
    if printFile or viewFile:
        payload = dict()
        payload[DATA] = dataText
        payload[FILEPATH] = filepath
        payload[PRINT_FILE] = printFile
        payload[VIEW_FILE] = viewFile
        project = getProject(chartScope)
        sendMessageToClient(project, 'sfcSaveData', payload)