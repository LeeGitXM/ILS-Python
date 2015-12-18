'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):
    from ils.sfc.gateway.util import getStepProperty, waitOnResponse, getTimeoutSeconds
    from ils.sfc.gateway.api import s88Set, s88Get, sendMessageToClient
    from system.ils.sfc.common.Constants import PROMPT, KEY, CHOICES, CHOICES_RECIPE_LOCATION, CHOICES_KEY, RECIPE_LOCATION, TIMEOUT
    # extract properties
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    prompt = getStepProperty(stepProperties, PROMPT) 
    choicesRecipeLocation = getStepProperty(stepProperties, CHOICES_RECIPE_LOCATION) 
    choicesKey = getStepProperty(stepProperties, CHOICES_KEY) 
    recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
    key = getStepProperty(stepProperties, KEY)     
    timeoutSeconds = getTimeoutSeconds(chartScope, stepProperties)
    
    choices = s88Get(chartScope, stepScope, choicesKey, choicesRecipeLocation)
    
    # send message
    payload = dict()
    payload[PROMPT] = prompt
    payload[CHOICES] = choices
    payload[TIMEOUT] = timeoutSeconds

    messageId = sendMessageToClient(chartScope, 'sfcSelectInput', payload) 
    value = waitOnResponse(messageId, chartScope)
    s88Set(chartScope, stepScope, key, value, recipeLocation)
