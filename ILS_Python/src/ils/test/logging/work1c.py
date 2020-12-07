'''
Created on Nov 30, 2020

@author: phass
'''

from ils.logging import xomGetLogger, DEFAULT_LEVEL_COMBO_CFG

from ils.test.logging.test import setLoggerToInfo, setLoggerToTrace

# Use the default configuration
log = xomGetLogger('ils.test.logging.work1c', DEFAULT_LEVEL_COMBO_CFG)

def setInfo():
    setLoggerToInfo(log)
    
def setTrace():
    setLoggerToTrace(log)

def work():
    log.infof("In %s.work()", __name__)
    myWorker()
    log.tracef("...All done in %s.work()", __name__)
    
def myWorker():
    log.tracef("In %s.myWorker()", __name__)
    print "Here I am!"
    log.tracef("...All done in %s.myWorker()", __name__)