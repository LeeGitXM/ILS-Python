'''
Created on Dec 16, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties, state):
    '''
    action for java ClearQueueStep
    delete all messages from the current message queue
    '''
    from ils.sfc.gateway.api import getDatabaseName, getChartLogger
    from ils.queue.message import clear
    from ils.sfc.gateway.api import getCurrentMessageQueue
    from ils.sfc.gateway.util import handleUnexpectedGatewayError
    chartScope = scopeContext.getChartScope()
    chartLogger = getChartLogger(chartScope)
    try:
        currentMsgQueue = getCurrentMessageQueue(chartScope)
        database = getDatabaseName(chartScope)
        clear(currentMsgQueue, database)
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in clearQueue.py', chartLogger)
    finally:
        return True