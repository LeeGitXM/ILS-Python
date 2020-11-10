import time
import ils.logging as logging
from ils.logging import FATAL, ERROR, WARNING, INFO, DEBUG, TRACE, IGNITION_HANDLER, DATABASE_HANDLER, CRASH_HANDLER, LOGCFG_LEVEL, LOGCFG_PRIORITY, LOGCFG_RETENTION
Retention = {FATAL:1, ERROR:1, WARNING:1, INFO:1, DEBUG:1, TRACE:1}  # Retentions are in hours

'''
This was added by Pete
'''
def set1():
    '''
    This test is to test an efficiency setup, where only INFO and up goes to all the handlers.
    '''
    log = logging.xomGetLogger('xom.test')
    print 'Setting basic configuration...'
    level_combo_cfg = {IGNITION_HANDLER: {LOGCFG_LEVEL:INFO,  LOGCFG_PRIORITY:20}, \
                   DATABASE_HANDLER: {LOGCFG_LEVEL:DEBUG, LOGCFG_PRIORITY:20, LOGCFG_RETENTION:Retention}, \
                   CRASH_HANDLER:    {LOGCFG_LEVEL:TRACE, LOGCFG_PRIORITY:20}}
    log.setLevelComboConfig(level_combo_cfg)


def set2():
    '''
    This test is to test an efficiency setup, where only INFO and up goes to all the handlers.
    '''
    log = logging.xomGetLogger('xom.test')
    print 'Testing efficiency - only INFO and up should be sent to all.'
    level_combo_cfg = {IGNITION_HANDLER: {LOGCFG_LEVEL:INFO,  LOGCFG_PRIORITY:20}, \
                       DATABASE_HANDLER: {LOGCFG_LEVEL:INFO,  LOGCFG_PRIORITY:20, LOGCFG_RETENTION:Retention}, \
                       CRASH_HANDLER:    {LOGCFG_LEVEL:INFO,  LOGCFG_PRIORITY:20}}
    log.setLevelComboConfig(level_combo_cfg)
    
    
def work():
    log = logging.xomGetLogger('xom.test')
    
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


def work1():    
    level_combo_cfg = {IGNITION_HANDLER: {LOGCFG_LEVEL:INFO,  LOGCFG_PRIORITY:20}, \
                       DATABASE_HANDLER: {LOGCFG_LEVEL:INFO,  LOGCFG_PRIORITY:20, LOGCFG_RETENTION:Retention}, \
                       CRASH_HANDLER:    {LOGCFG_LEVEL:INFO,  LOGCFG_PRIORITY:20}}
    
    log = logging.xomGetLogger('xom.test', level_combo_cfg)
    
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


def work2():
    level_combo_cfg = {IGNITION_HANDLER: {LOGCFG_LEVEL:TRACE,  LOGCFG_PRIORITY:20}, \
                       DATABASE_HANDLER: {LOGCFG_LEVEL:TRACE,  LOGCFG_PRIORITY:20, LOGCFG_RETENTION:Retention}, \
                       CRASH_HANDLER:    {LOGCFG_LEVEL:INFO,  LOGCFG_PRIORITY:20}}
    
    log = logging.xomGetLogger('xom.test', level_combo_cfg)
    
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