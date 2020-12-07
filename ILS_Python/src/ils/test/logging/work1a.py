'''
Created on Nov 11, 2020

@author: phass
'''
from ils.logging import xomGetLogger, DEFAULT_LEVEL_COMBO_CFG

from ils.test.logging.work1b import work as work1b
from ils.test.logging.test import setLoggerToInfo, setLoggerToTrace

# Use the default configuration
log = xomGetLogger('ils.test.logging.work1a', DEFAULT_LEVEL_COMBO_CFG)

def setInfo():
    setLoggerToInfo(log)
    
def setTrace():
    setLoggerToTrace(log)

def work():
    log.infof("In %s.work()", __name__)
    work1b()
    log.tracef("...back in %s.work", __name__)