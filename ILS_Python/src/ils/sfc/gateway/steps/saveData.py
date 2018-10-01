'''
Created on Dec 17, 2015

@author: rforbes
'''

import system
from ils.queue.constants import QUEUE_ERROR
from ils.sfc.gateway.api import getIsolationMode
from system.ils.sfc import getProviderName, getPVMonitorConfig, getDatabaseName
from ils.sfc.gateway.api import dictToString, getStepProperty, createFilepath, postToQueue, \
     getControlPanelId, createWindowRecord, createSaveDataRecord, getStepId, getChartLogger, handleUnexpectedGatewayError, getDatabaseName
from ils.sfc.common.constants import RECIPE_LOCATION, PRINT_FILE, VIEW_FILE, SERVER, POSITION, SCALE, WINDOW_TITLE, BUTTON_LABEL, SHOW_PRINT_DIALOG, NAME
from ils.sfc.recipeData.api import s88GetRecipeDataDataset
from ils.sfc.common.util import isEmpty
from ils.sfc.recipeData.constants import SIMPLE_VALUE, OUTPUT
    
def activate(scopeContext, stepProperties, state):

    try:
        # extract property values
        chartScope = scopeContext.getChartScope()
        logger = getChartLogger(chartScope)
        stepScope = scopeContext.getStepScope()
        
        recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION)
        windowTitle = getStepProperty(stepProperties, WINDOW_TITLE)
        path, filename = createFilepath(chartScope, stepProperties, True)
        logger.tracef("The recipe data report will be saved to: %s file: %s", path, filename)

        # get the data at the given location
        simpleValueDataset = s88GetRecipeDataDataset(chartScope, stepScope, SIMPLE_VALUE, recipeLocation)
        logger.tracef("Found %d simple value recipe data items", simpleValueDataset.rowCount)
        outputDataset = s88GetRecipeDataDataset(chartScope, stepScope, OUTPUT, recipeLocation)
        logger.tracef("Found %d output recipe data items", outputDataset.rowCount)
        
        ''' Always save the report to a file '''
        reportPath = "Recipe Data"
        project = "XOM"
        parameters = {"SimpleValue": simpleValueDataset, "Output": outputDataset, "Header": windowTitle}
        action = "save"
        actionSettings = {"path": path, "fileName": filename, "format": "pdf"}
        try:
            system.report.executeAndDistribute(path=reportPath, project=project, parameters=parameters, action=action, actionSettings=actionSettings)
        except:
            txt = "Error saving recipe data to: %s file: %s" % (path, filename)
            logger.error(txt)
            postToQueue(chartScope, QUEUE_ERROR, txt)
            
        printFile = getStepProperty(stepProperties, PRINT_FILE) 
        viewFile = getStepProperty(stepProperties, VIEW_FILE) 
        # write the file
        '''
        filepath = createFilepath(chartScope, stepProperties, True)
        fp = open(filepath, 'w')
        fp.write(dataText)
        fp.close()
        '''
        

        '''
        # send message to client for view/print
        if printFile:
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

        if viewFile:
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
#            sendOpenWindow(chartScope, windowId, stepId, database)
#            sendOpenWindow(chartScope, windowId, stepId, database)
        '''
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in saveData.py', logger) 
    finally:
        return True