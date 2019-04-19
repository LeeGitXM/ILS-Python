'''
Created on Dec 16, 2015

@author: rforbes

queues the step's message
'''

from ils.queue.message import insert
from ils.sfc.common.constants import MESSAGE, PRIORITY
from ils.sfc.gateway.api import getProject, getCurrentMessageQueue, getChartLogger, getStepProperty, getDatabaseName, handleUnexpectedGatewayError, getConsoleName
from ils.sfc.recipeData.api import substituteScopeReferences

def activate(scopeContext, stepProperties, state):
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    logger = getChartLogger(chartScope)
    
    try:
        chartScope = scopeContext.getChartScope()
        stepScope = scopeContext.getStepScope()
        chartLogger = getChartLogger(chartScope)
        currentMsgQueue = getCurrentMessageQueue(chartScope)
        project = getProject(chartScope)
        message = getStepProperty(stepProperties, MESSAGE)
        logger.tracef("The untranslated message is <%s>...", message)
        message = substituteScopeReferences(chartScope, stepScope, message)
        logger.tracef("...the translated message is <%s>", message)
        priority = getStepProperty(stepProperties, PRIORITY)  
        database = getDatabaseName(chartScope)
        consoleName = getConsoleName(chartScope, database)
        insert(currentMsgQueue, priority, message, database, project, console=consoleName)
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in queueInsert.py', chartLogger)
    finally:
        return True