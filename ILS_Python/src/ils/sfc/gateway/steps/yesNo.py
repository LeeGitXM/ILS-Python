'''
Created on Dec 16, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):
    '''
    Action for java YesNoStep
    Get a yes/no response from the user; block until a
    response is received, put response in chart properties
    '''
    from ils.sfc.gateway.util import getTimeoutSeconds, getControlPanelId, createWindowRecord, getStepProperty, waitOnResponse, getRecipeScope, sendOpenWindow, sendCloseWindow
    from ils.sfc.gateway.api import getDatabaseName, s88Set
    from system.ils.sfc.common.Constants import BUTTON_LABEL, POSITION, SCALE, WINDOW_TITLE, PROMPT, KEY
    import time
    import system.db
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    
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
    windowId = createWindowRecord(controlPanelId, 'SFC/YesNo', buttonLabel, position, scale, title, database)
    system.db.runUpdateQuery("insert into SfcYesNo (windowId, prompt, recipeLocation, recipeKey) values ('%s', '%s', '%s', '%s')" % (windowId, prompt, recipeLocation, key), database)
    sendOpenWindow(chartScope, windowId, database)
    
    value = waitOnResponse(windowId, chartScope, timeoutTime)
    if value == None:
        print "timed out"
        value = "Timeout"
    s88Set(chartScope, stepScope, key, value, recipeLocation)
    
    # delete db window records:
    system.db.runUpdateQuery("delete from SfcYesNo where windowId = '%s'" % (windowId), database)
    system.db.runUpdateQuery("delete from SfcWindow where windowId = '%s'" % (windowId), database)
    sendCloseWindow(chartScope, windowId)
