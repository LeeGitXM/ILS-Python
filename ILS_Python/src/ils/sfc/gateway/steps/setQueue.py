'''
Created on Dec 16, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):
    '''
    action for java SetQueueStep
    sets the chart's current message queue
    '''
    from ils.sfc.gateway.util import getStepProperty
    from system.ils.sfc.common.Constants import MESSAGE_QUEUE
    from ils.sfc.gateway.api import setCurrentMessageQueue
    chartScope = scopeContext.getChartScope()
    queue = getStepProperty(stepProperties, MESSAGE_QUEUE)
    setCurrentMessageQueue(chartScope, queue)