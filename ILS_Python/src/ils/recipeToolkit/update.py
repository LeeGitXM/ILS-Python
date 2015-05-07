'''
Created on Sep 10, 2014

@author: Pete
'''

import system

def recipeFamilyStatus(familyName, status, database = ""):
    SQL = "update RtRecipeFamily set status = '%s', Timestamp = getdate() where recipeFamilyName = '%s'" % (status, familyName)
    system.db.runUpdateQuery(SQL, database)
    