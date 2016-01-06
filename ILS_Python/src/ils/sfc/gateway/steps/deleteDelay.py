'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):
    import system.db
    from ils.sfc.gateway.api import getDatabaseName, getProject
    from ils.sfc.gateway.util import deleteAndSendClose
    chartScope = scopeContext.getChartScope()
    # chartLogger = getChartLogger(chartScope)
    
    # window common properties:
    database = getDatabaseName(chartScope)
    results = system.db.runQuery('select windowId from SfcBusyNotification', database)
    for row in results:
        windowId = row[0]
        system.db.runUpdateQuery("delete from SfcBusyNotification where windowId = '%s'" % (windowId), database)    
        project = getProject(chartScope)
        deleteAndSendClose(project, windowId, database)
