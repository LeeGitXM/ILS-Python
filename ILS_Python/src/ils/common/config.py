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

def isolationModeChangeHandler(newValue):
    '''
    This is called from the tag change handler on a a client tag.
    '''
    isolationMode = newValue.value
    log.infof("In %s.isolationModeChangeHandler(), new isolation mode: %s", __name__, str(isolationMode))
    projectName = system.util.getProjectName()

    payload = {"project": projectName, "isolationMode": isolationMode}
    log.infof("Payload: %s", payload)
    
    tagProvider = system.util.sendRequest(projectName, "getTagProvider", payload)
    log.infof("   Tag Provider: %s", tagProvider)
    
    timeFactor = system.util.sendRequest(projectName, "getTimeFactor", payload)
    log.infof("   Time Factor: %s", timeFactor)

    database = system.util.sendRequest(projectName, "getDatabase", payload)
    log.infof("   Database: %s", database)
    
    
    system.tag.writeBlocking(['[Client]Tag Provider', '[Client]Time Factor', '[Client]Database'], [tagProvider, timeFactor, database])


def getUserLibDir():
    scope = getScope()
    if scope == GATEWAY:
        from com.inductiveautomation.ignition.gateway import IgnitionGateway
        context = IgnitionGateway.get()
        path = context.getSystemManager().getUserLibDir().getAbsolutePath()
    else:
        path = "UNKNOWN"
        log.warnf("The User Lib Dir <%s> only exists on the gateway!", path)
    
    print "The UserLib path is: ", path
    return path
    

def getHistoryProvider():
    return 'XOMhistory'


def readTag(tagPath):
    '''
    This reads a single tag using a blocking read and returns a single qualified value.
    This just saves the caller the task of packing and unpacking the results when migrating
    to Ignition 8. 
    '''
    qvs = system.tag.readBlocking([tagPath])
    qv = qvs[0]
    return qv

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
    db = getProductionDatabase()
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

'''
These should be used only by a client.  They respect the isolation mode settings that are in force for the client.
'''
def getHistoryTagProviderClient():
    tagProvider=readTag("[Client]History Tag Provider").value
    return tagProvider

def getTagProviderClient():
    tagProvider=readTag("[Client]Tag Provider").value
    return tagProvider

def getTimeFactorClient():
    timeFactor=readTag("[Client]Time Factor").value
    return timeFactor

def getDatabaseClient():
    database=readTag("[Client]Database").value
    return database

def getIsolationModeClient():
    isolationMode=readTag("[Client]Isolation Mode").value
    return isolationMode

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
        from ils.common.configGateway import getTagProviderHandler
        tagProvider = getTagProviderHandler(payload)
    else:
        tagProvider = system.util.sendRequest(projectName, "getTagProvider", payload)
    return tagProvider

def getIsolationTagProviderFromInternalDatabase(projectName):
    isolationMode = True
    payload = {"project": projectName, "isolationMode": isolationMode}
    scope = getScope()

    if scope == GATEWAY:
        from ils.common.configGateway import getTagProviderHandler
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
        from ils.common.configGateway import getDatabaseHandler
        db = getDatabaseHandler(payload)
    else:
        db = system.util.sendRequest(projectName, "getDatabase", payload)
    
    return db

def getIsolationDatabaseFromInternalDatabase(projectName):
    isolationMode = True
    payload = {"project": projectName, "isolationMode": isolationMode}
    scope = getScope()
    
    if scope == GATEWAY:
        from ils.common.configGateway import getDatabaseHandler
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
        from ils.common.configGateway import getTimeFactorHandler
        db = getTimeFactorHandler(payload)
    else:
        db = system.util.sendRequest(projectName, "getTimeFactor", payload)
    
    return db

def getIsolationTimeFactorFromInternalDatabase(projectName):
    isolationMode = True
    payload = {"project": projectName, "isolationMode": isolationMode}
    scope = getScope()
    
    if scope == GATEWAY:
        from ils.common.configGateway import getTimeFactorHandler
        db = getTimeFactorHandler(payload)
    else:
        db = system.util.sendRequest(projectName, "getTimeFactor", payload)
        
    return db