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
        logger = getChartLogger(chartScope)
        currentMsgQueue = getCurrentMessageQueue(chartScope)
        database = getDatabaseName(chartScope)
        path, filename = createFilepath(chartScope, stepProperties, False)
        filePath = path + "/" + filename
        logger.infof("Saving message queue <%s> to <%s>", currentMsgQueue, filePath)
        save(currentMsgQueue, True, filePath, database)
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in activate.py', logger)
    finally:
        return True