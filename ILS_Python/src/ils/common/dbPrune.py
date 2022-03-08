'''
Created on Mar 8, 2020

@author: phass
'''

import system
from ils.common.config import getDatabase, getTagProvider
from ils.common.database import toDateString

def prune():
    from ils.log import getLogger
    log =getLogger(__name__)

    log.infof("In %s.prune", __name__)
    
    db = getDatabase()
    provider = getTagProvider()
    
    pruneDays = system.tag.read("[%s]Configuration/Common/dbPruneDays" % (provider)).value
    log.tracef("Pruning to %d days", pruneDays)
    
    pruneDate = system.date.addDays(system.date.now(), -1 * pruneDays)
    pruneDate = toDateString(pruneDate)

    pruner("delete from alarm_events where eventTime < '%s'" % pruneDate, "alarm_events", db, log)
    ''' TODO: Need to delete from alarm_event_data '''
    
    ''' This was also prune BtBatchLog and BtStripperBatchLog due to a cascade delete. '''
    pruner("delete from BtBatchRun where StartDate < '%s'" % pruneDate, "BtBatchRun", db, log)
    pruner("delete from DtDiagnosisEntry where Timestamp < '%s'" % pruneDate, "DtDiagnosisEntry", db, log)
    pruner("delete from DtFinalDiagnosisLog where Timestamp < '%s'" % pruneDate, "DtFinalDiagnosisLog", db, log)
    pruner("delete from LtHistory where SampleTime < '%s'" % pruneDate, "LtHistory", db, log)
    pruner("delete from QueueDetail where Timestamp < '%s'" % pruneDate, "QueueDetail", db, log)
    pruner("delete from RtDownloadMaster where DownloadStartTime < '%s'" % pruneDate, "RtDownloadMaster", db, log)
    pruner("delete from SfcRunLog where StartTime < '%s'" % pruneDate, "SfcRunLog", db, log)
    pruner("delete from TkLogbookDetail where Timestamp < '%s'" % pruneDate, "TkLogbookDetail", db, log)
    
    ''' Not including UIRs in this measure '''
    
    log.tracef("...done pruning!")
    
def pruner(SQL, table, db, log):
    log.tracef(SQL)
    rows = system.db.runUpdateQuery(SQL, db)
    log.tracef("Pruned %d rows from %s", rows, table)