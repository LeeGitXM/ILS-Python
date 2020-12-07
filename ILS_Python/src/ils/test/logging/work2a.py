'''
Created on Nov 11, 2020

@author: phass

This test demonstrates two Python modules sharing the same logger.
The log level can be set from either module 
'''

import ils.logging as logging
from ils.test.logging.test import setLoggerToInfo, setLoggerToTrace

# Use the default configuration
log = logging.xomGetLogger('ils.test.logging.work2')

def setInfo():
    setLoggerToInfo(log)
    
def setTrace():
    setLoggerToTrace(log)

def work():
    log.infof("Doing some work!")
    log.tracef("Doing some more work!")