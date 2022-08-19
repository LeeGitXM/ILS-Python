'''
Created on Sep 10, 2014

@author: Pete
'''

import system
log = system.util.getLogger(__name__)
from ils.common.constants import GATEWAY, DESIGNER, CLIENT


def getScope():
    '''
    This can be called in all scopes (designer, client, and gateway) and determines which scope it is running in.
    '''
    
    try:
        # This call throws an error in the gateway
        flags = system.util.getSystemFlags()
    except:
        return GATEWAY

    isDesigner = flags >> 0 & 1
    isClient = flags >> 2 & 1

    if isDesigner:
        return DESIGNER
    
    if isClient:
        return CLIENT

    return None



def getUserLibDir(projectName):
    scope = getScope()
    if scope == GATEWAY:
        from com.inductiveautomation.ignition.gateway import IgnitionGateway
        context = IgnitionGateway.get()
        path = context.getSystemManager().getUserLibDir().getAbsolutePath()
    else:
        payload = {}
        path = system.util.sendRequest(projectName, "getUserLibDir", payload)

    return path
    

def getHistoryProvider():
    return 'XOMhistory'



'''
This set of APIs go all the way to the source (the internal database) and can be used from any scope although it might be faster 
and easier to read the tags 
'''
def getTagProviderFromInternalDatabase(projectName):
    tagProvider = getProductionTagProviderFromInternalDatabase(projectName)
    return tagProvider

def getProductionTagProviderFromInternalDatabase(projectName):
    isolationMode = False
    payload = {"project": projectName, "isolationMode": isolationMode}
    scope = getScope()
    
    if scope == GATEWAY:
        from ils.config.gateway import getTagProviderHandler
        tagProvider = getTagProviderHandler(payload)
    else:
        tagProvider = system.util.sendRequest(projectName, "getTagProvider", payload)
    return tagProvider

def getIsolationTagProviderFromInternalDatabase(projectName):
    isolationMode = True
    payload = {"project": projectName, "isolationMode": isolationMode}
    scope = getScope()

    if scope == GATEWAY:
        from ils.config.gateway import getTagProviderHandler
        tagProvider = getTagProviderHandler(payload)
    else:
        tagProvider = system.util.sendRequest(projectName, "getTagProvider", payload)

    return tagProvider

def getDatabaseFromInternalDatabase(projectName):
    db = getProductionDatabaseFromInternalDatabase(projectName)
    return db
    
def getProductionDatabaseFromInternalDatabase(projectName):
    isolationMode = False
    payload = {"project": projectName, "isolationMode": isolationMode}
    scope = getScope()
    
    if scope == GATEWAY:
        from ils.config.gateway import getDatabaseHandler
        db = getDatabaseHandler(payload)
    else:
        db = system.util.sendRequest(projectName, "getDatabase", payload)
    
    return db

def getIsolationDatabaseFromInternalDatabase(projectName):
    isolationMode = True
    payload = {"project": projectName, "isolationMode": isolationMode}
    scope = getScope()
    
    if scope == GATEWAY:
        from ils.config.gateway import getDatabaseHandler
        db = getDatabaseHandler(payload)
    else:
        db = system.util.sendRequest(projectName, "getDatabase", payload)
        
    return db

def getTimeFactorFromInternalDatabase(projectName):
    db = getProductionTimeFactorFromInternalDatabase(projectName)
    return db
    
def getProductionTimeFactorFromInternalDatabase(projectName):
    isolationMode = False
    payload = {"project": projectName, "isolationMode": isolationMode}
    scope = getScope()
    
    if scope == GATEWAY:
        from ils.config.gateway import getTimeFactorHandler
        db = getTimeFactorHandler(payload)
    else:
        db = system.util.sendRequest(projectName, "getTimeFactor", payload)
    
    return db

def getIsolationTimeFactorFromInternalDatabase(projectName):
    isolationMode = True
    payload = {"project": projectName, "isolationMode": isolationMode}
    scope = getScope()
    
    if scope == GATEWAY:
        from ils.config.gateway import getTimeFactorHandler
        db = getTimeFactorHandler(payload)
    else:
        db = system.util.sendRequest(projectName, "getTimeFactor", payload)
        
    return db

def getDatabaseConnections():
    '''
    Get a list of available data connections using the information in the [System] tag provider.
    This should be available from all scopes in all projects.
    '''
    dbConnections = []
    ds = system.db.getConnections()
    for row in range(ds.rowCount):
        dbName = ds.getValueAt(row, "Name")
        status = ds.getValueAt(row, "Status")
        if status == "Valid":
            dbConnections.append(dbName)

    print "Returning: ", dbConnections
    return dbConnections

def getDefaultDatabase():
    ''' Get the default database for a client '''
    db = system.tag.readBlocking(["[System]Client/System/DefaultDatabase"])[0].value
    print "The default database is: ", db
    return db

def getDefaultTagProvider():
    ''' Get the default database for a client '''
    tagProvider = system.tag.readBlocking(["[System]Client/System/DefaultTagProvider"])[0].value
    print "The default tag provider is: ", tagProvider
    return tagProvider


'''
This set of APIs really shouldn't be used.  If running in a client, then we should use the client version.
If called from an SFC, then we should look at the chart scope dictionary (Remember that a chart is ALWAYS started from a client).
Tag change scripts, this is the one thing that does not belong to a project, should extract the tag provider from the tag path.
'''

def getTagProvider(projectName):
    tagProvider = getProductionTagProvider(projectName)
    return tagProvider

def getProductionTagProvider(projectName):
    isolationMode = False
    payload = {"project": projectName, "isolationMode": isolationMode}
    tagProvider = system.util.sendRequest(projectName, "getTagProvider", payload)
    return tagProvider

def getIsolationTagProvider(projectName):
    isolationMode = True
    payload = {"project": projectName, "isolationMode": isolationMode}
    tagProvider = system.util.sendRequest(projectName, "getTagProvider", payload)
    return tagProvider

def getDatabase(projectName):
    db = getProductionDatabase(projectName)
    return db
    
def getProductionDatabase(projectName):
    isolationMode = False
    payload = {"project": projectName, "isolationMode": isolationMode}
    db = system.util.sendRequest(projectName, "getDatabase", payload)
    return db

def getIsolationDatabase(projectName):
    isolationMode = True
    payload = {"project": projectName, "isolationMode": isolationMode}
    db = system.util.sendRequest(projectName, "getDatabase", payload)
    return db

