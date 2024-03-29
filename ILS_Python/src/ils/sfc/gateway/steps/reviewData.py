'''
Created on Dec 17, 2015

@author: rforbes
'''

import system, time
from ils.sfc.common.util import callMethodWithParams, isEmpty
from ils.common.cast import jsonToDict, isFloat
from ils.sfc.gateway.api import getStepProperty, getControlPanelId, registerWindowWithControlPanel, \
        logStepDeactivated, getTopChartRunId, hasStepProperty, deleteAndSendClose, getDatabaseName, getChartLogger, \
        sendMessageToClient, getProject, handleUnexpectedGatewayError
from ils.sfc.recipeData.api import s88Set, s88Get, s88GetStep, s88GetWithUnits, s88GetUnits, substituteScopeReferences
from ils.sfc.common.constants import BUTTON_LABEL, WAITING_FOR_REPLY, WINDOW_ID, POSITION, SCALE, WINDOW_TITLE, WINDOW_PATH, \
    DEACTIVATED, CANCELLED, PRIMARY_REVIEW_DATA_WITH_ADVICE, SECONDARY_REVIEW_DATA_WITH_ADVICE, PRIMARY_REVIEW_DATA, SECONDARY_REVIEW_DATA, \
    BUTTON_KEY_LOCATION, BUTTON_KEY, ACTIVATION_CALLBACK, CUSTOM_WINDOW_PATH, IS_SFC_WINDOW, PRIMARY_TAB_LABEL, SECONDARY_TAB_LABEL, REFERENCE_SCOPE

def activate(scopeContext, stepProperties, state):
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    
    logger = getChartLogger(chartScope)
    windowPath = "SFC/ReviewData"
    messageHandler = "sfcOpenWindow"
    responseKey = getStepProperty(stepProperties, BUTTON_KEY)
    responseRecipeLocation = getStepProperty(stepProperties, BUTTON_KEY_LOCATION)

    if state in [DEACTIVATED, CANCELLED]:
        logStepDeactivated(chartScope, stepProperties)
        cleanup(chartScope, stepProperties, stepScope, logger)
        return False
            
    try:        
        # Check for previous state
        workDone = False
        waitingForReply = stepScope.get(WAITING_FOR_REPLY, False);
        
        if not waitingForReply:
            # first call; do initialization and cache info in step scope for subsequent calls:
            logger.tracef("Initializing a Review Data step, the response key is <%s>", responseKey)

            # Clear the response recipe data so we know when the client has updated it
            if responseRecipeLocation != REFERENCE_SCOPE:
                responseKey = responseKey + ".value"

            s88Set(chartScope, stepScope, responseKey, "NULL", responseRecipeLocation)
            
            stepScope[WAITING_FOR_REPLY] = True
            
            controlPanelId = getControlPanelId(chartScope)
            database = getDatabaseName(chartScope)
            chartRunId = getTopChartRunId(chartScope)
            
            position = getStepProperty(stepProperties, POSITION) 
            scale = getStepProperty(stepProperties, SCALE) 
            title = getStepProperty(stepProperties, WINDOW_TITLE) 
            
            customWindowPath = getStepProperty(stepProperties, CUSTOM_WINDOW_PATH)
            if customWindowPath <> "":
                windowPath = customWindowPath
            
            primaryTabLabel = getStepProperty(stepProperties, PRIMARY_TAB_LABEL) 
            if primaryTabLabel in ["", None]:
                primaryTabLabel = "Primary"
            
            secondaryTabLabel = getStepProperty(stepProperties, SECONDARY_TAB_LABEL)
            if secondaryTabLabel in ["", None]:
                secondaryTabLabel = "Secondary"
            
            buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL)
            if isEmpty(buttonLabel):
                buttonLabel = 'Review'
            
            windowId = registerWindowWithControlPanel(chartRunId, controlPanelId, windowPath, buttonLabel, position, scale, title, database)
            stepScope[WINDOW_ID] = windowId

            showAdvice = hasStepProperty(stepProperties, PRIMARY_REVIEW_DATA_WITH_ADVICE)
            if showAdvice:
                primaryConfigJson = getStepProperty(stepProperties, PRIMARY_REVIEW_DATA_WITH_ADVICE) 
                secondaryConfigJson = getStepProperty(stepProperties, SECONDARY_REVIEW_DATA_WITH_ADVICE) 
            else:
                primaryConfigJson = getStepProperty(stepProperties, PRIMARY_REVIEW_DATA)        
                secondaryConfigJson = getStepProperty(stepProperties, SECONDARY_REVIEW_DATA)     
            
            logger.tracef("The primary configuration: %s", str(primaryConfigJson))
            logger.tracef("The secondary configuration is: %s", str(secondaryConfigJson))
            
            targetStepId, stepName, responseKey = s88GetStep(chartScope, stepScope, responseRecipeLocation, responseKey, database)
            
            SQL = "insert into SfcReviewData (windowId, showAdvice, targetStepId, responseKey, primaryTabLabel, secondaryTabLabel) "\
                "values ('%s', %d, '%s', '%s', '%s', '%s')" % (windowId, showAdvice, targetStepId, responseKey, primaryTabLabel, secondaryTabLabel)
            system.db.runUpdateQuery(SQL, database)
            
            '''
            Transfer the data from the configuration structures into the database table that will be read by the clients.  If the configuration data
            points to recipe data then evaluate the recipe data and convert to GUI units.
            '''
            logger.trace("Starting to transfer the configuration to the database...")
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
                logger.tracef("Calling custom activationCallback: %s", ACTIVATION_CALLBACK)

                keys = ['scopeContext', 'stepProperties']
                values = [scopeContext, stepProperties]
                try:
                    callMethodWithParams(activationCallback, keys, values)
                except Exception, e:
                    try:
                        cause = e.getCause()
                        errMsg = "Error calling custom activation callback for a reviewData task %s: %s" % (activationCallback, cause.getMessage())
                    except:
                        errMsg = "Error calling custom activation callback for a reviewData task %s: %s" % (activationCallback, str(e))

                    handleUnexpectedGatewayError(chartScope, stepProperties, errMsg, logger)
                    workDone = True
            
            payload = {WINDOW_ID: windowId, WINDOW_PATH: windowPath, IS_SFC_WINDOW: True}
            time.sleep(0.1)
            sendMessageToClient(chartScope, messageHandler, payload)
        
        else: # waiting for reply
            if responseRecipeLocation != REFERENCE_SCOPE:
                responseKey = responseKey + ".value"
            response = s88Get(chartScope, stepScope, responseKey, responseRecipeLocation)
            logger.tracef("...the current response to a review Data step is: %s", str(response))
            
            if response <> None and response <> "NULL":
                logger.tracef("Setting the workDone flag")
                workDone = True
             
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in %s.activate' % (__name__), logger)
        workDone = True
    finally:
        if workDone:
            logger.trace("All of the work is done, cleaning up...")
            cleanup(chartScope, stepProperties, stepScope, logger)

    return workDone

         
def addData(chartScope, stepScope, windowId, row, rowNum, isPrimary, showAdvice, database, logger):
    logger.tracef("Adding row: %s", str(row))
    
    configKey = row.get("configKey", None)
    key = row.get("valueKey", None)
    scope = row.get("recipeScope", "")
    
    if showAdvice:
        advice = substituteScopeReferences(chartScope, stepScope,  row.get("advice", None) )
        
        ''' If the advice field is blank, and this is not intended as a blank row, then use the advice of the destination recipe data '''
        if advice in ["null", "", None] and scope not in ["", "null", None]:
            if key.find(".") >= 0:
                adviceKey=key[:key.find(".")] + ".advice"
            else:
                adviceKey = key + ".advice"
    
            advice = s88Get(chartScope, stepScope, adviceKey, scope)
            logger.tracef("The advice from recipe is: <%s>", advice)
            if advice in ["null", None]:
                advice = ""
    else:
        advice = ''
        
    units = row.get("units", None)
    
    
    prompt = substituteScopeReferences(chartScope, stepScope, row.get("prompt", "Prompt:") )
    
    if advice == "null":
        advice = ""
    if prompt == "null":
        prompt = ""
    if units == "null":
        units = ""

    logger.tracef("Adding <%s>-<%s>-<%s>-<%s>", key, scope, units, prompt)
    
    if scope == "value":
        val = key
    elif scope in ["", "null", None]:
        val = ""
    else:
        if units == "":
            val = s88Get(chartScope, stepScope, key, scope)
        else:
            '''
            Because this is GUI, sometimes we want to use the units as a label rather than forcing unit conversion.  If the recipe
            data units are blank, then don't try to convert.
            '''
            recipeUnits = s88GetUnits(chartScope, stepScope, key, scope)
            if recipeUnits == "":
                val = s88Get(chartScope, stepScope, key, scope)
            else:
                val = s88GetWithUnits(chartScope, stepScope, key, scope, units)
    
    if val is False:
        val = "False"
    elif val is True:
        val = "True"
    elif isFloat(val):
        val = float(val)
        val = "%.4f" % (val)

    if isFloat(advice):
        advice = float(advice)
        advice = "%.4f" % (advice)
    
    SQL = "insert into SfcReviewDataTable (windowId, rowNum, configKey, prompt, value, units, advice, isPrimary) "\
        "values ('%s', %d, '%s', '%s', '%s', '%s', '%s', %d)" % (windowId, rowNum, configKey, prompt, str(val), units, advice, isPrimary)
    system.db.runUpdateQuery(SQL, database)


def cleanup(chartScope, stepProperties, stepScope, logger):
    try:
        logger.tracef("...cleaning up a Review Data step...")
        database = getDatabaseName(chartScope)
        project = getProject(chartScope)
        windowId = stepScope.get(WINDOW_ID, '???')
        system.db.runUpdateQuery("delete from SfcReviewDataTable where windowId = '%s'" % (windowId), database)
        system.db.runUpdateQuery("delete from SfcReviewData where windowId = '%s'" % (windowId), database)
        deleteAndSendClose(project, windowId, database)
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in cleanup in reviewData.py', logger)