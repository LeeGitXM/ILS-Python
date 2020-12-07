'''
Created on Nov 30, 2020

@author: phass
'''

import time
from ils.logging import xomGetLogger, DEFAULT_LEVEL_COMBO_CFG

from ils.test.logging.test import setLoggerToInfo, setLoggerToDebug, setLoggerToTrace, setLoggerToOff

# Use the default configuration
log = xomGetLogger('ils.test.logging.work1a', DEFAULT_LEVEL_COMBO_CFG)

def setInfo():
    setLoggerToInfo(log)
    
def setTrace():
    setLoggerToTrace(log)
    
def setDebug():
    setLoggerToDebug(log)
    
def setOff():
    setLoggerToOff(log)

def work():
    log.trace("A trace message")
    time.sleep(0.1)

    log.debug("A debug message")
    time.sleep(0.1)
    
    log.infof("An info message")
    time.sleep(0.1)

    log.warning("A warning")
    time.sleep(0.1)
    
    log.error("An error")
    time.sleep(0.1)