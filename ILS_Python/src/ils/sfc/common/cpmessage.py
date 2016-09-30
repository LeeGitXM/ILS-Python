'''

Things related to Control Panel messages
Created on Nov 3, 2014

@author: rforbes
'''
import system
from ils.sfc.common.util import boolToBit
from ils.sfc.common.util import handleUnexpectedClientError

def getControlPanelMessages(chartRunId, db):
    sql = "select * from SfcControlPanelMsg where chartRunId = '%s' order by createTime asc" % (chartRunId)
    results = system.db.runQuery(sql, db)
    return results

def addControlPanelMessage(message, priority, ackRequired, chartRunId, db):
    from ils.sfc.common.util import createUniqueId
    msgId = createUniqueId()
    sql = ("insert into SfcControlPanelMsg (chartRunId, message, priority, createTime, ackRequired, id) "\
           "values ('%s','%s','%s',getdate(),%d,'%s')") % (chartRunId, message, priority, boolToBit(ackRequired), msgId )
    print sql
    numUpdated = system.db.runUpdateQuery(sql, db)
    if(numUpdated != 1):
        handleUnexpectedClientError("insert into control panel msg db table failed")
    return msgId
