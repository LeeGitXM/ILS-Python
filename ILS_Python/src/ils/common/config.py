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

def getDatabase():
    return 'XOM'

# These should be used only by a client.  They totally respect the isolation mode settings that are in force for the client.
def getTagProviderClient():
    tagProvider=system.tag.read("[Client]Tag Provider").value
    return tagProvider

def getDatabaseClient():
    database=system.tag.read("[Client]Database").value
    return database
