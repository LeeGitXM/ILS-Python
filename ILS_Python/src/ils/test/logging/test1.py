'''
This is a test of setting the log level at the module level.
This is a requirement for Daniel and is most convenient if you are doing significant development in a 
given module and doing a bunch of gateway restarts or new clients and you don't want to have to keep setting the
modes of the relevant loggers.
'''

import time
from ils.log import getLogger

def workTrace():
    log = getLogger(__name__ + ".trace", "trace")
    print "In %s.workTrace()" % (__name__)
    
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
    
def workDebug():
    print "In %s.workDebug()" % (__name__)
    log = getLogger(__name__ + ".debug", "debug")
    
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