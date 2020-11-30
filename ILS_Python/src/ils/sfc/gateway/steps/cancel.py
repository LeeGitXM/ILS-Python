'''
Created on Dec 16, 2015

@author: rforbes
'''

import system

def activate(scopeContext, stepProperties, state):
    ''' Abort the chart execution'''
    from ils.sfc.common.constants import DEACTIVATED, CANCELLED, STEP_SCOPE, ACK_REQUIRED, WAITING_FOR_REPLY, CENTER, INSTANCE_ID, \
        ID, CLIENT_DONE, WINDOW_ID, WINDOW_PATH, IS_SFC_WINDOW
    from ils.sfc.gateway.steps.commonInput import cleanup
    from ils.sfc.gateway.api import getStepProperty, cancelChart, addControlPanelMessage, getChartLogger,handleUnexpectedGatewayError, logStepDeactivated, \
        getControlPanelId, getDatabaseName, getTopChartRunId, registerWindowWithControlPanel, sendMessageToClient

    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    log = getChartLogger(chartScope)
    log.tracef("In %s.activate() - %s", __name__, state)
        
    windowPath = "SFC/YesNo"
    messageHandler = "sfcOpenWindow"
    responseKey = "ack"
    responseLocation = STEP_SCOPE
    
    log.tracef("Response Location: %s", responseLocation)
    log.tracef("Response Key: %s", responseKey)

    if state in [DEACTIVATED, CANCELLED]:
        logStepDeactivated(chartScope, stepProperties)
        cleanup(chartScope, stepProperties, stepScope)
        return False

    try:    
        ackRequired = getStepProperty(stepProperties, ACK_REQUIRED)
    
        if not(ackRequired):
            log.tracef("Canceling the whole thing (without an ACK!")
            addControlPanelMessage(chartScope, stepProperties, "Chart canceled", "Error", False)
            workDone =True
            
            ''' This will raise the SystemExit exception '''
            cancelChart(chartScope)
            
        else:
            workDone = False
            waitingForReply = stepScope.get(WAITING_FOR_REPLY, False);
        
            if not waitingForReply:
                log.tracef("Setting up cancel with Acknowledgement!")
                
                chartId = chartScope.get(INSTANCE_ID, -1)
                stepId = getStepProperty(stepProperties, ID)
                log.tracef("Chart id: %s", chartId)
                log.tracef("Step id: %s", stepId)
    
                stepScope[WAITING_FOR_REPLY] = True
                stepScope[CLIENT_DONE] = False
                
                controlPanelId = getControlPanelId(chartScope)
                database = getDatabaseName(chartScope)
                chartRunId = getTopChartRunId(chartScope)
                
                position = CENTER
                scale = 1.0
                title = "Cancel Chart Confirmation" 
                buttonLabel = "Cancel"
                prompt = "<HTML>Are you sure you want to <b>cancel</b>?"
                
                windowId = registerWindowWithControlPanel(chartRunId, controlPanelId, windowPath, buttonLabel, position, scale, title, database)
                stepScope[WINDOW_ID] = windowId
                
                ''' Clear the response recipe data so we know when the client has updated it '''
                chartScope.responseKey = None
                
                ''' The recsponse here is totally internal to the implementation.  '''
                responseKeyAndAttribute = responseKey
                targetStepId = -1
                
                SQL = "insert into SfcInput (windowId, prompt, targetStepId, keyAndAttribute, responseLocation, chartId, stepId) values (?, ?, ?, ?, ?, ?, ?)"
                log.tracef(SQL)
                args =  [windowId, prompt, targetStepId, responseKeyAndAttribute, responseLocation, str(chartId), str(stepId)]
                log.tracef(str(args))
                system.db.runPrepUpdate(SQL, args, database)
                
                payload = {WINDOW_ID: windowId, WINDOW_PATH: windowPath, IS_SFC_WINDOW: True}
                sendMessageToClient(chartScope, messageHandler, payload)
            
            else: 
                clientDone = stepScope.get(CLIENT_DONE, False);

                log.tracef("...checking clientDone: %s", str(clientDone))
                if clientDone:
                    ack = stepScope.get("ack", "dunno")
                    workDone =True
                    if ack == "Yes":
                        addControlPanelMessage(chartScope, stepProperties, "Chart canceled", "Error", False)
                        ''' This will raise the SystemExit exception '''
                        cancelChart(chartScope)
                
    except SystemExit:
        ''' This exception is rased by the call to cancelChart().  The normal flow is to come through here. '''
        log.info("The chart has been cancelled!")
    
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in cancel.py', log)
    
    finally:
        if workDone:
            log.tracef("Work is done, cleaning up...")
            cleanup(chartScope, stepProperties, stepScope)
        log.tracef("Returning workdone: %s", str(workDone))
        return workDone
