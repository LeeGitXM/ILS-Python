'''
Common code for input steps: Yes/No, Input, Input w. choices
Created on Dec 21, 2015
@author: rforbes
'''
def activate(scopeContext, stepProperties, windowType, choices='', lowLimit='null', highLimit='null'):
    '''
    Action for java InputStep
    Get an response from the user; block until a
    response is received, put response in chart properties
    '''
    from ils.sfc.gateway.util import getTimeoutSeconds, getControlPanelId, createWindowRecord, getStepProperty, waitOnResponse, getRecipeScope, sendOpenWindow, sendCloseWindow, handleUnexpectedGatewayError
    from ils.sfc.gateway.api import getDatabaseName, s88Set, getChartLogger
    from system.ils.sfc.common.Constants import BUTTON_LABEL, POSITION, SCALE, WINDOW_TITLE, PROMPT, KEY
    import system.util
    import time
    import system.db
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    chartLogger = getChartLogger(chartScope)
    
    # window common properties:
    controlPanelId = getControlPanelId(chartScope)
    buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL) 
    position = getStepProperty(stepProperties, POSITION) 
    scale = getStepProperty(stepProperties, SCALE) 
    title = getStepProperty(stepProperties, WINDOW_TITLE) 

    database = getDatabaseName(chartScope)
     
    # step-specific properties:
    prompt = getStepProperty(stepProperties, PROMPT)
    recipeLocation = getRecipeScope(stepProperties) 
    key = getStepProperty(stepProperties, KEY) 

    # calculate the absolute timeout time in epoch secs:
    timeoutDurationSecs = getTimeoutSeconds(chartScope, stepProperties)
    if(timeoutDurationSecs > 0):
        timeoutTime = time.time() + timeoutDurationSecs
    else:
        timeoutTime = 0

    # create db window records:
    windowId = createWindowRecord(controlPanelId, windowType, buttonLabel, position, scale, title, database)
    # Note: the low/high limits are formatted as strings so we can insert 'null' if desired
    lowLimit = str(lowLimit)
    highLimit = str(highLimit)
    
    numInserted = system.db.runUpdateQuery("insert into SfcInput (windowId, prompt, recipeLocation, recipeKey, lowLimit, highLimit) values ('%s', '%s', '%s', '%s', %s, %s)" % (windowId, prompt, recipeLocation, key, lowLimit, highLimit), database)
    if numInserted == 0:
        handleUnexpectedGatewayError(chartScope, 'Failed to insert row into SfcInput', chartLogger)
        
    if choices != None:
        choicesList = system.util.jsonDecode(choices)
        for choice in choicesList:
            system.db.runUpdateQuery("insert into SfcInputChoices (windowId, choice) values ('%s', '%s')" % (windowId, choice), database)
            
        
    sendOpenWindow(chartScope, windowId, database)
    
    value = waitOnResponse(windowId, chartScope, timeoutTime)
    if value == None:
        print "timed out"
        value = "Timeout"
    s88Set(chartScope, stepScope, key, value, recipeLocation)
    
    # delete db window records:
    print 'deleting window records', windowId
    if choices != None:
        system.db.runUpdateQuery("delete from SfcInputChoices where windowId = '%s'" % (windowId), database)
    system.db.runUpdateQuery("delete from SfcInput where windowId = '%s'" % (windowId), database)
    system.db.runUpdateQuery("delete from SfcWindow where windowId = '%s'" % (windowId), database)
    sendCloseWindow(chartScope, windowId)
