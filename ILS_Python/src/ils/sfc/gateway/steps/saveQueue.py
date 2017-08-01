'''
Created on Dec 16, 2015

@author: rforbes
'''

from ils.sfc.gateway.api import getCurrentMessageQueue, getChartLogger
from ils.queue.message import save
from ils.sfc.gateway.api import createFilepath, handleUnexpectedGatewayError, getDatabaseName
    
def activate(scopeContext, stepProperties, state):

    try:
        chartScope = scopeContext.getChartScope()
        chartLogger = getChartLogger(chartScope)
        currentMsgQueue = getCurrentMessageQueue(chartScope)
        database = getDatabaseName(chartScope)
        filepath = createFilepath(chartScope, stepProperties, False)
        save(currentMsgQueue, True, filepath, database)
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in activate.py', chartLogger)
    finally:
        return True