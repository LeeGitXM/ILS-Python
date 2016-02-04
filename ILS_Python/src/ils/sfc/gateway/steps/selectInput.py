'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties, deactivate):
    from ils.sfc.gateway.util import getStepProperty, handleUnexpectedGatewayError
    from ils.sfc.gateway.api import s88Get, getChartLogger
    from system.ils.sfc.common.Constants import CHOICES_RECIPE_LOCATION, CHOICES_KEY, BUTTON_LABEL
    from ils.sfc.gateway.steps import commonInput
    from ils.sfc.common.util import isEmpty
    
    chartScope = scopeContext.getChartScope()
    chartLogger = getChartLogger(chartScope)
    stepScope = scopeContext.getStepScope()
    buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL)
    if isEmpty(buttonLabel):
        buttonLabel = 'Select'
    
    # Get the choices from recipe data:
    try:
        choicesRecipeLocation = getStepProperty(stepProperties, CHOICES_RECIPE_LOCATION) 
        choicesKey = getStepProperty(stepProperties, CHOICES_KEY) 
        choices = s88Get(chartScope, stepScope, choicesKey, choicesRecipeLocation)    
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in selectInput.py', chartLogger)
        return True
    
    return commonInput.activate(scopeContext, stepProperties, deactivate, buttonLabel, 'SFC/SelectInput', choices)
