import system, time
import ils.logging as logging
from ils.logging.constants import FATAL, ERROR, WARNING, INFO, DEBUG, TRACE, IGNITION_HANDLER, DATABASE_HANDLER, CRASH_HANDLER, LOGCFG_LEVEL, LOGCFG_PRIORITY, LOGCFG_RETENTION
Retention = {FATAL:1, ERROR:1, WARNING:1, INFO:1, DEBUG:1, TRACE:1}  # Retentions are in hours
level_combo_cfg = {IGNITION_HANDLER: {LOGCFG_LEVEL:WARNING,  LOGCFG_PRIORITY:15}, \
                   DATABASE_HANDLER: {LOGCFG_LEVEL:INFO,     LOGCFG_PRIORITY:15, LOGCFG_RETENTION:Retention}, \
                   CRASH_HANDLER:    {LOGCFG_LEVEL:INFO,     LOGCFG_PRIORITY:15}}
log = logging.xomGetLogger('xom.test.subtest', level_combo_cfg)

def main2(test_var):
    logs2(test_var)
    
def logs2(test_var):
    log.trace('A trace log : %d %f' % (3, 4.2))
    time.sleep(0.1)
    log.tracef('A tracef log : %d %f', 3, 4.2)
    time.sleep(0.1)
    log.debug('This error occurred: %s' % test_var)
    time.sleep(0.1)
    log.debugf('This error occurred: %s', test_var)
    time.sleep(0.1)
    log.info('This info occurred: %s' % test_var)
    time.sleep(0.1)
    log.infof('This info occurred: %s', test_var)
    time.sleep(0.1)
    log.warning('This warning occurred: %s' % test_var)
    time.sleep(0.1)
    log.warningf('This warning occurred: %s', test_var)
    time.sleep(0.1)
    log.error('This error occurred: %s' % test_var)
    time.sleep(0.1)
    log.errorf('This error occurred: %s', test_var)
    time.sleep(0.1)

def fail2():
    a = 1 / 0  # fail on purpose    
