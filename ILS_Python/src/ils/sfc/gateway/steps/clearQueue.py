'''
Created on Dec 16, 2015

@author: rforbes

delete all messages from the current message queue
'''
from ils.sfc.gateway.api import getDatabaseName, getChartLogger
from ils.queue.message import clear
from ils.sfc.gateway.api import getCurrentMessageQueue, handleUnexpectedGatewayError

def activate(scopeContext, stepProperties, state):
    chartScope = scopeContext.getChartScope()
    chartLogger = getChartLogger(chartScope)
    try:
        currentMsgQueue = getCurrentMessageQueue(chartScope)
        database = getDatabaseName(chartScope)
        clear(currentMsgQueue, database)
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in clearQueue.py', chartLogger)
    finally:
        return True