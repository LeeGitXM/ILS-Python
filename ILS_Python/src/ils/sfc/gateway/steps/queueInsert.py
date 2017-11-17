'''
Created on Dec 16, 2015

@author: rforbes

queues the step's message
'''

from ils.queue.message import insert
from ils.sfc.common.constants import MESSAGE, PRIORITY
from ils.sfc.gateway.api import getCurrentMessageQueue, getChartLogger, getStepProperty, getDatabaseName, handleUnexpectedGatewayError
from ils.sfc.recipeData.api import substituteScopeReferences

def activate(scopeContext, stepProperties, state):

    try:
        chartScope = scopeContext.getChartScope()
        stepScope = scopeContext.getStepScope()
        chartLogger = getChartLogger(chartScope)
        currentMsgQueue = getCurrentMessageQueue(chartScope)
        message = getStepProperty(stepProperties, MESSAGE)
        message = substituteScopeReferences(chartScope, stepScope, message)
        priority = getStepProperty(stepProperties, PRIORITY)  
        database = getDatabaseName(chartScope)
        insert(currentMsgQueue, priority, message, database)    
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in queueInsert.py', chartLogger)
    finally:
        return True