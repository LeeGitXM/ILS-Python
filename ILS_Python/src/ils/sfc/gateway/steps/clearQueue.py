'''
Created on Dec 16, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):
    '''
    action for java ClearQueueStep
    delete all messages from the current message queue
    '''
    from ils.sfc.gateway.api import getDatabaseName
    from ils.queue.message import clear
    from ils.sfc.gateway.api import getCurrentMessageQueue
    chartScope = scopeContext.getChartScope()
    currentMsgQueue = getCurrentMessageQueue(chartScope)
    database = getDatabaseName(chartScope)
    clear(currentMsgQueue, database)
