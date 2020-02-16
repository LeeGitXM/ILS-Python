'''
Created on Jan 22, 2020

@author: phass
'''

from ils.sfc.common.constants import GLOBAL_SCOPE
from ils.sfc.recipeData.api import s88Set

def recipeAccess(chart, step):
    print "In %s.recipeAccess()" % (__name__)
    s88Set(chart, step, "r1-c9.targetValue", 125.0, GLOBAL_SCOPE)

def recipeAccessBad(chart, step):
    print "In %s.recipeAccessBad()" % (__name__)
    s88Set(chart, step, "r1-c9.target", 100.0, GLOBAL_SCOPE)
    