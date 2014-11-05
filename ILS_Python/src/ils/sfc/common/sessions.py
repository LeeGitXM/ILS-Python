'''

Interface to database for SFC sessions (basically, a running SFC chart)
Created on Nov 3, 2014

@author: rforbes
'''
import system
from ils.sfc.common.constants import RUNNING, PAUSED
from ils.sfc.gateway.util import reportUnexpectedError
from ils.sfc.common.util import boolToBit
from ils.sfc.common.util import getChartRunId
from ils.sfc.common.util import getDatabase

SESSION_TABLE = 'SfcSessions'
MSG_TABLE = 'ControlPanelMsgs'

def createSession(user, chartName, chartRunId, db):
    '''Record the fact that an sfc chart has been started and some associated info'''
    sql = ("insert into " + SESSION_TABLE + \
        " (userName, chartName, chartRunId, status, startTime, lastChangeTime) values ('%s','%s','%s','%s',getdate(),getdate())") \
         % (user, chartName, chartRunId, RUNNING)
    numUpdated = system.db.runUpdateQuery(sql, db)
    if(numUpdated != 1):
        reportUnexpectedError("insert into session db table failed")
        
def getRunningSessions(user, db):
    '''Get all currently running or paused sessions for the given user'''
    sql = "select * from " + SESSION_TABLE + " where userName = '%s' and (status = '%s' OR status = '%s')" % (user, RUNNING, PAUSED)
    results = system.db.runQuery(sql, db)
    return results
    
def getSession(chartRunId, db):
    '''Get the session for the given chart'''
    sql = "select * from " + SESSION_TABLE + " where chartRunId = '%s'" % (chartRunId)
    results = system.db.runQuery(sql, db)
    return results[0]

def updateSessionStatus(chartProperties, status):
    '''
    update the status and lastChangeTime
    where does this get called from? could manually add to project sfc hooks,
    but an automatic method would be much better...
    '''
    from ils.sfc.gateway.util import sendUpdateControlPanelMsg
    chartRunId = getChartRunId(chartProperties)
    db = getDatabase(chartProperties)
    sql = ("update " + SESSION_TABLE + " set status = '%s', lastChangeTime = getdate() where chartRunId = '%s'") % (status, chartRunId)
    numUpdated = system.db.runUpdateQuery(sql, db)
    if(numUpdated != 1):
        reportUnexpectedError(chartProperties, "update of session db table failed")
    sendUpdateControlPanelMsg(chartProperties)
    
def updateSessionOperation(chartProperties, database):
    '''
    update the status and lastChangeTime
    where does this get called from? could manually add to project sfc hooks,
    but an automatic method would be much better...
    '''
    from ils.sfc.gateway.util import sendUpdateControlPanelMsg
    from ils.sfc.common.constants import OPERATION, DATABASE, CHART_RUN_ID
    operation = chartProperties[OPERATION]
    database = chartProperties[DATABASE]
    chartRunId = chartProperties[CHART_RUN_ID]
    sql = ("update " + SESSION_TABLE + " set operation = '%s', lastChangeTime = getdate() where chartRunId = '%s'") % (operation, chartRunId)
    numUpdated = system.db.runUpdateQuery(sql, database)
    if(numUpdated != 1):
        print "update of session db table failed"
    sendUpdateControlPanelMsg(chartProperties)

def getControlPanelMessages(chartRunId, db):
    sql = "select * from " + MSG_TABLE + " where chartRunId = '%s' order by createTime asc" % (chartRunId)
    results = system.db.runQuery(sql, db)
    return results

def addControlPanelMessage(message, ackRequired, chartRunId, db):
    sql = "insert into " + MSG_TABLE + " (chartRunId, message,createTime,ackRequired) values ('%s','%s',getdate(),%d)" % (chartRunId, message, boolToBit(ackRequired) )
    numUpdated = system.db.runUpdateQuery(sql, db)
    if(numUpdated != 1):
        reportUnexpectedError("insert into control panel msg db table failed")

def acknowledgeControlPanelMessage(msgId, db):
    sql = ("update " + MSG_TABLE + " set ackTime = getdate() where id = %s") % msgId
    numUpdated = system.db.runUpdateQuery(sql, db)
    if(numUpdated != 1):
        reportUnexpectedError("setting ack time in control panel msg table failed")
