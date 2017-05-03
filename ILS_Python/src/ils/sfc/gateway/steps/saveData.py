'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties, state):
    from ils.sfc.gateway.util import dictToString, getStepProperty, createFilepath, \
        handleUnexpectedGatewayError, getControlPanelId, createWindowRecord, \
        createSaveDataRecord, getStepId, sendOpenWindow
    from ils.sfc.gateway.api import getChartLogger, getDatabaseName
    from system.ils.sfc.common.Constants import RECIPE_LOCATION, PRINT_FILE, VIEW_FILE, \
    SERVER, POSITION, SCALE, WINDOW_TITLE, BUTTON_LABEL, SHOW_PRINT_DIALOG
    from ils.sfc.gateway.recipe import browseRecipeData
    from ils.sfc.common.util import isEmpty
    
    try:
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
            database = getDatabaseName(chartScope)
            stepId = getStepId(stepProperties) 
            controlPanelId = getControlPanelId(chartScope)
            buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL) 
            if isEmpty(buttonLabel):
                buttonLabel = 'Save'
            position = getStepProperty(stepProperties, POSITION) 
            showPrintDialog = getStepProperty(stepProperties, SHOW_PRINT_DIALOG) 
            scale = getStepProperty(stepProperties, SCALE) 
            title = getStepProperty(stepProperties, WINDOW_TITLE) 
            if isEmpty(title):
                title = filepath
            windowId = createWindowRecord(controlPanelId, 'SFC/SaveData', buttonLabel, position, scale, title, database)
            createSaveDataRecord(windowId, dataText, filepath, SERVER, printFile, showPrintDialog, viewFile, database)
            sendOpenWindow(chartScope, windowId, stepId, database)
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in saveData.py', logger) 
    finally:
        return True