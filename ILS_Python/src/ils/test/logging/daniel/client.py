'''
Created on Jan 29, 2021

@author: phass
'''

import system, time
import ils.log2 as Log

def work():
    print "In %s.work()" % (__name__)
    log = Log.getLogger(__name__)
    
    #log.trace("A trace message")
    #time.sleep(0.1)

    #log.debug("A debug message")
    #time.sleep(0.1)
    
    log.info("An info message")
    #time.sleep(0.1)

    #log.warn("A warning")
    #time.sleep(0.1)
    
    #log.error("An error")
    #time.sleep(0.1)