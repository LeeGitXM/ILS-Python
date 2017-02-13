'''
Created on Dec 16, 2015

    action for java SetQueueStep
    sets the chart's current message queue

@author: rforbes
'''

from ils.sfc.gateway.util import getStepProperty, handleUnexpectedGatewayError
from system.ils.sfc.common.Constants import MESSAGE_QUEUE
from ils.sfc.gateway.api import setCurrentMessageQueue, getChartLogger

def activate(scopeContext, stepProperties, state):
    try: 
        chartScope = scopeContext.getChartScope()
        stepScope = scopeContext.getStepScope()
        chartLogger = getChartLogger(chartScope)
        queue = getStepProperty(stepProperties, MESSAGE_QUEUE)
        setCurrentMessageQueue(chartScope, queue)
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in setQueue.py', chartLogger)
    finally:
        return True