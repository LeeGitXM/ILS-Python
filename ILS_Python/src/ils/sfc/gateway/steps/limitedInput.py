'''
Created on Dec 17, 2015

@author: rforbes
'''
def activate(scopeContext, step):
    from ils.sfc.gateway.steps import commonInput
    from ils.sfc.gateway.util import getStepProperty
    from ils.sfc.common.util import isEmpty
    from system.ils.sfc.common.Constants import BUTTON_LABEL
    stepProperties = step.getProperties();
    buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL)
    if isEmpty(buttonLabel):
        buttonLabel = 'Input<>'
    from system.ils.sfc.common.Constants import MINIMUM_VALUE, MAXIMUM_VALUE
    minValue = getStepProperty(stepProperties, MINIMUM_VALUE)
    maxValue = getStepProperty(stepProperties, MAXIMUM_VALUE) 
    commonInput.activate(scopeContext, step, buttonLabel, 'SFC/Input', '', minValue, maxValue)