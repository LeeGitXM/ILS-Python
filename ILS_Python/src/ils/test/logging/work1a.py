'''
Created on Nov 11, 2020

@author: phass
'''

import ils.logging as logging
from ils.logging.test import setLoggerToInfo, setLoggerToTrace, doWork

# Use the default configuration
log = logging.xomGetLogger('xom.test.work1')

def setInfo():
    setLoggerToInfo(log)
    
def setTrace():
    setLoggerToTrace(log)

def work():
    doWork(log)
