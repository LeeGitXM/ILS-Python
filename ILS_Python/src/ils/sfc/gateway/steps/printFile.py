'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):  
    from ils.sfc.gateway.util import getStepProperty, handleUnexpectedGatewayError, \
    getControlPanelId, createWindowRecord, createSaveDataRecord
    from system.ils.sfc.common.Constants import COMPUTER, SERVER, FILENAME, BUTTON_LABEL, \
    POSITION, SCALE, WINDOW_TITLE, PRINT_FILE, VIEW_FILE
    from ils.sfc.gateway.api import getChartLogger, getDatabaseName
    from ils.sfc.common.util import readFile, isEmpty
    # extract property values
    try:
        chartScope = scopeContext.getChartScope()
        chartLogger = getChartLogger(chartScope)
        fileName = getStepProperty(stepProperties, FILENAME) 
        database = getDatabaseName(chartScope)
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
        viewFile = getStepProperty(stepProperties, VIEW_FILE) 
        print 'b4 createWindowRecord'      
        windowId = createWindowRecord(controlPanelId, 'SFC/SaveData', buttonLabel, position, scale, title, database)
        print 'b4 createSaveDataRecord'
        createSaveDataRecord(windowId, text, fileName, computer, printFile, viewFile, database)
  
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in printFile.py', chartLogger)
