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
    
    try:
        chartScope = scopeContext.getChartScope()
        chartLogger = getChartLogger(chartScope)
        stepScope = scopeContext.getStepScope()
        buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL)
        if isEmpty(buttonLabel):
            buttonLabel = 'Select'
        choicesRecipeLocation = getStepProperty(stepProperties, CHOICES_RECIPE_LOCATION) 
        choicesKey = getStepProperty(stepProperties, CHOICES_KEY) 
        choices = s88Get(chartScope, stepScope, choicesKey, choicesRecipeLocation)    
        return commonInput.activate(scopeContext, stepProperties, buttonLabel, 'SFC/SelectInput', choices)
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in selectInput.py', chartLogger)
    finally:
        return True