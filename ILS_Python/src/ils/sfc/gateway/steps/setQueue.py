'''
Created on Dec 16, 2015

    action for java SetQueueStep
    sets the chart's current message queue

@author: rforbes
'''

from ils.sfc.common.constants import MESSAGE_QUEUE
from ils.sfc.gateway.api import setCurrentMessageQueue, getChartLogger, handleUnexpectedGatewayError, getStepProperty

def activate(scopeContext, stepProperties, state):
    try: 
        chartScope = scopeContext.getChartScope()
        stepScope = scopeContext.getStepScope()
        chartLogger = getChartLogger(chartScope)
        queue = getStepProperty(stepProperties, MESSAGE_QUEUE)
        setCurrentMessageQueue(chartScope, queue)
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in setQueue.py', chartLogger)
    finally:
        return True