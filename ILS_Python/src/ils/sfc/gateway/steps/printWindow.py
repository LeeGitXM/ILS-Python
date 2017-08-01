'''
Created on Dec 17, 2015

@author: rforbes
'''

from ils.sfc.gateway.api import getProject, getChartLogger, handleUnexpectedGatewayError, transferStepPropertiesToMessage, sendMessageToClient

def activate(scopeContext, stepProperties, state):   
    
    try:
        chartScope = scopeContext.getChartScope()
        chartLogger = getChartLogger(chartScope)
        payload = dict()
        transferStepPropertiesToMessage(stepProperties, payload)
        sendMessageToClient(chartScope, 'sfcPrintWindow', payload)
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in printWindow.py', chartLogger)
    finally:
        return True