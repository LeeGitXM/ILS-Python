'''
Created on Nov 30, 2020

@author: phass
'''

import time
import system.ils.log.properties as LogProps 
from ils.logging import DEFAULT_LEVEL_COMBO_CFG

from ils.test.logging.test import setLoggerToInfo, setLoggerToDebug, setLoggerToTrace, setLoggerToOff

# Use the default configuration
from ils.log.LogRecorder import LogRecorder
log = LogProps.getLogger('ils.test.logging.work1a')

def setInfo():
    setLoggerToInfo(log)
    
def setTrace():
    setLoggerToTrace(log)
    
def setDebug():
    setLoggerToDebug(log)
    
def setOff():
    setLoggerToOff(log)

def work():
    print "In %s.work0()" % (__name__)
    
    log.trace("A trace message")
    time.sleep(0.1)

    log.debug("A debug message")
    time.sleep(0.1)
    
    log.info("An info message")
    time.sleep(0.1)

    log.warning("A warning")
    time.sleep(0.1)
    
    log.error("An error")
    time.sleep(0.1)
    print "Done!"