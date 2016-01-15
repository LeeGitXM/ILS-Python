'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, step): 
    from ils.sfc.gateway.api import getChartLogger    
    from ils.sfc.gateway.util import handleUnexpectedGatewayError
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    stepProperties = step.getProperties();
    chartLogger = getChartLogger(chartScope)
    try:
        pass
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in confirmControllers.py', chartLogger)