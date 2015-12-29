'''
Created on Dec 17, 2015

@author: rforbes
'''
def activate(scopeContext, stepProperties):
    from ils.sfc.gateway.steps import commonInput
    from ils.sfc.gateway.util import getStepProperty
    from system.ils.sfc.common.Constants import MINIMUM_VALUE, MAXIMUM_VALUE
    minValue = getStepProperty(stepProperties, MINIMUM_VALUE)
    maxValue = getStepProperty(stepProperties, MAXIMUM_VALUE) 
    commonInput.activate(scopeContext, stepProperties, 'SFC/Input', '', minValue, maxValue)