'''
Created on Dec 17, 2015

@author: rforbes
'''

import system, time, string
from ils.sfc.common.util import callMethodWithParams
from ils.sfc.recipeData.api import s88Set, s88Get, s88GetStep, s88GetWithUnits
from ils.common.cast import jsonToDict, isFloat
from ils.sfc.gateway.api import getStepProperty, getControlPanelId, registerWindowWithControlPanel, \
        logStepDeactivated, getTopChartRunId, deleteAndSendClose, getDatabaseName, getChartLogger, sendMessageToClient, getProject, handleUnexpectedGatewayError
from ils.sfc.common.constants import BUTTON_LABEL, WAITING_FOR_REPLY, WINDOW_ID, POSITION, SCALE, WINDOW_TITLE, WINDOW_PATH, DEACTIVATED, CANCELLED, \
    BUTTON_KEY_LOCATION, BUTTON_KEY, ACTIVATION_CALLBACK, CUSTOM_WINDOW_PATH, IS_SFC_WINDOW, HEADING1, HEADING2, HEADING3, REVIEW_FLOWS, SECONDARY_REVIEW_DATA, \
    PRIMARY_TAB_LABEL, SECONDARY_TAB_LABEL, REFERENCE_SCOPE
from ils.sfc.common.util import isEmpty

def activate(scopeContext, stepProperties, state):    
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    
    logger = getChartLogger(chartScope)
    windowPath = "SFC/ReviewFlows"
    messageHandler = "sfcOpenWindow"
    responseKey = getStepProperty(stepProperties, BUTTON_KEY)
    responseRecipeLocation = getStepProperty(stepProperties, BUTTON_KEY_LOCATION)

    if state in [DEACTIVATED, CANCELLED]:
        logStepDeactivated(chartScope, stepProperties)
        cleanup(chartScope, stepProperties, stepScope, logger)
        return False
        
    try:
        workDone = False
        waitingForReply = stepScope.get(WAITING_FOR_REPLY, False);
        
        if not waitingForReply:
            # first call; do initialization and cache info in step scope for subsequent calls:
            logger.tracef("Initializing a Review Flows step, the response key is <%s>", responseKey)
            
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
            heading1 = getStepProperty(stepProperties, HEADING1) 
            heading2 = getStepProperty(stepProperties, HEADING2) 
            heading3 = getStepProperty(stepProperties, HEADING3) 
            
            primaryTabLabel = getStepProperty(stepProperties, PRIMARY_TAB_LABEL) 
            if primaryTabLabel in ["", None]:
                primaryTabLabel = "Primary"
            
            secondaryTabLabel = getStepProperty(stepProperties, SECONDARY_TAB_LABEL)
            if secondaryTabLabel in ["", None]:
                secondaryTabLabel = "Secondary"
            
            buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL)
            if isEmpty(buttonLabel):
                buttonLabel = 'Flows'
    
            customWindowPath = getStepProperty(stepProperties, CUSTOM_WINDOW_PATH)
            if customWindowPath <> "":
                windowPath = customWindowPath
            
            windowId = registerWindowWithControlPanel(chartRunId, controlPanelId, windowPath, buttonLabel, position, scale, title, database)
            stepScope[WINDOW_ID] = windowId

            targetStepUUID, stepName, responseKey = s88GetStep(chartScope, stepScope, responseRecipeLocation, responseKey, database)
            
            SQL = "insert into SfcReviewFlows (windowId, heading1, heading2, heading3, targetStepUUID, responseKey, primaryTabLabel, secondaryTabLabel) "\
                "values (?, ?, ?, ?, ?, ?, ?, ?)"
            system.db.runPrepUpdate(SQL, [windowId, heading1, heading2, heading3, targetStepUUID, responseKey, primaryTabLabel, secondaryTabLabel], database)

            '''
            Transfer the data from the configuration structures into the database table that will be read by the clients.  If the configuration data
            points to recipe data then evaluate the recipe data and convert to GUI units.
            '''
            logger.trace("Starting to transfer the configuration to the database...")
            
            configJson = getStepProperty(stepProperties, REVIEW_FLOWS)
            print "JSON: ", configJson
            configDict = jsonToDict(configJson)
            print "Dictionary: ", configDict
            rows = configDict.get("rows", [])
            rowNum = 0
            for row in rows:
                logger.tracef("...adding row %d", rowNum)
                addData(chartScope, stepScope, windowId, row, rowNum, database, logger)
                rowNum = rowNum + 1
            
            configJson = getStepProperty(stepProperties, SECONDARY_REVIEW_DATA)
            configDict = jsonToDict(configJson)
            rows = configDict.get("rows", [])
            rowNum = 0
            for row in rows:
                addSecondaryData(chartScope, stepScope, windowId, row, rowNum, database, logger)
                rowNum = rowNum + 1

            # Look for a custom activation callback
            activationCallback = getStepProperty(stepProperties, ACTIVATION_CALLBACK)
            if activationCallback <> "":
                logger.tracef("Calling a custom activationCallback: %s", ACTIVATION_CALLBACK)

                keys = ['scopeContext', 'stepProperties']
                values = [scopeContext, stepProperties]
                try:
                    callMethodWithParams(activationCallback, keys, values)
                except Exception, e:
                    try:
                        cause = e.getCause()
                        errMsg = "Error calling custom activation callback for a reviewFlows task %s: %s" % (activationCallback, cause.getMessage())
                    except:
                        errMsg = "Error calling custom activation callback for a reviewFlows task %s: %s" % (activationCallback, str(e))

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
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in reviewFlows.py', logger)
        workDone = True
    finally:
        if workDone:
            cleanup(chartScope, stepProperties, stepScope, logger)

    return workDone
        

def addData(chartScope, stepScope, windowId, row, rowNum, database, logger):
    logger.tracef("Adding row #%d - %s", rowNum, str(row))
    
    advice = row.get("advice", None)    
    units = row.get("units", None)
    
    configKey = row.get("configKey", None)
    key1 = row.get("flow1Key", None)
    key2 = row.get("flow2Key", None)
    key3 = row.get("flow3Key", None)
    scope = row.get("destination", "")
    prompt = row.get("prompt", "Prompt:")
    
    if advice == "null":
        advice = ""
    if prompt == "null":
        prompt = ""
    if units == "null":
        units = ""

    logger.tracef("Adding <%s>-<%s>-<%s>-<%s>-<%s>-<%s>", prompt, scope, units, key1, key2, key3)

    if scope == "value":
        val1 = key1
        val2 = key2
        if string.upper(key3) == "SUM":
            val3 = float(val1) + float(val2)
        else:
            val3 = key3
        
    elif scope in ["", "null", None]:
        val1 = ""
        val2 = ""
        val3 = ""

    else:
        if units == "":
            if key1 in ["", "null", None]:
                val1 = ""
            else:
                val1 = s88Get(chartScope, stepScope, key1, scope)
            
            if key2 in ["", "null", None]:
                val2 = ""
            else:
                val2 = s88Get(chartScope, stepScope, key2, scope)
        else:
            if key1 in ["", "null", None]:
                val1 = ""
            else:
                val1 = s88GetWithUnits(chartScope, stepScope, key1, scope, units)
                
            if key2 in ["", "null", None]:
                val2 = ""
            else:
                val2 = s88GetWithUnits(chartScope, stepScope, key2, scope, units)
            
        if string.upper(key3) == "SUM":
            val3 = val1 + val2
        else:
            if key3 in ["", "null", None]:
                val3 = ""
            else:
                if units == "":
                    val3 = s88Get(chartScope, stepScope, key3, scope)
                else:
                    val3 = s88GetWithUnits(chartScope, stepScope, key3, scope, units)
    
    if val1 is False:
        val1 = "False"
    elif val1 is True:
        val1 = "True"             
    elif isFloat(val1):
        val1 = float(val1)
        val1 = "%.4f" % (val1)
    
    if val2 is False:
        val2 = "False"
    elif val2 is True:
        val2 = "True"
    elif isFloat(val2):
        val2 = float(val2)
        val2 = "%.4f" % (val2)
    
    if val3 is False:
        val3 = "False"
    elif val3 is True:
        val3 = "True"
    elif isFloat(val3):
        val3 = float(val3)
        val3 = "%.4f" % (val3)
        
    SQL = "insert into SfcReviewFlowsTable (windowId, rowNum, configKey, advice, units, prompt, data1, data2, data3, isPrimary) "\
        "values ('%s', %d, '%s', '%s', '%s', '%s', '%s', '%s', '%s', %d)"\
         % (windowId, rowNum, configKey, advice, units, prompt, str(val1), str(val2), str(val3), True)

    logger.tracef("%s", SQL)
    system.db.runUpdateQuery(SQL, database)


def addSecondaryData(chartScope, stepScope, windowId, row, rowNum, database, logger):
    logger.tracef("Adding row %d: %s", rowNum, str(row))
        
    units = row.get("units", None)
    
    configKey = row.get("configKey", None)
    key = row.get("valueKey", None)
    scope = row.get("recipeScope", "")
    prompt = row.get("prompt", "Prompt:")
    
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
            val = s88GetWithUnits(chartScope, stepScope, key, scope, units)
    
    if isFloat(val):
        val = float(val)
        val = "%.4f" % (val)

    SQL = "insert into SfcReviewFlowsTable (windowId, rowNum, configKey, advice, units, prompt, data1, data2, data3, isPrimary) "\
        "values ('%s', %d, '%s', '%s', '%s', '%s', '%s', '%s', '%s', %d)" % (windowId, rowNum, configKey, "", units, prompt, str(val), "", "", False)
    system.db.runUpdateQuery(SQL, database)


def cleanup(chartScope, stepProperties, stepScope, logger):
    try:
        logger.tracef("...cleaning up a review flows step...")
        database = getDatabaseName(chartScope)
        project = getProject(chartScope)
        windowId = stepScope.get(WINDOW_ID, '???')
        system.db.runUpdateQuery("delete from SfcReviewFlowsTable where windowId = '%s'" % (windowId), database)
        system.db.runUpdateQuery("delete from SfcReviewFlows where windowId = '%s'" % (windowId), database)
        deleteAndSendClose(project, windowId, database)
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in cleanup in %s.py' % (__name__), logger)
        