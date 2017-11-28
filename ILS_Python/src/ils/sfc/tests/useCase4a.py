'''
Created on Sep 8, 2015

@author: Pete
'''

from ils.sfc.gateway.api import getDatabaseName
from ils.sfc.recipeData.api import s88Get
from ils.sfc.common.constants import GLOBAL_SCOPE

def delayCallback(scopeContext, stepProperties):
    print "In ils.sfc.tests.useCase4a.delayCallback()..."

    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()

    delay = s88Get(chartScope, stepScope, "delay.value", GLOBAL_SCOPE)
    print "The delay from recipe is: ", delay
    
    myDelay = delay * 2.5
    print "The newly calculated delay is: ", myDelay

    return myDelay