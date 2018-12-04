'''
Created on Dec 17, 2015

@author: rforbes
'''

import system, string
from ils.queue.constants import QUEUE_ERROR
from ils.sfc.gateway.api import getIsolationMode
from system.ils.sfc import getProviderName, getPVMonitorConfig, getDatabaseName
from ils.sfc.gateway.api import dictToString, getStepProperty, createFilepath, postToQueue, registerWindowWithControlPanel, getTopChartRunId, \
     getControlPanelId, createWindowRecord, createSaveDataRecord, getStepId, getChartLogger, handleUnexpectedGatewayError, getDatabaseName, sendMessageToClient
from ils.sfc.common.constants import RECIPE_LOCATION, PRINT_FILE, VIEW_FILE, SERVER, POSITION, SCALE, WINDOW_TITLE, BUTTON_LABEL, SHOW_PRINT_DIALOG, NAME, \
    WINDOW_ID, WINDOW_PATH, TARGET_STEP_UUID, IS_SFC_WINDOW, EXTENSION
from ils.sfc.recipeData.api import s88GetRecipeDataDataset
from ils.sfc.recipeData.constants import SIMPLE_VALUE, OUTPUT
    
def activate(scopeContext, stepProperties, state):

    try:
        chartScope = scopeContext.getChartScope()
        chartPath = chartScope.get("chartPath","Unknown")

        logger = getChartLogger(chartScope)
        database = getDatabaseName(chartScope)
        stepScope = scopeContext.getStepScope()
        stepName = getStepProperty(stepProperties, NAME)
        chartRunId = getTopChartRunId(chartScope)

        logger.tracef("In %s.activate(), step: %s, state: %s...", __name__, str(stepName), str(state) )
        
        ''' extract property values '''
        recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION)
        windowTitle = getStepProperty(stepProperties, WINDOW_TITLE)
        extension = getStepProperty(stepProperties, EXTENSION) 
        path, filename = createFilepath(chartScope, stepProperties, False)

        if path == "" or filename == "":
            logger.errorf("ERROR: SaveData step named <%S> on chart <%s> does not specify a directory and/or filename", stepName, chartPath)
            return True
        
        logger.tracef("The <%s> recipe data report will be saved to: %s file: %s", recipeLocation, path, filename)

        ''' get the data at the given location '''
        simpleValueDataset = s88GetRecipeDataDataset(chartScope, stepScope, SIMPLE_VALUE, recipeLocation)
        logger.tracef("Found %d simple value recipe data items", simpleValueDataset.rowCount)
        outputDataset = s88GetRecipeDataDataset(chartScope, stepScope, OUTPUT, recipeLocation)
        logger.tracef("Found %d output recipe data items", outputDataset.rowCount)
            
        printFile = getStepProperty(stepProperties, PRINT_FILE)
        print "Print: ", printFile
        
        if printFile:
            logger.infof("generating a report...")
            try:
                reportPath = "Recipe Data"
                project = "XOM"
                parameters = {"SimpleValue": simpleValueDataset, "Output": outputDataset, "Header": windowTitle}
                action = "save"
                
                if string.upper(extension) in ["CSV", ".CSV"]:
                    format = "csv"
                else:
                    format = "pdf"
                    
                actionSettings = {"path": path, "fileName": filename, "format": format}
                system.report.executeAndDistribute(path=reportPath, project=project, parameters=parameters, action=action, actionSettings=actionSettings)
            except:
                txt = "Error saving recipe data to: %s file: %s" % (path, filename)
                logger.error(txt)
                postToQueue(chartScope, QUEUE_ERROR, txt)
        
        viewFile = getStepProperty(stepProperties, VIEW_FILE) 
        print "View: ", viewFile
        
        if viewFile:
            logger.infof("Sending a message to clients to view th erecipe data report...")
            ''' Insert a window record into the database '''
            controlPanelId = getControlPanelId(chartScope)
            buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL)
            position = getStepProperty(stepProperties, POSITION)
            scale = getStepProperty(stepProperties, SCALE)
            title = getStepProperty(stepProperties, WINDOW_TITLE)
            windowPath = "SFC/SaveData"
            messageHandler = "sfcOpenWindow"
            
            windowId = registerWindowWithControlPanel(chartRunId, controlPanelId, windowPath, buttonLabel, position, scale, title, database)
            stepScope[WINDOW_ID] = windowId # This step completes as soon as the GUI is posted do I doubt I need to save this.
    
            print "Inserted a window with id: ", windowId
            
            payload = {WINDOW_ID: windowId, WINDOW_PATH: windowPath, "simpleValue": simpleValueDataset, "output": outputDataset, "header": windowTitle, IS_SFC_WINDOW: True}
            sendMessageToClient(chartScope, messageHandler, payload)
            
            logger.tracef("   Save Data Payload: %s", str(payload))

        logger.trace("...leaving saveData.activate()")      
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in monitorDownload.py', logger)


    finally:
        return True