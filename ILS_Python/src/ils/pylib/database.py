'''
Created on Dec 19, 2016

@author: phass
'''

import system.ils.blt.diagram as script
import system

# Place a result of "true" in the common dictionary
# if the application is found in the default database.
# Argument is the application name
def initialize(common,name):
    handler = script.getHandler()
    db = handler.getDefaultDatabase(name)
    SQL = "SELECT ApplicationId FROM DtApplication "\
          " WHERE Application = '%s';" % name
    system.db.runScalarQuery(SQL,db)

    common['result'] = True
