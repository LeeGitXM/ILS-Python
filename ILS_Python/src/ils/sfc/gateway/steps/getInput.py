'''
Created on Dec 17, 2015

@author: rforbes
'''
def activate(scopeContext, stepProperties):
    '''
    Action for java InputStep
    Get an response from the user; block until a
    response is received, put response in chart properties
    '''
    from ils.sfc.gateway.steps import commonInput
    commonInput.activate(scopeContext, stepProperties, 'SFC/Input')