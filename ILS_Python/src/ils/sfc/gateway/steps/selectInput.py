'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):
    from ils.sfc.gateway.util import getStepProperty
    from ils.sfc.gateway.api import s88Get
    from system.ils.sfc.common.Constants import CHOICES_RECIPE_LOCATION, CHOICES_KEY
    from ils.sfc.gateway.steps import commonInput
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    choicesRecipeLocation = getStepProperty(stepProperties, CHOICES_RECIPE_LOCATION) 
    choicesKey = getStepProperty(stepProperties, CHOICES_KEY) 
    choices = s88Get(chartScope, stepScope, choicesKey, choicesRecipeLocation)    
    commonInput.activate(scopeContext, stepProperties, 'SFC/SelectInput', choices)