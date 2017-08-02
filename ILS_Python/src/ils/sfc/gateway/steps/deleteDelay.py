'''
Created on Dec 17, 2015

@author: rforbes

Ordinarily window closing logic would be in a finally block, but since the whole business
of this block is to close windows, there is no finally block... 
'''

import system
from ils.sfc.gateway.api import getDatabaseName, getProject, getChartLogger, handleUnexpectedGatewayError, deleteAndSendClose
from ils.sfc.common.constants import NAME
    
def activate(scopeContext, stepProperties, state):
   
    try:
        chartScope = scopeContext.getChartScope()
        stepScope = scopeContext.getStepScope()
        stepName=stepScope.get(NAME, "Unknown")
        
        logger = getChartLogger(chartScope)
        logger.tracef("In %s.activate() initializing the step %s...", __name__, stepName)
        
        # window common properties:
        database = getDatabaseName(chartScope)
        results = system.db.runQuery('select windowId from SfcBusyNotification', database)
        for row in results:
            windowId = row[0]
            system.db.runUpdateQuery("delete from SfcBusyNotification where windowId = '%s'" % (windowId), database)    
            project = getProject(chartScope)
            deleteAndSendClose(project, windowId, database)
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in deleteDelay.py', logger)
    finally:
        return True