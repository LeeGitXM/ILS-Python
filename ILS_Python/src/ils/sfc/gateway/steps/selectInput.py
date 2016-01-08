'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):
    from ils.sfc.gateway.util import getStepProperty, handleUnexpectedGatewayError
    from ils.sfc.gateway.api import s88Get, getChartLogger
    from system.ils.sfc.common.Constants import CHOICES_RECIPE_LOCATION, CHOICES_KEY
    from ils.sfc.gateway.steps import commonInput
    
    try:
        chartScope = scopeContext.getChartScope()
        chartLogger = getChartLogger(chartScope)
        stepScope = scopeContext.getStepScope()
        choicesRecipeLocation = getStepProperty(stepProperties, CHOICES_RECIPE_LOCATION) 
        choicesKey = getStepProperty(stepProperties, CHOICES_KEY) 
        choices = s88Get(chartScope, stepScope, choicesKey, choicesRecipeLocation)    
        commonInput.activate(scopeContext, stepProperties, buttonLabel, 'SFC/SelectInput', choices)
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in selectInput.py', chartLogger)
