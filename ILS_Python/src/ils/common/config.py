'''
Created on Sep 10, 2014

@author: Pete
'''

import system
import system.ils.blt.diagram as scriptingInterface

def getHistoryProvider():
    return 'XOMhistory'

def getTagProvider():
    #return 'XOM'
    return scriptingInterface.getProductionTagProvider()

def getDatabase():
    #return 'XOM'
    return scriptingInterface.getProductionDatabase()

def getIsolationTagProvider():
    #return 'XOM_ISOLATION'
    return scriptingInterface.getIsolationTagProvider()

def getIsolationDatabase():
    #return 'XOM_ISOLATION'
    return scriptingInterface.getIsolationDatabase()

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
