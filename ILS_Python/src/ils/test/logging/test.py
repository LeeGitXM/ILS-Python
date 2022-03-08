import time
from ils.log import getLogger
log = getLogger(__name__)

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