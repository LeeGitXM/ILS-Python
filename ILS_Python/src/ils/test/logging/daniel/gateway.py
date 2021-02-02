'''
Created on Jan 29, 2021

@author: phass
'''
import system, time
import system.ils.log.properties as LogProps 
log = LogProps.getLogger(__name__)


import ils.logging as logging
from ils.logging import OFF, NOTSET, FATAL, ERROR, WARNING, INFO, DEBUG, TRACE, IGNITION_HANDLER, DATABASE_HANDLER, CRASH_HANDLER, LOGCFG_LEVEL, LOGCFG_PRIORITY, LOGCFG_RETENTION, DEFAULT_LEVEL_COMBO_CFG

Retention = {FATAL:1, ERROR:1, WARNING:1, INFO:1, DEBUG:1, TRACE:1}  # Retentions are in hours

log_cfg = {IGNITION_HANDLER: {LOGCFG_LEVEL:INFO,  LOGCFG_PRIORITY:20}, \
                   DATABASE_HANDLER: {LOGCFG_LEVEL:INFO, LOGCFG_PRIORITY:20, LOGCFG_RETENTION:Retention}, \
                   CRASH_HANDLER:    {LOGCFG_LEVEL:TRACE, LOGCFG_PRIORITY:20}}

log = logging.xomGetLogger('ils.test.logging.test', log_cfg)


def work():
    print "In %s.work()" % (__name__)
    
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