'''
Created on Dec 17, 2015

@author: rforbes
'''
def activate(scopeContext, step):
    '''
    Action for java InputStep
    Get an response from the user; block until a
    response is received, put response in chart properties
    '''
    from ils.sfc.common.util import isEmpty
    from ils.sfc.gateway.steps import commonInput
    from ils.sfc.gateway.util import getStepProperty
    from system.ils.sfc.common.Constants import BUTTON_LABEL
    stepProperties = step.getProperties();
    buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL)
    if isEmpty(buttonLabel):
        buttonLabel = 'Input'
    commonInput.activate(scopeContext, step, buttonLabel, 'SFC/Input')