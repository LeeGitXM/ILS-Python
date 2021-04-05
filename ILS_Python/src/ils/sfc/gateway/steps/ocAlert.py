'''
Created on Mar 18, 2021

@author: phass
'''
from ils.common.ocAlert import sendAlert
from ils.sfc.common.util import isEmpty
from ils.sfc.gateway.steps.commonInput import cleanup
from ils.sfc.gateway.api import getStepProperty, getControlPanelId, getProject, \
        logStepDeactivated, getTopChartRunId, getDatabaseName, getChartLogger, handleUnexpectedGatewayError
from ils.sfc.common.constants import ACK_REQUIRED, BUTTON_CALLBACK, BUTTON_LABEL, WAITING_FOR_REPLY, DEACTIVATED, CANCELLED, \
    ID, INSTANCE_ID, CLIENT_DONE, TOP_MESSAGE, MAIN_MESSAGE, BOTTOM_MESSAGE, OC_ALERT_WINDOW, POST, OC_ALERT_WINDOW_TYPE

def activate(scopeContext, stepProperties, state):
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    log = getChartLogger(chartScope)
    log.tracef("In %s.activate()", __name__)

    if state in [DEACTIVATED, CANCELLED]:
        logStepDeactivated(chartScope, stepProperties)
        cleanup(chartScope, stepProperties, stepScope)
        return False
            
    try:        
        # Check for previous state:
        workDone = False
        waitingForReply = stepScope.get(WAITING_FOR_REPLY, False);
        
        if not waitingForReply:
            # first call; do initialization and cache info in step scope for subsequent calls:
            log.tracef("Initializing a OC Alert step")

            chartId = chartScope.get(INSTANCE_ID, -1)
            stepId = getStepProperty(stepProperties, ID)
            controlPanelId = getControlPanelId(chartScope)
            database = getDatabaseName(chartScope)
            chartRunId = getTopChartRunId(chartScope)
            project = getProject(chartScope)
            
            stepScope[WAITING_FOR_REPLY] = True
            stepScope[CLIENT_DONE] = False
            
            topMessage = getStepProperty(stepProperties, TOP_MESSAGE) 
            mainMessage = getStepProperty(stepProperties, MAIN_MESSAGE) 
            bottomMessage = getStepProperty(stepProperties, BOTTOM_MESSAGE) 
            windowPath = getStepProperty(stepProperties, OC_ALERT_WINDOW) 
            windowType = getStepProperty(stepProperties, OC_ALERT_WINDOW_TYPE) 
            post = getStepProperty(stepProperties, POST)
            buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL)
            if isEmpty(buttonLabel):
                buttonLabel = 'OC Alert'
            buttonCallback = getStepProperty(stepProperties, BUTTON_CALLBACK)
            ackRequired = getStepProperty(stepProperties, ACK_REQUIRED)
            
            if ackRequired:
                log.tracef("Calling sendAlert() ** Requiring an ACK **")
                sendAlert(project, post, topMessage, bottomMessage, mainMessage, buttonLabel, 
                    callbackPayloadDictionary={"chartId": chartId, "stepId": stepId, "buttonCallback": buttonCallback}, callback="ils.common.ocAlert.sfcHandshake", 
                    timeoutEnabled=False, timeoutSeconds=0, db=database, isolationMode=False, windowName=windowPath, windowType=windowType)
                log.trace("   setting ACK flag...")
                stepScope[WAITING_FOR_REPLY] = True
            else:
                sendAlert(project, post, topMessage, bottomMessage, mainMessage, buttonLabel, 
                          callbackPayloadDictionary={}, callback=buttonCallback,
                          timeoutEnabled=False, timeoutSeconds=0, db=database, isolationMode=False, windowName=windowPath, windowType=windowType)
                workDone = True
    
        else: 
            ''' waiting for reply '''
            clientDone = stepScope.get(CLIENT_DONE, False);
            log.tracef("...waiting for the client to ACK (checking clientDone: %s)", str(clientDone))
            if clientDone:
                workDone =True

    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in commonInput.py', log)
        workDone = True
    finally:
        if workDone:
            log.trace("All of the work is done, cleaning up...")
            cleanup(chartScope, stepProperties, stepScope)
        return workDone