'''
Created on Dec 17, 2015

@author: rforbes
'''
def activate(scopeContext, stepProperties):
    from ils.sfc.gateway.util import getTimeoutSeconds, getStepProperty, waitOnResponse
    from ils.sfc.gateway.api import sendMessageToClient, s88Set
    from system.ils.sfc.common.Constants import PROMPT, RECIPE_LOCATION, MINIMUM_VALUE, MAXIMUM_VALUE, TIMEOUT, KEY
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    prompt = getStepProperty(stepProperties, PROMPT) 
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
    key = getStepProperty(stepProperties, KEY) 
    minimumValue = getStepProperty(stepProperties, MINIMUM_VALUE)
    maximumValue = getStepProperty(stepProperties, MAXIMUM_VALUE) 
    timeoutSeconds = getTimeoutSeconds(chartScope, stepProperties)
        
    payload = dict()
    payload[PROMPT] = prompt
    payload[MINIMUM_VALUE] = minimumValue
    payload[MAXIMUM_VALUE] = maximumValue
    payload[TIMEOUT] = timeoutSeconds
    responseIsValid = False
    while not responseIsValid:
        messageId = sendMessageToClient(chartScope, 'sfcLimitedInput', payload)   
        responseValue = waitOnResponse(messageId, chartScope)
        try:
            floatValue = float(responseValue)
            responseIsValid = floatValue >= minimumValue and floatValue <= maximumValue
        except ValueError:
            payload[PROMPT] = 'Input is not valid. ' + prompt  
    
    s88Set(chartScope, stepScope, key, floatValue, recipeLocation )
