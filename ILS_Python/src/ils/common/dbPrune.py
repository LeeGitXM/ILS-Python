'''
Created on Mar 8, 2020

@author: phass
'''

import system
from ils.config.client import getDatabase, getTagProvider
from ils.common.constants import CR
from ils.common.database import toDateString
from ils.io.util import readTag
from ils.log import getLogger
log = getLogger(__name__)

SQL = [
    "delete from alarm_events where eventTime ",
    "delete from BtBatchRun where StartDate",
    "delete from DtDiagnosisEntry where Timestamp",
    "delete from DtFinalDiagnosisLog where Timestamp",
    "delete from LtHistory where SampleTime",
    "delete from QueueDetail where Timestamp",
    "delete from RtDownloadMaster where DownloadStartTime",
    "delete from SfcRunLog where StartTime",
    "delete from TkLogbookDetail where Timestamp"
    ]
    
def pruneClient(event):
    log.infof("In %s.pruneClient", __name__)

    db = getDatabase()
    provider = getTagProvider()
    pruneDays = readTag("[%s]Configuration/Common/dbPruneDays" % (provider)).value
    log.tracef("Pruning to %d days", pruneDays)
    pruneDate = system.date.addDays(system.date.now(), -1 * pruneDays)
    pruneDate = toDateString(pruneDate)
    textArea = event.source.parent.getComponent("Text Area")
    textArea.text = ""
    
    def work(textArea=textArea):
        txt = ""
        for sql in SQL:
            t = pruner(sql, pruneDate, db)
            txt = txt + CR + t
            textArea.text = txt
    
    system.util.invokeLater(work)
    
def prune(db, provider):
    ''' This can be called from a timer script or a cron timer '''
    log.infof("In %s.prune", __name__)
    
    pruneDays = readTag("[%s]Configuration/Common/dbPruneDays" % (provider)).value
    log.infof("Pruning to %d days", pruneDays)
    
    pruneDate = system.date.addDays(system.date.now(), -1 * pruneDays)
    pruneDate = toDateString(pruneDate)
    
    for sql in SQL:
        txt = pruner(sql, pruneDate, db)
        log.infof(txt)
        
    log.infof("...done pruning!")
    
def pruner(SQL, pruneDate, db):
    words = SQL.split(" ")
    tableName = words[2]
    SQL = "%s < '%s'" % (SQL, pruneDate)
    log.tracef(SQL)
    rows = system.db.runUpdateQuery(SQL, db)
    txt = "Pruned %d rows from %s" % (rows, tableName)
    return txt