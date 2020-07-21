'''
Created on Dec 17, 2015

@author: rforbes
'''

import system, string
from ils.common.util import parseFilename
from ils.sfc.common.constants import GATEWAY, CLIENT, FILENAME, FILE_LOCATION, BUTTON_LABEL, POSITION, SCALE, WINDOW_TITLE, PRINT_FILE, VIEW_FILE, SHOW_PRINT_DIALOG, WINDOW_ID, \
    IS_SFC_WINDOW, WINDOW_PATH
from ils.sfc.gateway.api import getChartLogger, getDatabaseName, handleUnexpectedGatewayError, getStepProperty, getControlPanelId, createSaveDataRecord, getTopChartRunId, registerWindowWithControlPanel, sendMessageToClient
from ils.sfc.common.util import readFile, isEmpty
    
def activate(scopeContext, stepProperties, state):  

    # extract property values
    try:
        chartScope = scopeContext.getChartScope()
        stepScope = scopeContext.getStepScope()
        
        logger = getChartLogger(chartScope)
        logger.tracef("In %s.activate()", __name__)
        filename = getStepProperty(stepProperties, FILENAME)
        fileLocation = getStepProperty(stepProperties, FILE_LOCATION)
        logger.tracef("File location: %s", fileLocation)
        
        drive, rootFilename, extension = parseFilename(filename)
        logger.tracef("Filename: %s", filename)
        logger.tracef("Drive: %s", drive)
        logger.tracef("File root: %s", rootFilename)
        logger.tracef("Extension: %s", extension)
    
        database = getDatabaseName(chartScope)
        chartRunId = getTopChartRunId(chartScope)
        controlPanelId = getControlPanelId(chartScope)
        buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL) 
        if isEmpty(buttonLabel):
            buttonLabel = 'Print'
        position = getStepProperty(stepProperties, POSITION) 
        scale = getStepProperty(stepProperties, SCALE) 
        title = getStepProperty(stepProperties, WINDOW_TITLE) 
        if isEmpty(title):
            title = filename
 
        if fileLocation == GATEWAY:
            if string.upper(extension) == "PDF":
                textData = None
                binaryData = system.file.readFileAsBytes(filename)
            else:
                textData = readFile(filename)
                binaryData = None
        else:
            textData = None
            binaryData = None
            
        printFile = getStepProperty(stepProperties, PRINT_FILE) 
        showPrintDialog = getStepProperty(stepProperties, SHOW_PRINT_DIALOG) 
        viewFile = getStepProperty(stepProperties, VIEW_FILE) 
        windowPath = "SFC/ViewFile"
        messageHandler = "sfcOpenWindow"
        
        windowId = registerWindowWithControlPanel(chartRunId, controlPanelId, windowPath, buttonLabel, position, scale, title, database)
        stepScope[WINDOW_ID] = windowId    

        createSaveDataRecord(windowId, textData, binaryData, filename, fileLocation, printFile, showPrintDialog, viewFile, database, extension)

        payload = {WINDOW_ID: windowId, WINDOW_PATH: windowPath, IS_SFC_WINDOW: True}
        sendMessageToClient(chartScope, messageHandler, payload)
  
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in printFile.py', logger)
    finally:
        return True