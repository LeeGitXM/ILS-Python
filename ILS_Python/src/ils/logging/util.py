'''
Created on Sep 4, 2020

@author: aedmw
'''
import system, datetime
import xom.logging
log = xom.logging.xomGetLogger('xom.logging.util')

def logCleanup(db_name='Logs'):
    '''
    Log cleanup function called by Gateway Timer script.
    '''
    sql = 'DELETE FROM log WHERE retain_until < ?'
    values = [datetime.datetime.now()]
    return_val = system.db.runPrepUpdate(sql, values, db_name)
    log.debugf('Deleted %d rows from log', return_val)
    
    '''
    now = datetime.datetime.now()
    delta = datetime.timedelta(days=30)
    delete_before = now - delta
    log.debugf('Deleting all log entries with timestamp before %s', delete_before)    
    '''
    
