'''
Created on Aug 2, 2022

@author: ils
'''

import system
log = system.util.getLogger(__name__)

'''
These should be used only by a client.  They respect the isolation mode settings that are in force for the client.
'''
def getHistoryTagProvider():
    tagProvider=readTag("[Client]History Tag Provider").value
    return tagProvider

def getDatabase():
    database=readTag("[Client]Database").value
    return database

def getDatabaseConnections():
    from ils.config.common import getDatabaseConnections as getDatabaseConnectionsCommon
    dbConnections = getDatabaseConnectionsCommon()
    return dbConnections

def getIsolationMode():
    isolationMode=readTag("[Client]Isolation Mode").value
    return isolationMode

def getTagProvider():
    tagProvider=readTag("[Client]Tag Provider").value
    return tagProvider

def getTagProviders():
    print "In %s.getTagProviders()" % (__name__)
    projectName = system.util.getProjectName()
    payload = {}
    print "Sending request..."
    tagProviderNames = system.util.sendRequest(projectName, "getTagProviders", payload)
    log.infof("   Tag Providers: %s", str(tagProviderNames))
    return tagProviderNames

def getTimeFactor():
    timeFactor=readTag("[Client]Time Factor").value
    return timeFactor

def isolationModeChangeHandler(qv):
    '''
    This is called from the tag change handler on a client tag.
    '''
    log.infof("In %s.isolationModeChangeHandler(), new isolation mode: %s", __name__, str(qv))
    isolationMode = qv.value
    _isolationModeChangeHandler(isolationMode)
    
def _isolationModeChangeHandler(isolationMode):
    log.infof("In %s._isolationModeChangeHandler(), new isolation mode: %s", __name__, str(isolationMode))
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


def readTag(tagPath):
    '''
    This reads a single tag using a blocking read and returns a single qualified value.
    This just saves the caller the task of packing and unpacking the results when migrating
    to Ignition 8. 
    '''
    qvs = system.tag.readBlocking([tagPath])
    qv = qvs[0]
    return qv
