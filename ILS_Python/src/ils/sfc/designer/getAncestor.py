'''
Created on Jan 7, 2022

@author: ils
'''

import system
from ils.sfc.recipeData.api import s88GetAncestors, s88GetEnclosingCharts
from ils.common.config import getIsolationDatabaseFromInternalDatabase, getIsolationTagProviderFromInternalDatabase, getIsolationTimeFactorFromInternalDatabase, \
    getProductionDatabaseFromInternalDatabase, getProductionTagProviderFromInternalDatabase, getProductionTimeFactorFromInternalDatabase
    
def main(chartPath, scope):
    print "In %s.main() with %s - %s" % (__name__, chartPath, scope)
    ancestors = s88GetAncestors(chartPath, scope)    
    print "...returning: %s" % (str(ancestors))
    return ancestors

def getEnclosingCharts(chartPath, isolationMode):
    print "In %s.getEnclosingCharts() with %s, IsolationMode: %s" % (__name__, chartPath, str(isolationMode))
    ds = s88GetEnclosingCharts(chartPath)
    return ds

def getProjectInterfaces(projectName, isolationMode):
    print "In %s.getProjectInterfaces() with project: %s, IsolationMode: %s" % (__name__, projectName, str(isolationMode))

    if isolationMode:
        tagProvider = getIsolationTagProviderFromInternalDatabase(projectName)
        database = getIsolationDatabaseFromInternalDatabase(projectName)
        timeFactor = getIsolationTimeFactorFromInternalDatabase(projectName)
    else:
        tagProvider = getProductionTagProviderFromInternalDatabase(projectName)
        database = getProductionDatabaseFromInternalDatabase(projectName)
        timeFactor = getProductionTimeFactorFromInternalDatabase(projectName)

    interfaces = [tagProvider, database, str(timeFactor)]
    print "Returning: ", interfaces
    
    return interfaces