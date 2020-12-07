import time, system
import ils.logging as logging
from ils.logging import OFF, NOTSET, FATAL, ERROR, WARNING, INFO, DEBUG, TRACE, IGNITION_HANDLER, DATABASE_HANDLER, CRASH_HANDLER, LOGCFG_LEVEL, LOGCFG_PRIORITY, LOGCFG_RETENTION, DEFAULT_LEVEL_COMBO_CFG

Retention = {FATAL:1, ERROR:1, WARNING:1, INFO:1, DEBUG:1, TRACE:1}  # Retentions are in hours

log_cfg = {IGNITION_HANDLER: {LOGCFG_LEVEL:INFO,  LOGCFG_PRIORITY:20}, \
                   DATABASE_HANDLER: {LOGCFG_LEVEL:INFO, LOGCFG_PRIORITY:20, LOGCFG_RETENTION:Retention}, \
                   CRASH_HANDLER:    {LOGCFG_LEVEL:TRACE, LOGCFG_PRIORITY:20}}

log = logging.xomGetLogger('ils.test.logging.test', log_cfg)

'''
This was added by Pete   
'''
def setLoggerToTrace(log):
    print 'Setting to TRACE...'
    level_combo_cfg = {IGNITION_HANDLER: {LOGCFG_LEVEL:TRACE,  LOGCFG_PRIORITY:20}, \
                   DATABASE_HANDLER: {LOGCFG_LEVEL:TRACE, LOGCFG_PRIORITY:20, LOGCFG_RETENTION:Retention}, \
                   CRASH_HANDLER:    {LOGCFG_LEVEL:TRACE, LOGCFG_PRIORITY:20}}
    log.setLevelComboConfig(level_combo_cfg)

def setLoggerToDebug(log):
    print 'Setting to DEBUG...'
    level_combo_cfg = {IGNITION_HANDLER: {LOGCFG_LEVEL:DEBUG,  LOGCFG_PRIORITY:20}, \
                   DATABASE_HANDLER: {LOGCFG_LEVEL:DEBUG, LOGCFG_PRIORITY:20, LOGCFG_RETENTION:Retention}, \
                   CRASH_HANDLER:    {LOGCFG_LEVEL:DEBUG, LOGCFG_PRIORITY:20}}
    log.setLevelComboConfig(level_combo_cfg)

def setLoggerToInfo(log):
    print 'Setting to INFO...'
    level_combo_cfg = {IGNITION_HANDLER: {LOGCFG_LEVEL:INFO,  LOGCFG_PRIORITY:20}, \
                       DATABASE_HANDLER: {LOGCFG_LEVEL:INFO,  LOGCFG_PRIORITY:20, LOGCFG_RETENTION:Retention}, \
                       CRASH_HANDLER:    {LOGCFG_LEVEL:INFO,  LOGCFG_PRIORITY:20}}
    log.setLevelComboConfig(level_combo_cfg)
    
def setLoggerToOff(log):
    print 'Setting to OFF / NOTSET...'
    level_combo_cfg = {IGNITION_HANDLER: {LOGCFG_LEVEL:NOTSET,  LOGCFG_PRIORITY:20}, \
                       DATABASE_HANDLER: {LOGCFG_LEVEL:NOTSET,  LOGCFG_PRIORITY:20, LOGCFG_RETENTION:Retention}, \
                       CRASH_HANDLER:    {LOGCFG_LEVEL:NOTSET,  LOGCFG_PRIORITY:20}}
    log.setLevelComboConfig(level_combo_cfg)
    

def doWork():
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


def doWorkLog(log):
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
    