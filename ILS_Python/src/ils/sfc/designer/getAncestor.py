'''
Created on Jan 7, 2022

@author: ils
'''

import system
from ils.sfc.recipeData.api import s88GetAncestors, s88GetEnclosingCharts

def main(chartPath, scope):
    print "In %s.main() with %s - %s" % (__name__, chartPath, scope)
    ancestors = s88GetAncestors(chartPath, scope)    
    print "...returning: %s" % (str(ancestors))
    return ancestors

def getEnclosingCharts(chartPath, isolationMode):
    print "In %s.getEnclosingCharts() with %s, IsolationMode: %s" % (__name__, chartPath, str(isolationMode))
    ds = s88GetEnclosingCharts(chartPath)
    return ds