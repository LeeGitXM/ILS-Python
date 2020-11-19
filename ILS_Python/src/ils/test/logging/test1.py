import system
import xom.logging as logging
from xom.logging import FATAL, ERROR, WARNING, INFO, DEBUG, TRACE, IGNITION_HANDLER, DATABASE_HANDLER, CRASH_HANDLER, LOGCFG_LEVEL, LOGCFG_PRIORITY, LOGCFG_RETENTION
Retention = {FATAL:1, ERROR:1, WARNING:1, INFO:1, DEBUG:1, TRACE:1}  # Retentions are in hours
Level_combo_cfg = {IGNITION_HANDLER: {LOGCFG_LEVEL:INFO,  LOGCFG_PRIORITY:20}, \
                   DATABASE_HANDLER: {LOGCFG_LEVEL:DEBUG, LOGCFG_PRIORITY:20, LOGCFG_RETENTION:Retention}, \
                   CRASH_HANDLER:    {LOGCFG_LEVEL:TRACE, LOGCFG_PRIORITY:20}}
log = logging.xomGetLogger('xom.test', Level_combo_cfg)
from xom.logging.test2 import main2, logs2, fail2

'''
Excellent introduction to logging:
https://opensource.com/article/17/9/python-logging

SQL command to create table used with this module:

CREATE TABLE log (
    [id] [bigint] IDENTITY(1,1) NOT NULL,
    [process] [int] NULL,
    [thread] [bigint] NULL,
    [thread_name] [char](32) NULL,
    [module] [char](32) NULL,
    [logger_name] [char](32) NOT NULL,
    [timestamp] [datetime] NOT NULL DEFAULT (getdate()),
    [retain_until] [datetime] NOT NULL,
    [log_level] [int] NULL,
    [log_levelname] [char](32) NULL,
    [log_message] [char](2048) NOT NULL,
    [function_name] [char](32) NULL,
    [filename] [char](32) NULL,
    [line_number] [int] NULL,
) ON [PRIMARY]
'''

def main():            
    test1()

def test1():
    '''
    This test is to check that logging works right with module settings.
    Database and Crash handlers are set to accept everything.
    Also tests that module priority handling works.  The test2 module is a submodule of this
    one and has a lower priority setup with INFO cutoff.  It should be overridden by the module settings here.
    '''
    logs2('- Testing basic module configuration setup -')

def test2():
    '''
    This test is to test an efficiency setup, where only INFO and up goes to all the handlers.
    '''
    print 'Testing efficiency - only INFO and up should be sent to all.'
    level_combo_cfg = {IGNITION_HANDLER: {LOGCFG_LEVEL:INFO,  LOGCFG_PRIORITY:20}, \
                       DATABASE_HANDLER: {LOGCFG_LEVEL:INFO,  LOGCFG_PRIORITY:20, LOGCFG_RETENTION:Retention}, \
                       CRASH_HANDLER:    {LOGCFG_LEVEL:INFO,  LOGCFG_PRIORITY:20}}
    log.setLevelComboConfig(level_combo_cfg)
    logs2('- Testing efficiency setup -')

def test3():
    '''
    This is to test the Crash queue handler.  It should send all levels to database after ERROR logged.
    '''
    print 'Testing Crash Queue'
    level_combo_cfg = {IGNITION_HANDLER: {LOGCFG_LEVEL:DEBUG,  LOGCFG_PRIORITY:20}, \
                       DATABASE_HANDLER: {LOGCFG_LEVEL:INFO,   LOGCFG_PRIORITY:20, LOGCFG_RETENTION:Retention}, \
                       CRASH_HANDLER:    {LOGCFG_LEVEL:TRACE,  LOGCFG_PRIORITY:20}}
    log.setLevelComboConfig(level_combo_cfg)
    logs2('- Testing crash queue -')
    
def test4():
    '''
    This is to test runtime change of the root level.
    '''
    level_combo_cfg = {IGNITION_HANDLER: {LOGCFG_LEVEL:DEBUG,  LOGCFG_PRIORITY:15}, \
                       DATABASE_HANDLER: {LOGCFG_LEVEL:TRACE,  LOGCFG_PRIORITY:30, LOGCFG_RETENTION:Retention}, \
                       CRASH_HANDLER:    {LOGCFG_LEVEL:TRACE,  LOGCFG_PRIORITY:30}}
    root = logging.getLogger()
    root.setRootLevel(level_combo_cfg)
    try:
        main2('- Testing root level change -')
        fail2()
    except:
        log.exception('fail2 failed - big surprise')
        
if __name__ == '__main__':
    main()
    
    
    
                