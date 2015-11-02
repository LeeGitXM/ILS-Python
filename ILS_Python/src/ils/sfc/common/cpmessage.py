'''

Things related to Control Panel messages
Created on Nov 3, 2014

@author: rforbes
'''
import system
from ils.sfc.common.util import boolToBit
from ils.sfc.common.util import handleUnexpectedClientError

MSG_TABLE = 'SfcControlPanelMsgs'

def getControlPanelMessages(chartRunId, db):
    sql = "select * from " + MSG_TABLE + " where chartRunId = '%s' order by createTime asc" % (chartRunId)
    results = system.db.runQuery(sql, db)
    return results

def addControlPanelMessage(message, ackRequired, chartRunId, db):
    from ils.sfc.common.util import createUniqueId
    msgId = createUniqueId()
    sql = ("insert into " + MSG_TABLE + " (chartRunId, message,createTime,ackRequired,id) values ('%s','%s',getdate(),%d,'%s')") % (chartRunId, message, boolToBit(ackRequired), msgId )
    numUpdated = system.db.runUpdateQuery(sql, db)
    if(numUpdated != 1):
        handleUnexpectedClientError("insert into control panel msg db table failed")
    return msgId

def acknowledgeControlPanelMessage(msgId, db):
    sql = ("update " + MSG_TABLE + " set ackTime = getdate() where id = '%s'") % msgId
    numUpdated = system.db.runUpdateQuery(sql, db)
    if(numUpdated != 1):
        handleUnexpectedClientError("setting ack time in control panel msg table failed")

def getAckTime(msgId, db):
    sql = ("select ackTime from " + MSG_TABLE + " where id = '%s'") % msgId
    results = system.db.runQuery(sql, db)
    ackTime = results[0][0]
    return ackTime

def timeOutControlPanelMessageAck(msgId, db):
    sql = ("update " + MSG_TABLE + " set ackTimedOut = 1 where id = '%s'") % msgId
    numUpdated = system.db.runUpdateQuery(sql, db)
    if(numUpdated != 1):
        handleUnexpectedClientError("setting ack timed out in control panel msg table failed")
