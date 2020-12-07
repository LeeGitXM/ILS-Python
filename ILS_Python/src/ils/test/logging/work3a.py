'''
Created on Nov 11, 2020

@author: phass
'''
from ils.logging import xomGetLogger, IGNITION_HANDLER, LOGCFG_LEVEL, LOGCFG_PRIORITY, LOGCFG_RETENTION, DEBUG, DATABASE_HANDLER, CRASH_HANDLER, TRACE, DEFAULT_RETENTION

from ils.test.logging.work3b import work as work3b
from ils.test.logging.test import setLoggerToInfo

HIGH_PRIORITY_CONFIG = {IGNITION_HANDLER: {LOGCFG_LEVEL:TRACE,  LOGCFG_PRIORITY:50}, \
                       DATABASE_HANDLER: {LOGCFG_LEVEL:TRACE,  LOGCFG_PRIORITY:50, LOGCFG_RETENTION:DEFAULT_RETENTION}, \
                       CRASH_HANDLER:    {LOGCFG_LEVEL:TRACE,  LOGCFG_PRIORITY:50}}

# Use the default configuration
log = xomGetLogger('ils.test.logging.work3a', HIGH_PRIORITY_CONFIG)

def setInfo():
    setLoggerToInfo(log)
    
def setTrace():
    print "Setting to a high priority Trace!"
    log.setLevelComboConfig(HIGH_PRIORITY_CONFIG)

def work():
    log.infof("In %s.work()", __name__)
    work3b()
    log.tracef("...back in %s.work", __name__)