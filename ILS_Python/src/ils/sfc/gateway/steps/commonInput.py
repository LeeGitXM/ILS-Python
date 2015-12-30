'''
Common code for input steps: Yes/No, Input, Input w. choices
Created on Dec 21, 2015
@author: rforbes
'''
def activate(scopeContext, stepProperties, windowType, choices='', lowLimit=None, highLimit=None):
    '''
    Action for java InputStep
    Get an response from the user; block until a
    response is received, put response in chart properties
    '''
    from ils.sfc.gateway.util import getTimeoutTime, getControlPanelId, createWindowRecord, \
        getStepProperty, waitOnResponse, getRecipeScope, sendOpenWindow, deleteAndSendClose, \
        handleUnexpectedGatewayError, getStepId, dbStringForFloat
    from ils.sfc.common.util import isEmpty
    from ils.sfc.gateway.api import getDatabaseName, s88Set, getChartLogger
    from system.ils.sfc.common.Constants import BUTTON_LABEL, POSITION, SCALE, WINDOW_TITLE, PROMPT, KEY
    import system.util
    import system.db
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    chartLogger = getChartLogger(chartScope)
    
    # window common properties:
    database = getDatabaseName(chartScope)
    controlPanelId = getControlPanelId(chartScope)
    buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL) 
    if isEmpty(buttonLabel):
        buttonLabel = 'Input'
    position = getStepProperty(stepProperties, POSITION) 
    scale = getStepProperty(stepProperties, SCALE) 
    title = getStepProperty(stepProperties, WINDOW_TITLE) 
    # step-specific properties:
    prompt = getStepProperty(stepProperties, PROMPT)
    recipeLocation = getRecipeScope(stepProperties) 
    key = getStepProperty(stepProperties, KEY) 
    stepId = getStepId(stepProperties) 

    # calculate the absolute timeout time in epoch secs:
    timeoutTime = getTimeoutTime(chartScope, stepProperties)

    # create db window records:
    windowId = createWindowRecord(controlPanelId, windowType, buttonLabel, position, scale, title, database)
    # Note: the low/high limits are formatted as strings so we can insert 'null' if desired
    lowLimit = dbStringForFloat(lowLimit)
    highLimit = dbStringForFloat(highLimit)
    
    numInserted = system.db.runUpdateQuery("insert into SfcInput (windowId, prompt, recipeLocation, recipeKey, lowLimit, highLimit) values ('%s', '%s', '%s', '%s', %s, %s)" % (windowId, prompt, recipeLocation, key, lowLimit, highLimit), database)
    if numInserted == 0:
        handleUnexpectedGatewayError(chartScope, 'Failed to insert row into SfcInput', chartLogger)
        
    if choices != None:
        choicesList = system.util.jsonDecode(choices)
        for choice in choicesList:
            system.db.runUpdateQuery("insert into SfcInputChoices (windowId, choice) values ('%s', '%s')" % (windowId, choice), database)
            
        
    sendOpenWindow(chartScope, windowId, stepId, database)
    
    response = waitOnResponse(windowId, chartScope, timeoutTime)
    if response == None:
        response = "Timeout"
    s88Set(chartScope, stepScope, key, response, recipeLocation)
    
    # delete db window records:
    if choices != None:
        system.db.runUpdateQuery("delete from SfcInputChoices where windowId = '%s'" % (windowId), database)
    system.db.runUpdateQuery("delete from SfcInput where windowId = '%s'" % (windowId), database)
    
    deleteAndSendClose(chartScope, windowId, database)
