'''
Created on Dec 16, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):
    from ils.sfc.gateway.api import getCurrentMessageQueue
    from ils.queue.message import save
    from ils.sfc.gateway.util import createFilepath
    from ils.sfc.gateway.api import getDatabaseName
    chartScope = scopeContext.getChartScope()
    currentMsgQueue = getCurrentMessageQueue(chartScope)
    database = getDatabaseName(chartScope)
    filepath = createFilepath(chartScope, stepProperties, False)
    save(currentMsgQueue, True, filepath, database)
