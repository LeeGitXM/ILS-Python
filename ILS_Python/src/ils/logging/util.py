'''
Created on Sep 4, 2020

@author: aedmw
'''
import system, datetime
import ils.logging
log = ils.logging.xomGetLogger('ils.logging.util')

def logCleanup(db_name='Logs'):
    '''
    Log cleanup function called by Gateway Timer script.
    '''
    sql = 'DELETE FROM log WHERE retain_until < ?'
    values = [datetime.datetime.now()]
    return_val = system.db.runPrepUpdate(sql, values, db_name)
    log.debugf('Deleted %d rows from log', return_val)