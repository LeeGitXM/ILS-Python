'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):    
    from ils.sfc.gateway.util import sendMessageToClient, hasStepProperty, getStepProperty, transferStepPropertiesToMessage, waitOnResponse
    from ils.sfc.gateway.api import s88Set
    from system.ils.sfc.common.Constants import AUTO_MODE, SEMI_AUTOMATIC, PRIMARY_REVIEW_DATA_WITH_ADVICE, SECONDARY_REVIEW_DATA_WITH_ADVICE, BUTTON_KEY, BUTTON_KEY_LOCATION 
    from ils.sfc.common.constants import PRIMARY_REVIEW_DATA, PRIMARY_CONFIG, SECONDARY_CONFIG, SECONDARY_REVIEW_DATA
    from system.ils.sfc import getReviewData
    chartScope = scopeContext.getChartScope() 
    stepScope = scopeContext.getStepScope()
    autoMode = getStepProperty(stepProperties, AUTO_MODE) 
    if autoMode == SEMI_AUTOMATIC:   
        showAdvice = hasStepProperty(stepProperties, PRIMARY_REVIEW_DATA_WITH_ADVICE)
        if showAdvice:
            primaryConfig = getStepProperty(stepProperties, PRIMARY_REVIEW_DATA_WITH_ADVICE) 
            secondaryConfig = getStepProperty(stepProperties, SECONDARY_REVIEW_DATA_WITH_ADVICE) 
            primaryConfig = getStepProperty(stepProperties, PRIMARY_REVIEW_DATA)        
            secondaryConfig = getStepProperty(stepProperties, SECONDARY_REVIEW_DATA)        
        payload = dict()
        transferStepPropertiesToMessage(stepProperties, payload)
        payload[PRIMARY_CONFIG] = getReviewData(chartScope, stepScope, primaryConfig, showAdvice)
        payload[SECONDARY_CONFIG] = getReviewData(chartScope, stepScope, secondaryConfig, showAdvice)
        messageId = sendMessageToClient(chartScope, 'sfcReviewData', payload)    
        responseValue = waitOnResponse(messageId, chartScope)
        recipeKey = getStepProperty(stepProperties, BUTTON_KEY)
        recipeLocation = getStepProperty(stepProperties, BUTTON_KEY_LOCATION)
        s88Set(chartScope, stepScope, recipeKey, responseValue, recipeLocation )
    else: # AUTOMATIC
        # ?? nothing to do ? we got the values from the recipe data ?!
        pass
