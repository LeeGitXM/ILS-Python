'''
Common code for input steps: Yes/No, Input, Input w. choices
Created on Dec 21, 2015
@author: rforbes
'''
def activate(scopeContext, stepProperties, buttonLabel, windowType, choices='', lowLimit=None, highLimit=None):
    '''
    Action for java InputStep
    Get an response from the user; block until a
    response is received, put response in chart properties
    '''
    from ils.sfc.gateway.util import getTimeoutTime, getControlPanelId, createWindowRecord, \
        getStepProperty, waitOnResponse, getRecipeScope, sendOpenWindow, deleteAndSendClose,\
        getStepId, dbStringForFloat, handleUnexpectedGatewayError
    from ils.sfc.common.util import createUniqueId
    from ils.sfc.gateway.api import getDatabaseName, s88Set, getChartLogger, getProject
    from system.ils.sfc.common.Constants import POSITION, SCALE, WINDOW_TITLE, PROMPT, KEY
    import system.util
    import system.db
    
    try:
        chartScope = scopeContext.getChartScope()
        stepScope = scopeContext.getStepScope()
        chartLogger = getChartLogger(chartScope)
        
        # window common properties:
        database = getDatabaseName(chartScope)
        controlPanelId = getControlPanelId(chartScope)
        print 'controlPanelId', controlPanelId
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
        if controlPanelId != None:
            print 'creating window record'
            windowId = createWindowRecord(controlPanelId, windowType, buttonLabel, position, scale, title, database)
            # Note: the low/high limits are formatted as strings so we can insert 'null' if desired
            print 'getting strings for limits'
            lowLimit = dbStringForFloat(lowLimit)
            highLimit = dbStringForFloat(highLimit)
            sql = "insert into SfcInput (windowId, prompt, recipeLocation, recipeKey, lowLimit, highLimit) values ('%s', '%s', '%s', '%s', %s, %s)" % (windowId, prompt, recipeLocation, key, lowLimit, highLimit)
            print sql
            numInserted = system.db.runUpdateQuery(sql, database)
            if numInserted == 0:
                handleUnexpectedGatewayError(chartScope, 'Failed to insert row into SfcInput', chartLogger)
                
            if choices != None:
                choicesList = system.util.jsonDecode(choices)
                for choice in choicesList:
                    system.db.runUpdateQuery("insert into SfcInputChoices (windowId, choice) values ('%s', '%s')" % (windowId, choice), database)
                    
                
            sendOpenWindow(chartScope, windowId, stepId, database)
        else:
            from system.ils.sfc import addRequestId
            # in "headless" test mode; just register the request under an arbitrary id:
            windowId=createUniqueId()
            addRequestId(windowId, stepId)
       
        print "CommonInput: Waiting for response ..."
        response = waitOnResponse(windowId, chartScope, timeoutTime)
        if response == None:
            response = "Timeout"
        print "CommonInput: Received response ",response
        s88Set(chartScope, stepScope, key, response, recipeLocation)
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in commonInput.py', chartLogger)
    finally:
        if controlPanelId!=None:
            # delete db window records:
            if choices != None:
                system.db.runUpdateQuery("delete from SfcInputChoices where windowId = '%s'" % (windowId), database)
            system.db.runUpdateQuery("delete from SfcInput where windowId = '%s'" % (windowId), database)
            project = getProject(chartScope)
            deleteAndSendClose(project, windowId, database)
