'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties, state):
    import system.db
    from ils.sfc.gateway.api import getDatabaseName, getProject, getChartLogger
    from ils.sfc.gateway.util import deleteAndSendClose, handleUnexpectedGatewayError
 
# NOTE: ordinarily window closing logic would be in a finally block, but since the whole business
# of this block is to close windows, there is no finally block...   
    try:
        chartScope = scopeContext.getChartScope()
        chartLogger = getChartLogger(chartScope)
        # window common properties:
        database = getDatabaseName(chartScope)
        results = system.db.runQuery('select windowId from SfcBusyNotification', database)
        for row in results:
            windowId = row[0]
            system.db.runUpdateQuery("delete from SfcBusyNotification where windowId = '%s'" % (windowId), database)    
            project = getProject(chartScope)
            deleteAndSendClose(project, windowId, database)
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in deleteDelay.py', chartLogger)
    finally:
        return True