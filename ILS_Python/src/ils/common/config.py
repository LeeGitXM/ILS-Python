'''
Created on Sep 10, 2014

@author: Pete
'''

import system
from ils.common.constants import GATEWAY, DESIGNER, CLIENT

def isolationModeChangeHandler(currentValue):
    if currentValue.value:
        provider = getIsolationTagProvider()
        database = getIsolationDatabase()
    else:
        provider = getProductionTagProvider()
        database = getProductionDatabase()
        
    system.tag.write('[Client]Tag Provider', provider)
    system.tag.write('[Client]Database', database)

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

def getUserLibDir():
    scope = getScope()
    if scope == GATEWAY:
        from com.inductiveautomation.ignition.gateway import IgnitionGateway
        context = IgnitionGateway.get()
        path = context.getSystemManager().getUserLibDir().getAbsolutePath()
    else:
        path = "UNKNOWN"
    
    print "The UserLib path is: ", path
    return path
    

def getHistoryProvider():
    return 'XOMhistory'

def getTagProvider():
    tp = getProductionTagProvider()
    return tp
    #return scriptingInterface.getProductionTagProvider()

def getProductionTagProvider():
    return 'XOM'
    #return scriptingInterface.getProductionTagProvider()

def getDatabase():
    db = getProductionDatabase()
    return db
    #return scriptingInterface.getProductionDatabase()
    
def getProductionDatabase():
    return 'XOM_Dev'
    #return scriptingInterface.getProductionDatabase()

def getIsolationTagProvider():
    return 'XOM_ISOLATION'
    #return scriptingInterface.getIsolationTagProvider()

def getIsolationDatabase():
    return 'XOM_ISOLATION'
    #return scriptingInterface.getIsolationDatabase()

# These should be used only by a client.  They totally respect the isolation mode settings that are in force for the client.
def getHistoryTagProviderClient():
    tagProvider=readTag("[Client]History Tag Provider").value
    return tagProvider

# These should be used only by a client.  They totally respect the isolation mode settings that are in force for the client.
def getTagProviderClient():
    tagProvider=readTag("[Client]Tag Provider").value
    return tagProvider

def getDatabaseClient():
    database=readTag("[Client]Database").value
    return database

def getIsolationModeClient():
    isolationMode=readTag("[Client]Isolation Mode").value
    return isolationMode

def readTag(tagPath):
    '''
    This reads a single tag using a blocking read and returns a single qualified value.
    This just saves the caller the task of packing and unpacking the results when migrating
    to Ignition 8. 
    '''
    qvs = system.tag.readBlocking([tagPath])
    qv = qvs[0]
    return qv
