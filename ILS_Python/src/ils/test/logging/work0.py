'''
Created on Nov 30, 2020

@author: phass
'''

import time

#from ils.logging import DEFAULT_LEVEL_COMBO_CFG
#from ils.test.logging.test import setLoggerToInfo, setLoggerToDebug, setLoggerToTrace, setLoggerToOff

import system.ils.log.properties as LogProps 
log = LogProps.getLogger('ils.test.logging.work')

#def setInfo():
#    setLoggerToInfo(log)
    
#def setTrace():
#    setLoggerToTrace(log)
    
#def setDebug():
#    setLoggerToDebug(log)
    
#def setOff():
#    setLoggerToOff(log)

def work():
    print "In %s.work()" % (__name__)
    
    log.trace("A trace message")
    time.sleep(0.1)

    log.debug("A debug message")
    time.sleep(0.1)
    
    log.info("An info message")
    time.sleep(0.1)

    log.warn("A warning")
    time.sleep(0.1)
    
    log.error("An error")
    time.sleep(0.1)
    
    log.info("This is a formatted info message #%d"%(42)) 
    log.info("This is also a formatted info message #{}",43) 
    
    print "Done!"
    
def workf():
    print "In %s.workf()" % (__name__)
    
    pi = 3.14159
    
    log.tracef("A trace message, pi = %.3f", pi)
    time.sleep(0.1)

    log.debugf("A debug message, pi = %.3f", pi)
    time.sleep(0.1)
    
    log.infof("An info message, pi = %.3f", pi)
    time.sleep(0.1)

    log.warnf("A warning, pi = %.3f", pi)
    time.sleep(0.1)
    
    log.errorf("An error, pi = %.3f", pi)
    time.sleep(0.1)
    print "Done!"