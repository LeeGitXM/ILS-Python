'''
Created on Sep 10, 2014

@author: Pete
'''

import system

def recipeMapStatus(recipeKey, status, database = ""):
    SQL = "update RtRecipeMap set status = '%s', Timestamp = getdate() where recipeKey = '%s'" % (status, recipeKey)
    system.db.runUpdateQuery(SQL, database)