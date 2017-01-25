'''
Created on Sep 10, 2014

@author: Pete
'''

import system

# This should be the only place in the project that we hard-code the provider name EMC.
# It would be better to get this from some configurable place.  
# This will generally get called by some top-level entry point and then passed along to anyone 
# that needs it.
def getTagProvider():
    return 'XOM'

def getHistoryProvider():
    return 'XOMhistory'

def getDatabase():
    return 'XOM'

def getIsolationTagProvider():
    return 'XOM_ISOLATION'

def getIsolationDatabase():
    return 'XOM_ISOLATION'

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
