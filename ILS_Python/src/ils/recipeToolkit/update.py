'''
Created on Sep 10, 2014

@author: Pete
'''

import system

def recipeMapStatus(recipeKey, status):
    SQL = "update RtRecipeMap set status = '%s', Timestamp = getdate() where recipeKey = '%s'" % (status, recipeKey)
    print "SQL: ", SQL
    rows = system.db.runUpdateQuery(SQL)
    
    print "updated %i rows" % (rows)