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
        getStepProperty, getRecipeScope, sendOpenWindow,\
        getStepId, dbStringForFloat, handleUnexpectedGatewayError
    from ils.sfc.gateway.api import getDatabaseName, s88Set, getChartLogger
    from system.ils.sfc.common.Constants import POSITION, SCALE, WINDOW_TITLE, PROMPT, KEY
    from ils.sfc.common.constants import WAITING_FOR_REPLY, TIMEOUT_TIME, WINDOW_ID
    from system.ils.sfc import getResponse
    import time
    import system.util
    import system.db
    
    try:
#        print "Starting commonInput.activate()..."
        chartScope = scopeContext.getChartScope()
        stepScope = scopeContext.getStepScope()
        
        # Get info from scope common across invocations 
        chartLogger = getChartLogger(chartScope)
        stepId = getStepId(stepProperties) 

        # Check for previous state:
        workDone = False
        waitingForReply = stepScope.get(WAITING_FOR_REPLY, False)
        stepName = stepScope.get("name", "")
        
        if not waitingForReply:
            chartLogger.trace("Initializing step %s..." % (stepName))
            # first call; do initialization and cache info in step scope for subsequent calls:
            # calculate the absolute timeout time in epoch secs:
            stepScope[WAITING_FOR_REPLY] = True
            timeoutTime = getTimeoutTime(chartScope, stepProperties)
            stepScope[TIMEOUT_TIME] = timeoutTime
            controlPanelId = getControlPanelId(chartScope)
            position = getStepProperty(stepProperties, POSITION) 
            scale = getStepProperty(stepProperties, SCALE) 
            title = getStepProperty(stepProperties, WINDOW_TITLE) 
            # step-specific properties:
            prompt = getStepProperty(stepProperties, PROMPT)
            database = getDatabaseName(chartScope)
            windowId = createWindowRecord(controlPanelId, windowType, buttonLabel, position, scale, title, database)
            stepScope[WINDOW_ID] = windowId
            # Note: the low/high limits are formatted as strings so we can insert 'null' if desired
            lowLimit = dbStringForFloat(lowLimit)
            highLimit = dbStringForFloat(highLimit)
            sql = "insert into SfcInput (windowId, prompt, lowLimit, highLimit) values ('%s', '%s', %s, %s)" % (windowId, prompt, lowLimit, highLimit)
            numInserted = system.db.runUpdateQuery(sql, database)
            if numInserted == 0:
                handleUnexpectedGatewayError(chartScope, 'Failed to insert row into SfcInput', chartLogger)
            
            if choices != None:
                choicesList = system.util.jsonDecode(choices)
                for choice in choicesList:
                    system.db.runUpdateQuery("insert into SfcInputChoices (windowId, choice) values ('%s', '%s')" % (windowId, choice), database)                   
                
            sendOpenWindow(chartScope, windowId, stepId, database)
        else: # waiting for reply
#            print "...waiting for reply..."
            recipeLocation = getRecipeScope(stepProperties) 
            key = getStepProperty(stepProperties, KEY)
            
            timeoutTime = stepScope[TIMEOUT_TIME]
            if time.time() > timeoutTime:
                chartLogger.info("Step %s Timed out waiting for a response" % (stepName))
                response = "Timeout"
                s88Set(chartScope, stepScope, key, response, recipeLocation)
                workDone = True
            else:
                windowId = stepScope[WINDOW_ID]
                response = getResponse(windowId)
        
                if response != None:
#                    print "CommonInput: Received response ",response
                    response=response.get("response","Not Found")
                    chartLogger.trace("Step %s received response: %s" % (stepName, response))
                    s88Set(chartScope, stepScope, key, response, recipeLocation)
                    workDone = True           
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in commonInput.py', chartLogger)
        workDone = True
    finally:
        if workDone:
            cleanup(chartScope, stepScope)
        return workDone
    
def cleanup(chartScope, stepScope):
    import system.db
    from ils.sfc.gateway.util import deleteAndSendClose, handleUnexpectedGatewayError
    from ils.sfc.gateway.api import getDatabaseName, getProject, getChartLogger
    from ils.sfc.common.constants import WINDOW_ID

    try:
        database = getDatabaseName(chartScope)
        project = getProject(chartScope)
        windowId = stepScope.get(WINDOW_ID, '???')
        system.db.runUpdateQuery("delete from SfcInputChoices where windowId = '%s'" % (windowId), database)
        system.db.runUpdateQuery("delete from SfcInput where windowId = '%s'" % (windowId), database)   
        deleteAndSendClose(project, windowId, database)
    except:
        chartLogger = getChartLogger(chartScope)
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in cleanup in commonInput.py', chartLogger)

        