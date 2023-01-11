'''
Created on Dec 20, 2021

@author: ils
'''

import system, sys
from ils.common.error import catchError

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
    log.tracef("In getDatabaseHandler: %s", str(payload))
    project = payload.get("project", None)
    isolationMode = payload.get("isolationMode", None)
    if project == None or isolationMode == None:
        log.errorf("Missing required arguments!")
        return None
    
    db = getDatabase(project, isolationMode)
    return db

def getDatabase(project, isolationMode):
    '''
    This runs in the gateway in response to a message sent from a client.
    '''
    log.tracef("In %s.getDatabase() for %s - %s", __name__, project, str(isolationMode))
    
    context = IgnitionGateway.get()
    handler = ToolkitProjectRecordHandler(context)
    
    if isolationMode:
        db = handler.getToolkitProjectProperty(project, ISOLATION_DATABASE)
    else:
        db = handler.getToolkitProjectProperty(project, PRODUCTION_DATABASE)

    log.tracef("Returning database: %s", db)
    return db

def setDatabaseHandler(payload):
    '''
    This runs in the gateway in response to a message sent from a client.
    '''
    log.infof("In %s.setDatabaseHandler: %s", __name__, str(payload))
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
        txt = catchError("setDatabaseHandler", str(payload))
        log.errorf(txt)
        status = "failure"
    else:
        status = "success"

    log.tracef("Setting database: %s", status)
    return status

def getTagProviderHandler(payload):
    '''
    This runs in the gateway in response to a message sent from a client.
    '''
    log.tracef("In getTagProviderHandler: %s", payload)
    project = payload.get("project", None)
    isolationMode = payload.get("isolationMode", None)
    if project == None or isolationMode == None:
        log.errorf("Missing required arguments!")
        return None
    
    tp = getTagProvider(project, isolationMode)

    return tp

def getTagProvider(project, isolationMode):
    '''
    This runs in the gateway and can be called directly from a tag change script.
    '''
    context = IgnitionGateway.get()
    handler = ToolkitProjectRecordHandler(context)

    if isolationMode:
        tp = handler.getToolkitProjectProperty(project, ISOLATION_TAG_PROVIDER)
    else:
        tp = handler.getToolkitProjectProperty(project, PRODUCTION_TAG_PROVIDER)

    log.tracef("Returning tag provider: %s", tp)
    return tp

def getTagProvidersHandler(payload):
    '''
    This runs in the gateway in response to a message sent from a client.
    '''
    log.tracef("In %s.getTagProviderHandler(): %s", __name__, payload)
    providers = getTagProviders()

    log.tracef("Returning tag providers: %s", str(providers))
    return providers

def setTagProviderHandler(payload):
    '''
    This runs in the gateway in response to a message sent from a client.
    '''
    log.infof("In %s.setTagProviderHandler: %s", __name__, payload)
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
        txt = catchError("setTagProviderHandler", str(payload))
        log.errorf(txt)
        status = "failure"
    else:
        status = "success"
        
    log.tracef("Setting tag provider: %s", status)
    return status


def getTimeFactorHandler(payload):
    '''
    This runs in the gateway in response to a message sent from a client.
    '''
    log.tracef("In getTimeFactorHandler: %s", payload)
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

    log.tracef("Returning time factor: %s", tp)
    return tp


def setTimeFactorHandler(payload):
    '''
    This runs in the gateway in response to a message sent from a client.
    '''
    log.infof("In %s.setTimeFactorHandler: %s", __name__, str(payload))
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
        txt = catchError("setTimeFactorHandler", str(payload))
        log.errorf(txt)
        status = "failure"
    else:
        status = "success"
        
    log.tracef("Setting tag provider: %s", status)
    return status

def getUserLibDirHandler(payload):
    '''
    This runs in the gateway in response to a message sent from a client.
    '''
    log.tracef("In getUserLibDirHandler: %s", str(payload))
    
    context = IgnitionGateway.get()
    path = context.getSystemManager().getUserLibDir().getAbsolutePath()
    log.tracef("Returning UserLibDir: %s", path)
    
    return path

def getTagProviders():
    context = IgnitionGateway.get()
    tagProviderNames = context.getTagManager().getTagProviderNames()
#    for provider in 
    print "found ", tagProviderNames
        #tagProviderNames.append(provider.getInformation().getName())
    return tagProviderNames


def getHistoryProvider():
    return 'XOMhistory'
