import time, system
import ils.logging as logging
from ils.logging import FATAL, ERROR, WARNING, INFO, DEBUG, TRACE, IGNITION_HANDLER, DATABASE_HANDLER, CRASH_HANDLER, LOGCFG_LEVEL, LOGCFG_PRIORITY, LOGCFG_RETENTION
Retention = {FATAL:1, ERROR:1, WARNING:1, INFO:1, DEBUG:1, TRACE:1}  # Retentions are in hours

'''
This was added by Pete
'''
def setLoggerToTrace(log):
    '''
    This test is to test an efficiency setup, where only INFO and up goes to all the handlers.
    '''
    print 'Setting to TRACE...'
    level_combo_cfg = {IGNITION_HANDLER: {LOGCFG_LEVEL:TRACE,  LOGCFG_PRIORITY:20}, \
                   DATABASE_HANDLER: {LOGCFG_LEVEL:TRACE, LOGCFG_PRIORITY:20, LOGCFG_RETENTION:Retention}, \
                   CRASH_HANDLER:    {LOGCFG_LEVEL:TRACE, LOGCFG_PRIORITY:20}}
    log.setLevelComboConfig(level_combo_cfg)


def setLoggerToInfo(log):
    '''
    This test is to test an efficiency setup, where only INFO and up goes to all the handlers.
    '''
    print 'Setting to INFO...'
    level_combo_cfg = {IGNITION_HANDLER: {LOGCFG_LEVEL:INFO,  LOGCFG_PRIORITY:20}, \
                       DATABASE_HANDLER: {LOGCFG_LEVEL:INFO,  LOGCFG_PRIORITY:20, LOGCFG_RETENTION:Retention}, \
                       CRASH_HANDLER:    {LOGCFG_LEVEL:INFO,  LOGCFG_PRIORITY:20}}
    log.setLevelComboConfig(level_combo_cfg)
    

def doWork(log):
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
    