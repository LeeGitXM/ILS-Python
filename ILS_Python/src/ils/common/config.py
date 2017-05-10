'''
Created on Sep 10, 2014

@author: Pete
'''

import system
from system.ils.sfc import getDatabaseName, getProviderName

def getHistoryProvider():
    return 'XOMhistory'

def getTagProvider():
    return getProviderName(False)

def getDatabase():
    return getDatabaseName(False)

def getIsolationTagProvider():
    return getProviderName(True)

def getIsolationDatabase():
    return getDatabaseName(True)

# These should be used only by a client.  They totally respect the isolation mode settings that are in force for the client.
def getHistoryTagProviderClient():
    tagProvider=system.tag.read("[Client]History Tag Provider").value
    return tagProvider

# These should be used only by a client.  They totally respect the isolation mode settings that are in force for the client.
def getTagProviderClient():
    tagProvider=system.tag.read("[Client]Tag Provider").value
    return tagProvider

def getDatabaseClient():
    database=system.tag.read("[Client]Database").value
    return database

def getIsolationModeClient():
    isolationMode=system.tag.read("[Client]Isolation Mode").value
    return isolationMode
