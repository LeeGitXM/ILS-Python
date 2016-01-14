'''
Created on Dec 16, 2015

@author: rforbes
'''

def activate(scopeContext, step):
    '''
    action for java SetQueueStep
    sets the chart's current message queue
    '''
    from ils.sfc.gateway.util import getStepProperty, handleUnexpectedGatewayError
    from system.ils.sfc.common.Constants import MESSAGE_QUEUE
    from ils.sfc.gateway.api import setCurrentMessageQueue, getChartLogger
    
    try: 
        chartScope = scopeContext.getChartScope()
        chartLogger = getChartLogger(chartScope)
        stepProperties = step.getProperties();
        queue = getStepProperty(stepProperties, MESSAGE_QUEUE)
        setCurrentMessageQueue(chartScope, queue)
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in setQueue.py', chartLogger)