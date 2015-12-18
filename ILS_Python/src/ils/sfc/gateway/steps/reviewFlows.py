'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):    
    from ils.sfc.gateway.util import sendMessageToClient, transferStepPropertiesToMessage, getStepProperty, waitOnResponse
    from ils.sfc.gateway.api import s88Set
    from system.ils.sfc import getReviewFlows, getReviewFlowsConfig
    from system.ils.sfc.common.Constants import BUTTON_KEY, BUTTON_KEY_LOCATION, VALUE, AUTO_MODE, SEMI_AUTOMATIC, OK, DATA, REVIEW_FLOWS, HEADING1, HEADING2, HEADING3
    chartScope = scopeContext.getChartScope() 
    stepScope = scopeContext.getStepScope()
    configJson = getStepProperty(stepProperties, REVIEW_FLOWS) 
    config = getReviewFlowsConfig(configJson) 
    dataset = getReviewFlows(chartScope, stepScope, configJson)  
    autoMode = getStepProperty(stepProperties, AUTO_MODE) 
    if autoMode == SEMI_AUTOMATIC:   
        payload = dict()
        transferStepPropertiesToMessage(stepProperties, payload)
        payload[DATA] = dataset
        payload[HEADING1] = getStepProperty(stepProperties, HEADING1) 
        payload[HEADING2] = getStepProperty(stepProperties, HEADING2) 
        payload[HEADING3] = getStepProperty(stepProperties, HEADING3) 
        messageId = sendMessageToClient(chartScope, 'sfcReviewFlows', payload)     
        response = waitOnResponse(messageId, chartScope)
        responseButton = response[VALUE]
        recipeKey = getStepProperty(stepProperties, BUTTON_KEY)
        recipeLocation = getStepProperty(stepProperties, BUTTON_KEY_LOCATION)
        s88Set(chartScope, stepScope, recipeKey, responseButton, recipeLocation)
        responseDataset = response[DATA]
        if responseButton == OK:
            for i in range(len(config.rows)):
                configRow = config.rows[i]
                responseFlow1 = responseDataset.getValueAt(i,2)
                s88Set(chartScope, stepScope, configRow.flow1Key, responseFlow1, configRow.destination )
                responseFlow2 = responseDataset.getValueAt(i,3)
                s88Set(chartScope, stepScope, configRow.flow2Key, responseFlow2, configRow.destination )
                sumFlows = configRow.flow3Key.lower() == 'sum'
                if not sumFlows:
                    responseFlow3 = responseDataset.getValueAt(i,4)
                    s88Set(chartScope, stepScope, configRow.flow3Key, responseFlow3, configRow.destination )
    else: # AUTOMATIC
        # ?? nothing to do ? we got the values from the recipe data ?!
        pass
