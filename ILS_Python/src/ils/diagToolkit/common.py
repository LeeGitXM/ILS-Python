'''
Created on Sep 19, 2014

@author: Pete
'''

import system

def fetchApplicationId(applicationName):

    # Lookup the application Id
    SQL = "select ApplicationId from Application where ApplicationName = '%s'" % (applicationName)
    applicationId = system.db.runScalarQuery(SQL)
    
    return applicationId