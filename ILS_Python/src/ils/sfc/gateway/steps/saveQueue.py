'''
Created on Dec 16, 2015

@author: rforbes
'''

def activate(scopeContext, step):
    from ils.sfc.gateway.api import getCurrentMessageQueue, getChartLogger
    from ils.queue.message import save
    from ils.sfc.gateway.util import createFilepath, handleUnexpectedGatewayError
    from ils.sfc.gateway.api import getDatabaseName
    
    try:
        chartScope = scopeContext.getChartScope()
        chartLogger = getChartLogger(chartScope)
        stepProperties = step.getProperties();
        currentMsgQueue = getCurrentMessageQueue(chartScope)
        database = getDatabaseName(chartScope)
        filepath = createFilepath(chartScope, stepProperties, False)
        save(currentMsgQueue, True, filepath, database)
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in activate.py', chartLogger)
