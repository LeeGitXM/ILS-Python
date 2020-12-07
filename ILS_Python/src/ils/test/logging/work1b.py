'''
Created on Nov 11, 2020

@author: phass
'''
from ils.logging import xomGetLogger, DEFAULT_LEVEL_COMBO_CFG

from ils.test.logging.work1c import work as work1c
from ils.test.logging.test import setLoggerToInfo, setLoggerToTrace

# Use the default configuration
log = xomGetLogger('ils.test.logging.work1b', DEFAULT_LEVEL_COMBO_CFG)

def setInfo():
    setLoggerToInfo(log)
    
def setTrace():
    setLoggerToTrace(log)

def work():
    log.infof("In %s.work()", __name__)
    worker()
    log.tracef("...back in %s.work", __name__)
    
def worker():
    log.tracef("In %s.worker()", __name__)
    work1c()
    log.tracef("...back in %s.worker", __name__)