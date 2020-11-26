'''
Created on Dec 17, 2015

@author: rforbes
'''

import system, string
from ils.queue.constants import QUEUE_ERROR
from ils.sfc.gateway.api import getStepProperty, createFilepath, postToQueue, registerWindowWithControlPanel, getTopChartRunId, \
     getControlPanelId, getChartLogger, handleUnexpectedGatewayError, sendMessageToClient, getDatabaseName
from ils.sfc.common.constants import RECIPE_LOCATION, PRINT_FILE, VIEW_FILE, POSITION, SCALE, WINDOW_TITLE, BUTTON_LABEL, NAME, \
    WINDOW_ID, WINDOW_PATH, IS_SFC_WINDOW, EXTENSION
from ils.sfc.recipeData.api import s88GetRecipeDataDataset
from ils.sfc.recipeData.constants import SIMPLE_VALUE, OUTPUT, OUTPUT_RAMP, INPUT, ARRAY, MATRIX, RECIPE, SQC, TIMER
    
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
        path, filename, filePath = createFilepath(chartScope, stepProperties, False)
        
        logger.tracef("Filepath: %s", filePath)

        if path == "" or filename == "":
            logger.errorf("ERROR: SaveData step named <%s> on chart <%s> does not specify a directory and/or filename", stepName, chartPath)
            return True
        
        logger.tracef("The <%s> recipe data report will be saved to: %s file: %s", recipeLocation, path, filename)

        ''' get the data at the given location '''
        simpleValueDataset = s88GetRecipeDataDataset(chartScope, stepScope, SIMPLE_VALUE, recipeLocation)
        logger.tracef("Found %d simple value recipe data items", simpleValueDataset.rowCount)
        outputDataset = s88GetRecipeDataDataset(chartScope, stepScope, OUTPUT, recipeLocation)
        logger.tracef("Found %d output recipe data items", outputDataset.rowCount)
        outputRampDataset = s88GetRecipeDataDataset(chartScope, stepScope, OUTPUT_RAMP, recipeLocation)
        logger.tracef("Found %d output ramp recipe data items", outputRampDataset.rowCount)
        inputDataset = s88GetRecipeDataDataset(chartScope, stepScope, INPUT, recipeLocation)
        logger.tracef("Found %d input recipe data items", inputDataset.rowCount)
        arrayDataset = s88GetRecipeDataDataset(chartScope, stepScope, ARRAY, recipeLocation)
        logger.tracef("Found %d array recipe data items", arrayDataset.rowCount)
        matrixDataset = s88GetRecipeDataDataset(chartScope, stepScope, MATRIX, recipeLocation)
        logger.tracef("Found %d matrix recipe data items", matrixDataset.rowCount)
        recipeDataset = s88GetRecipeDataDataset(chartScope, stepScope, RECIPE, recipeLocation)
        logger.tracef("Found %d recipe recipe data items", recipeDataset.rowCount)
        sqcDataset = s88GetRecipeDataDataset(chartScope, stepScope, SQC, recipeLocation)
        logger.tracef("Found %d SQC recipe data items", sqcDataset.rowCount)
        timerDataset = s88GetRecipeDataDataset(chartScope, stepScope, TIMER, recipeLocation)
        logger.tracef("Found %d timer recipe data items", timerDataset.rowCount)
        
        '''
        Always save the report to a file
        '''
        try:
            reportPath = "SFC/Recipe Data"
            project = "XOM"
            parameters = {
                "Array": arrayDataset,
                "Input": inputDataset, 
                "Matrix": matrixDataset,
                "Output": outputDataset, 
                "OutputRamp":outputRampDataset, 
                "Recipe": recipeDataset,
                "SimpleValue": simpleValueDataset, 
                "SQC": sqcDataset,
                "Timer": timerDataset,
                "Header": windowTitle}
            
            action = "save"
            
            if string.upper(extension) in ["CSV", ".CSV"]:
                format = "csv"
            elif string.upper(extension) in ["RTF", ".RTF", "TXT",".TXT"]:
                format = "rtf"
            else:
                format = "pdf"
                
            actionSettings = {"path": path, "fileName": filename, "format": format}
            logger.tracef("Action Settings: %s", str(actionSettings))
            logger.tracef("Writing recipe data to: %s%s" % (path, filename))
            system.report.executeAndDistribute(path=reportPath, project=project, parameters=parameters, action=action, actionSettings=actionSettings)
        except:
            txt = "Error saving recipe data to: %s%s" % (path, filename)
            logger.error(txt)
            postToQueue(chartScope, QUEUE_ERROR, txt)

        '''
        Printing is optional
        '''
        printFile = getStepProperty(stepProperties, PRINT_FILE)
        logger.tracef("PrintFile: %s", str(printFile))
        
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
                logger.tracef("Writing recipe data to: %s%s" % (path, filename))
                system.report.executeAndDistribute(path=reportPath, project=project, parameters=parameters, action=action, actionSettings=actionSettings)
            except:
                txt = "Error saving recipe data to: %s file: %s" % (path, filename)
                logger.error(txt)
                postToQueue(chartScope, QUEUE_ERROR, txt)
        
        '''
        Viewing is optional
        '''
        viewFile = getStepProperty(stepProperties, VIEW_FILE) 
        logger.tracef("ViewFile: %s", str(viewFile))
        
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
            
            payload = {
                WINDOW_ID: windowId, 
                WINDOW_PATH: windowPath, 
                "array": arrayDataset,
                "input": inputDataset, 
                "matrix": matrixDataset,
                "output": outputDataset,
                "outputRamp": outputRampDataset, 
                "recipe": recipeDataset,
                "simpleValue": simpleValueDataset, 
                "sqc": sqcDataset,
                "timer": timerDataset,
                "header": windowTitle, 
                IS_SFC_WINDOW: True}
            sendMessageToClient(chartScope, messageHandler, payload)
            
            logger.tracef("   Save Data Payload: %s", str(payload))

        logger.trace("...leaving saveData.activate()")      
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error saving recipe data', logger)

    finally:
        return True