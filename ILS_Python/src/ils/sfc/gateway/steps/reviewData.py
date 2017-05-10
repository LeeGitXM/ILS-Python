'''
Created on Dec 17, 2015

@author: rforbes
'''

import system, time
from ils.sfc.common.util import callMethodWithParams
from system.ils.sfc import getReviewData
from ils.sfc.common.util import isEmpty
from ils.common.cast import jsonToDict
from ils.sfc.gateway.steps.commonInput import cleanup, checkForTimeout
from ils.sfc.gateway.util import getStepProperty, getTimeoutTime, getControlPanelId, registerWindowWithControlPanel, \
        logStepDeactivated, getTopChartRunId, handleUnexpectedGatewayError, hasStepProperty, deleteAndSendClose
from ils.sfc.gateway.api import getDatabaseName, getChartLogger, sendMessageToClient, getProject
from ils.sfc.recipeData.api import s88Set, s88Get, s88GetTargetStepUUID
from ils.sfc.common.constants import BUTTON_LABEL, TIMED_OUT, WAITING_FOR_REPLY, TIMEOUT_TIME, \
    WINDOW_ID, POSITION, SCALE, WINDOW_TITLE, PROMPT, WINDOW_PATH, DEACTIVATED, RECIPE_LOCATION, KEY, TARGET_STEP_UUID, \
    PRIMARY_REVIEW_DATA_WITH_ADVICE, SECONDARY_REVIEW_DATA_WITH_ADVICE, PRIMARY_REVIEW_DATA, SECONDARY_REVIEW_DATA, \
    BUTTON_KEY_LOCATION, BUTTON_KEY, ACTIVATION_CALLBACK, CUSTOM_WINDOW_PATH, IS_SFC_WINDOW

def activate(scopeContext, stepProperties, state):
    buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL)
    if isEmpty(buttonLabel):
        buttonLabel = 'Review'
    
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    
    project = getProject(chartScope)
    logger = getChartLogger(chartScope)
    windowPath = "SFC/ReviewData"
    messageHandler = "sfcOpenWindow"
    responseKey = getStepProperty(stepProperties, BUTTON_KEY)
    responseRecipeLocation = getStepProperty(stepProperties, BUTTON_KEY_LOCATION)

    if state == DEACTIVATED:
        logStepDeactivated(chartScope, stepProperties)
        cleanup(chartScope, stepProperties, stepScope)
        return False
            
    try:        
        # Check for previous state:
        workDone = False
        waitingForReply = stepScope.get(WAITING_FOR_REPLY, False);
        
        if not waitingForReply:
            # first call; do initialization and cache info in step scope for subsequent calls:
            # calculate the absolute timeout time in epoch secs:
            logger.tracef("Initializing a Review Data step, the response key is <%s>", responseKey)
            
            # Clear the response recipe data so we know when the client has updated it
            s88Set(chartScope, stepScope, responseKey + ".value", "NULL", responseRecipeLocation)
            
            stepScope[WAITING_FOR_REPLY] = True
            timeoutTime = getTimeoutTime(chartScope, stepProperties)
            stepScope[TIMEOUT_TIME] = timeoutTime
            
            controlPanelId = getControlPanelId(chartScope)
            database = getDatabaseName(chartScope)
            chartRunId = getTopChartRunId(chartScope)
            
            position = getStepProperty(stepProperties, POSITION) 
            scale = getStepProperty(stepProperties, SCALE) 
            title = getStepProperty(stepProperties, WINDOW_TITLE) 
            prompt = getStepProperty(stepProperties, PROMPT)
            
            windowId = registerWindowWithControlPanel(chartRunId, controlPanelId, windowPath, buttonLabel, position, scale, title, database)
            stepScope[WINDOW_ID] = windowId

#----
            logger.trace("Starting to transfer the configuration to the database...")
            showAdvice = hasStepProperty(stepProperties, PRIMARY_REVIEW_DATA_WITH_ADVICE)
            if showAdvice:
                primaryConfigJson = getStepProperty(stepProperties, PRIMARY_REVIEW_DATA_WITH_ADVICE) 
                secondaryConfigJson = getStepProperty(stepProperties, SECONDARY_REVIEW_DATA_WITH_ADVICE) 
            else:
                primaryConfigJson = getStepProperty(stepProperties, PRIMARY_REVIEW_DATA)        
                secondaryConfigJson = getStepProperty(stepProperties, SECONDARY_REVIEW_DATA)     
            
            logger.tracef("The primary configuration: %s", str(primaryConfigJson))
            logger.tracef("The secondary configuration is: %s", str(secondaryConfigJson))
            
            SQL = "insert into SfcReviewData (windowId, showAdvice) "\
                "values ('%s', %d)" % (windowId, showAdvice)
            system.db.runUpdateQuery(SQL, database)
            
            '''
            Transfer the data fro the configuration structures into the database table that will be read by the clients.  If the configuration data
            points to recipe data then evaluate the recipe data and convert to GUI units.
            '''
            
            primaryDict = jsonToDict(primaryConfigJson)
            rows = primaryDict.get("rows", [])
            rowNum = 0
            for row in rows:
                addData(chartScope, stepScope, windowId, row, rowNum, True, showAdvice, database, logger)
                rowNum = rowNum + 1

#TODO            Whatever getReviewData is in Java is no longer needed!
#            secondaryDataset = getReviewData(chartScope, stepScope, secondaryConfigJson, showAdvice)
            secondaryDict = jsonToDict(secondaryConfigJson)
            rows = secondaryDict.get("rows", [])
            rowNum = 0
            for row in rows:
                addData(chartScope, stepScope, windowId, row, rowNum, False, showAdvice, database, logger)
                rowNum = rowNum + 1

            # Look for a custom activation callback
            activationCallback = getStepProperty(stepProperties, ACTIVATION_CALLBACK)
            if activationCallback <> "":
                print "Need to call custom activationCallback: ", ACTIVATION_CALLBACK

                keys = ['scopeContext', 'stepProperties']
                values = [scopeContext, stepProperties]
                try:
                    callMethodWithParams(activationCallback, keys, values)
                except Exception, e:
                    try:
                        cause = e.getCause()
                        errMsg = "Error dispatching gateway message %s: %s" % (activationCallback, cause.getMessage())
                    except:
                        errMsg = "Error dispatching gateway message %s: %s" % (activationCallback, str(e))
                    #TODO: whats the right logger here?
                    print errMsg
                
            customWindowPath = getStepProperty(stepProperties, CUSTOM_WINDOW_PATH)
            if customWindowPath <> "":
                windowPath = customWindowPath

            targetStepUUID = s88GetTargetStepUUID(chartScope, stepScope, responseRecipeLocation)
            payload = {WINDOW_ID: windowId, WINDOW_PATH: windowPath, TARGET_STEP_UUID: targetStepUUID, KEY: responseKey, IS_SFC_WINDOW: True}
            time.sleep(0.1)
            sendMessageToClient(chartScope, messageHandler, payload)
        
        else: # waiting for reply
            response = s88Get(chartScope, stepScope, responseKey + ".value", responseRecipeLocation)
            logger.tracef("...the current response to a review Data step is: %s", str(response))
            
            if response <> None and response <> "NULL":
                logger.tracef("Setting the workDone flag")
                workDone = True
            else:
                timeout = checkForTimeout(stepScope)
                if timeout:
                    logger.tracef("Setting the Timeout flag")
                    stepScope[TIMED_OUT] = True
             
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in commonInput.py', logger)
        workDone = True
    finally:
        if workDone:
            logger.trace("All of the work is done, cleaning up...")
            cleanup(chartScope, stepProperties, stepScope)

    return workDone

         
def addData(chartScope, stepScope, windowId, row, rowNum, isPrimary, showAdvice, database, logger):
    logger.tracef("Adding row: %s", str(row))
    
    if showAdvice:
        advice = row.get("advice", None)
    else:
        advice = ''
        
    units = row.get("units", None)
    
    configKey = row.get("configKey", None)
    key = row.get("valueKey", None)
    scope = row.get("recipeScope", "")
    prompt = row.get("prompt", "Prompt:")
    
    if advice == "null":
        advice = ""
    if prompt == "null":
        prompt = ""
    if units == "null":
        units = ""

    print "Looking at row: %d - %s - %s" % (rowNum, configKey, key)
    

    print "Adding <%s>-<%s>-<%s>-<%s>" % (key, scope, units, prompt)
    if scope == "value":
        val = key
    elif scope in ["", "null", None]:
        val = ""
    else:
        val = s88Get(chartScope, stepScope, key, scope)
        
    SQL = "insert into SfcReviewDataTable (windowId, rowNum, configKey, prompt, value, units, advice, isPrimary) "\
        "values ('%s', %d, '%s', '%s', '%s', '%s', '%s', %d)" % (windowId, rowNum, configKey, prompt, str(val), units, advice, isPrimary)
    print SQL
    system.db.runUpdateQuery(SQL, database)


def cleanup(chartScope, stepProperties, stepScope):
    try:
        database = getDatabaseName(chartScope)
        project = getProject(chartScope)
        windowId = stepScope.get(WINDOW_ID, '???')
        system.db.runUpdateQuery("delete from SfcReviewDataTable where windowId = '%s'" % (windowId), database)
        system.db.runUpdateQuery("delete from SfcReviewData where windowId = '%s'" % (windowId), database)
        project = getProject(chartScope)
        deleteAndSendClose(project, windowId, database)
    except:
        chartLogger = getChartLogger(chartScope)
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in cleanup in reviewData.py', chartLogger)
        
