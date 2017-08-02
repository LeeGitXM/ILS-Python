'''
Created on Dec 17, 2015

@author: rforbes
'''

from ils.sfc.common.constants import COMPUTER, SERVER, FILENAME, BUTTON_LABEL, POSITION, SCALE, WINDOW_TITLE, PRINT_FILE, VIEW_FILE, SHOW_PRINT_DIALOG
from ils.sfc.gateway.api import getChartLogger, getDatabaseName, handleUnexpectedGatewayError, getStepProperty, getControlPanelId, createWindowRecord, createSaveDataRecord, sendOpenWindow, getStepId
from ils.sfc.common.util import readFile, isEmpty
    
def activate(scopeContext, stepProperties, state):  

    # extract property values
    try:
        chartScope = scopeContext.getChartScope()
        chartLogger = getChartLogger(chartScope)
        fileName = getStepProperty(stepProperties, FILENAME) 
        database = getDatabaseName(chartScope)
        stepId = getStepId(stepProperties) 
        controlPanelId = getControlPanelId(chartScope)
        buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL) 
        if isEmpty(buttonLabel):
            buttonLabel = 'Print'
        position = getStepProperty(stepProperties, POSITION) 
        scale = getStepProperty(stepProperties, SCALE) 
        title = getStepProperty(stepProperties, WINDOW_TITLE) 
        if isEmpty(title):
            title = fileName
 
        computer = getStepProperty(stepProperties, COMPUTER) 
        if computer == SERVER:
            text = readFile(fileName)
        else:
            text = ''
        printFile = getStepProperty(stepProperties, PRINT_FILE) 
        showPrintDialog = getStepProperty(stepProperties, SHOW_PRINT_DIALOG) 
        viewFile = getStepProperty(stepProperties, VIEW_FILE) 
        windowId = createWindowRecord(controlPanelId, 'SFC/SaveData', buttonLabel, position, scale, title, database)
        createSaveDataRecord(windowId, text, fileName, computer, printFile, showPrintDialog, viewFile, database)
        sendOpenWindow(chartScope, windowId, stepId, database)
  
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in printFile.py', chartLogger)
    finally:
        return True