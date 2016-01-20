'''
Created on Dec 16, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties, deactivate):
    '''
    Action for java YesNoStep
    Get a yes/no response from the user; block until a
    response is received, put response in chart properties
    '''
    from ils.sfc.common.util import isEmpty
    from ils.sfc.gateway.steps import commonInput
    from ils.sfc.gateway.util import getStepProperty
    from ils.sfc.gateway.api import s88Set
    from system.ils.sfc.common.Constants import BUTTON_LABEL, RECIPE_LOCATION, KEY
    from ils.sfc.common.constants import WAITING_FOR_REPLY
    print "In yesNo.activate()..."
    
    stepScope = scopeContext.getStepScope()
    chartScope = scopeContext.getChartScope()
    
    waitingForReply = stepScope.get(WAITING_FOR_REPLY, False);    
    if not waitingForReply:
        print "*** Initialize the recipe data ****"
        recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION) 
        key = getStepProperty(stepProperties, KEY) 
        s88Set(chartScope, stepScope, key, "??????", recipeLocation)
        
    buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL)
    if isEmpty(buttonLabel):
        buttonLabel = 'Y/N'
    return commonInput.activate(scopeContext, stepProperties, deactivate, buttonLabel, 'SFC/YesNo')