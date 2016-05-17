'''
Created on Dec 17, 2015

@author: rforbes
'''
def activate(scopeContext, stepProperties, deactivate):
    from ils.sfc.gateway.steps import commonInput
    from ils.sfc.gateway.util import getStepProperty
    from ils.sfc.common.util import isEmpty
    from system.ils.sfc.common.Constants import BUTTON_LABEL
    buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL)
    if isEmpty(buttonLabel):
        buttonLabel = 'Input<>'
    from system.ils.sfc.common.Constants import MINIMUM_VALUE, MAXIMUM_VALUE
    minValue = getStepProperty(stepProperties, MINIMUM_VALUE)
    maxValue = getStepProperty(stepProperties, MAXIMUM_VALUE) 
    return commonInput.activate(scopeContext, stepProperties, deactivate, buttonLabel, 'SFC/Input', None, minValue, maxValue)