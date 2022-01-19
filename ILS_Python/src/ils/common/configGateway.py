'''
Created on Dec 20, 2021

@author: ils
'''

import system

'''
TOOLKIT_PROPERTY_BE_DATABASE         = "BatchExpertDatabase"; //Database for BatchExpert
TOOLKIT_PROPERTY_PYSFC_DATABASE      = "PySfcDatabase";       //Database for PySfc
TOOLKIT_PROPERTY_BE_DBMS             = "BatchExpertDBMS";     //Database for BatchExpert
TOOLKIT_PROPERTY_PYSFC_DBMS          = "PySfcDBMS";          //Database for PySfc
TOOLKIT_PROPERTY_SECONDARY_DATABASE  = "SecondaryDatabase";  // Alternate database
TOOLKIT_PROPERTY_DBMS                = "DBMS";           // Production database DBMS
TOOLKIT_PROPERTY_ISOLATION_DBMS      = "SecondaryDBMS";      // Database DBMS when in isolation
TOOLKIT_PROPERTY_SECONDARY_DBMS      = "SecondaryDBMS";      // Alternate DBMS
TOOLKIT_PROPERTY_SECONDARY_PROVIDER  = "SecondaryProvider";  // Alternate tag provider
TOOLKIT_PROPERTY_ISOLATION_TIME      = "SecondaryTimeFactor";// Time speedup when in isolation
'''

log = system.util.getLogger(__name__)
from com.inductiveautomation.ignition.gateway import IgnitionGateway
from com.ils.common.persistence import ToolkitProjectRecordHandler

PRODUCTION_DATABASE = "Database"
ISOLATION_DATABASE = "SecondaryDatabase"
PRODUCTION_TAG_PROVIDER = "Provider"
ISOLATION_TAG_PROVIDER = "SecondaryProvider"
PRODUCTION_TIME_FACTOR = "TimeFactor"
ISOLATION_TIME_FACTOR = "SecondaryTimeFactor"

def getDatabaseHandler(payload):
    '''
    This runs in the gateway in response to a message sent from a client.
    '''
    log.infof("In getDatabaseHandler: %s", str(payload))
    project = payload.get("project", None)
    isolationMode = payload.get("isolationMode", None)
    if project == None or isolationMode == None:
        log.errorf("Missing required arguments!")
        return None
    
    context = IgnitionGateway.get()
    handler = ToolkitProjectRecordHandler(context)
    
    if isolationMode:
        db = handler.getToolkitProjectProperty(project, ISOLATION_DATABASE)
    else:
        db = handler.getToolkitProjectProperty(project, PRODUCTION_DATABASE)

    log.infof("Returning database: %s", db)
    
    return db

def setDatabaseHandler(payload):
    '''
    This runs in the gateway in response to a message sent from a client.
    '''
    log.infof("In setDatabaseHandler: %s", str(payload))
    project = payload.get("project", None)
    isolationMode = payload.get("isolationMode", None)
    val = payload.get("val", None)
    if project == None or isolationMode == None or val == None:
        log.errorf("Missing required arguments!")
        return None
    
    context = IgnitionGateway.get()
    handler = ToolkitProjectRecordHandler(context)
    
    try:
        if isolationMode:
            handler.setToolkitProjectProperty(project, ISOLATION_DATABASE, val)
        else:
            handler.setToolkitProjectProperty(project, PRODUCTION_DATABASE, val)
    except:
        print "Caught an exception"
        status = "failure"
    else:
        status = "success"

    log.infof("Setting database: %s", status)
    return status

def getTagProviderHandler(payload):
    '''
    This runs in the gateway in response to a message sent from a client.
    '''
    log.infof("In getTagProviderHandler: %s", payload)
    project = payload.get("project", None)
    isolationMode = payload.get("isolationMode", None)
    if project == None or isolationMode == None:
        log.errorf("Missing required arguments!")
        return None
    
    context = IgnitionGateway.get()
    handler = ToolkitProjectRecordHandler(context)

    if isolationMode:
        tp = handler.getToolkitProjectProperty(project, ISOLATION_TAG_PROVIDER)
    else:
        tp = handler.getToolkitProjectProperty(project, PRODUCTION_TAG_PROVIDER)

    log.infof("Returning tag provider: %s", tp)
    return tp

def setTagProviderHandler(payload):
    '''
    This runs in the gateway in response to a message sent from a client.
    '''
    log.infof("In setTagProviderHandler: %s", payload)
    project = payload.get("project", None)
    isolationMode = payload.get("isolationMode", None)
    val = payload.get("val", None)
    if project == None or isolationMode == None or val == None:
        log.errorf("Missing required arguments!")
        return None
    
    context = IgnitionGateway.get()
    handler = ToolkitProjectRecordHandler(context)

    try:
        if isolationMode:
            handler.setToolkitProjectProperty(project, ISOLATION_TAG_PROVIDER, val)
        else:
            handler.setToolkitProjectProperty(project, PRODUCTION_TAG_PROVIDER, val)
    except:
        print "Caught an exception"
        status = "failure"
    else:
        status = "success"
        
    log.infof("Setting tag provider: %s", status)
    return status


def getTimeFactorHandler(payload):
    '''
    This runs in the gateway in response to a message sent from a client.
    '''
    log.infof("In getTimeFactorHandler: %s", payload)
    project = payload.get("project", None)
    isolationMode = payload.get("isolationMode", None)
    if project == None or isolationMode == None:
        log.errorf("Missing required arguments!")
        return None
    
    context = IgnitionGateway.get()
    handler = ToolkitProjectRecordHandler(context)

    if isolationMode:
        tp = handler.getToolkitProjectProperty(project, ISOLATION_TIME_FACTOR)
    else:
        tp = handler.getToolkitProjectProperty(project, PRODUCTION_TIME_FACTOR)

    log.infof("Returning time factor: %s", tp)
    return tp


def setTimeFactorHandler(payload):
    '''
    This runs in the gateway in response to a message sent from a client.
    '''
    log.infof("In setTimeFactorHandler: %s", payload)
    project = payload.get("project", None)
    isolationMode = payload.get("isolationMode", None)
    val = payload.get("val", None)
    if project == None or isolationMode == None or val == None:
        log.errorf("Missing required arguments!")
        return None
    
    context = IgnitionGateway.get()
    handler = ToolkitProjectRecordHandler(context)

    try:
        if isolationMode:
            handler.setToolkitProjectProperty(project, ISOLATION_TIME_FACTOR, val)
        else:
            handler.setToolkitProjectProperty(project, PRODUCTION_TIME_FACTOR, val)
    except:
        print "Caught an exception"
        status = "failure"
    else:
        status = "success"
        
    log.infof("Setting tag provider: %s", status)
    return status


def getTagProviders():
    from com.inductiveautomation.ignition.gateway import SRContext
    context = SRContext.get()
    tagProviderNames = []
    for provider in context.getTagManager().getTagProviders():
        tagProviderNames.append(provider.getInformation().getName())
    return tagProviderNames

'''
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
''' 

def getHistoryProvider():
    return 'XOMhistory'


'''
def getTagProvider(project):
    ToolkitProjectRecordHandler.getToolkitProjectProperty(project, )
    return "foo"

def getTagProviderX():
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
'''

def readTag(tagPath):
    '''
    This reads a single tag using a blocking read and returns a single qualified value.
    This just saves the caller the task of packing and unpacking the results when migrating
    to Ignition 8. 
    '''
    qvs = system.tag.readBlocking([tagPath])
    qv = qvs[0]
    return qv
