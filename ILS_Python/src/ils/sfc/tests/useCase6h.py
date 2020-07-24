'''
Created on Jul 15, 2020

@author: phass
'''

import system
from ils.sfc.common.constants import GLOBAL_SCOPE, SUPERIOR_SCOPE, MSG_STATUS_INFO
from ils.sfc.gateway.api import getChartLogger, postToQueue, getProviderName, getDatabaseName, getChartPath, getIsolationMode
from ils.sfc.recipeData.api import s88Get, s88Set
from ils.diagToolkit.reset import resetApplication
from ils.common.error import catchError

'''
This callback needs to set the limits of the Vanadium flow setpoint to either high or low depending on the 
global voc3-flag. 
'''
def pvMonitorActivationCallback(scopeContext, stepProperties, config):
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    chartPath = getChartPath(chartScope)
 
    print "--------------------------"
    print "In %s.pvMonitorActivationCallback" % (__name__)
    print "scopeContext: ", scopeContext
    print "stepProperties: ", stepProperties
    print "chartScope: ", chartScope
    print "stepScope: ", stepScope
    print "chartPath: ", chartPath
    print "config: ", config
    print "--------------------------"
    
    log = getChartLogger(chartScope)
    blockName = stepScope.get("name","")
    log.tracef("In %s.pvMonitorLevelActivation with %s - %s. . .", __name__, chartPath, blockName)

    database = getDatabaseName(chartScope)
    
    i = 0
    for configRow in config.rows:
        print "Row ", i, " ", configRow
        
        pvKey = configRow.pvKey
        enabled = configRow.enabled
        tolerance = configRow.tolerance
        deadTime = configRow.deadTime
        print "     ", pvKey, enabled, tolerance, deadTime
        
        i = i + 1
    
    '''
    In order to update the configuration you need to iterate through the configuration of the block and find the one you are interested in.
    '''
    for configRow in config.rows:
        pvKey = configRow.pvKey
        
        if pvKey == "tc100":
            print " *** disabling tc100 *** "
            configRow.enabled = False
            
        if pvKey == "pv":
            print " *** setting tolerance *** "
            configRow.tolerance = 5.75
   
    return config