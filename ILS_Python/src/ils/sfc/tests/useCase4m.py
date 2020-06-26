'''
Created on Apr 25, 2017

@author: phass
'''

import system
from ils.sfc.gateway.api import getDatabaseName, getStepProperty
from ils.sfc.common.constants import WINDOW_ID, WINDOW_TITLE

def activationCallback(scopeContext, stepProperties):
    print "In %s.activationCallback() " % (__name__)
    
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    
    # Test that the arguments that passed are usable
    title = getStepProperty(stepProperties, WINDOW_TITLE) 
    database = getDatabaseName(chartScope)
    windowId = stepScope[WINDOW_ID]
    
    prompt = "FoobyBar"
    
    SQL = "update SfcReviewDataTable set prompt = '%s' where windowId = %s and configKey = 'row1' and isPrimary = 1" % (prompt, str(windowId) )
    print SQL
    
    rows = system.db.runUpdateQuery(SQL, database)
    if rows != 1:
        print"Warning: %d rows were updated when exactly 1 was expected.  SQL = %s" % (rows, SQL)
    
    print "--------------------------"
    print "Title:     ", title
    print "Database:  ", database
    print "Window Id: ", windowId
    print "--------------------------"


def activationCallback2(scopeContext, stepProperties):
    print "In %s.activationCallback2" % (__name__)
    
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    
    # Test that the arguments that passed are usable
    title = getStepProperty(stepProperties, WINDOW_TITLE) 
    database = getDatabaseName(chartScope)
    windowId = stepScope[WINDOW_ID]
    
    print "--------------------------"
    print "Title:     ", title
    print "Database:  ", database
    print "Window Id: ", windowId
    print "--------------------------"
    
    x = 3.4
    y = 0.0
    z = x / y
    
    print "Reached the end!"