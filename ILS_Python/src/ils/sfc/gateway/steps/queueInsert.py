'''
Created on Dec 16, 2015

@author: rforbes
'''


def activate(scopeContext, stepProperties, state):
    '''
    action for java QueueMessageStep
    queues the step's message
    '''
    from ils.sfc.gateway.util import getStepProperty, handleUnexpectedGatewayError
    from ils.sfc.gateway.api import getDatabaseName
    from ils.queue.message import insert
    from system.ils.sfc.common.Constants import MESSAGE, PRIORITY
    from ils.sfc.gateway.api import getCurrentMessageQueue, getChartLogger
    from ils.sfc.gateway.recipe import substituteScopeReferences

    try:
        chartScope = scopeContext.getChartScope()
        stepScope = scopeContext.getStepScope()
        chartLogger = getChartLogger(chartScope)
        currentMsgQueue = getCurrentMessageQueue(chartScope)
        message = getStepProperty(stepProperties, MESSAGE)
        print "Raw: ", message
        message = substituteScopeReferences(chartScope, stepScope, message)
        print "Local substitutions: ", message

        print "Escaped: ", message
        priority = getStepProperty(stepProperties, PRIORITY)  
        database = getDatabaseName(chartScope)
        insert(currentMsgQueue, priority, message, database)    
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in queueInsert.py', chartLogger)
    finally:
        return True