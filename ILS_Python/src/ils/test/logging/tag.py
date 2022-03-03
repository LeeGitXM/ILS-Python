'''
Created on Mar 3, 2022

@author: phass
'''

import time
from ils.log.LogRecorder import LogRecorder
log = LogRecorder(__name__)

def work():
    print "In %s.work()" % (__name__)
    
    log.trace("A trace message from a tag change script")
    time.sleep(0.1)

    log.debug("A debug message from a tag change script")
    time.sleep(0.1)
    
    log.info("An info message from a tag change script")
    time.sleep(0.1)

    log.warn("A warning from a tag change script")
    time.sleep(0.1)
    
    log.error("An error from a tag change script")
    time.sleep(0.1)
    
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