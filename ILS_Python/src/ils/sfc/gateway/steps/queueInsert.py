'''
Created on Dec 16, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):
    '''
    action for java QueueMessageStep
    queues the step's message
    '''
    from ils.sfc.gateway.util import getStepProperty
    from ils.sfc.gateway.api import getDatabaseName
    from ils.queue.message import insert
    from system.ils.sfc.common.Constants import MESSAGE, PRIORITY
    from ils.sfc.gateway.api import getCurrentMessageQueue
    from ils.sfc.gateway.recipe import substituteScopeReferences

    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    currentMsgQueue = getCurrentMessageQueue(chartScope)
    message = getStepProperty(stepProperties, MESSAGE)  
    message = substituteScopeReferences(chartScope, stepScope, message)
    priority = getStepProperty(stepProperties, PRIORITY)  
    database = getDatabaseName(chartScope)
    insert(currentMsgQueue, priority, message, database) 
