'''
Created on Apr 25, 2017

@author: phass
'''

from ils.sfc.gateway.api import getDatabaseName, getStepProperty
from ils.sfc.common.constants import WINDOW_ID, WINDOW_TITLE

def activationCallback(scopeContext, stepProperties):
    print "Hello there!"
    
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