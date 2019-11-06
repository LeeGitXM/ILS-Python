'''
Created on Jan 7, 2017

@author: phass
'''

import system, string

# Return the current value of a specified variable from
# the database. If the query is not defined, simply 
# return the parameter name.

def getValue(param, modelId) :

    # Fetch alerts that are active and not suppressed
    def getActiveAlertCount(modelId) :
        SQL = "select count(*) from events where RuleId = " + str(modelId) + " and ClearTimestamp is NULL "
        SQL = SQL + " and RuleId not in (select TargetId from Suppressors)"
        
        cnt = system.db.runScalarQuery(SQL)
        return cnt

    def getClearedAlertCount(modelId) :
        SQL = "select count(*) from events where RuleId = " + str(modelId) + " and ClearTimestamp is not NULL"
        cnt = system.db.runScalarQuery(SQL)
        return cnt

    def getAckdAlertCount(modelId) :
        SQL = "select count(*) from events where RuleId = " + str(modelId) + " and AckTimeStamp is not NULL"
        cnt = system.db.runScalarQuery(SQL)
        return cnt
    
    def getSuppressedAlertCount(modelId) :
        SQL = "select count(*) from Events where RuleId = " + str(modelId)
        SQL = SQL + " and suppressedCntr > 0 or ManuallySuppressed = 1" 
        cnt = system.db.runScalarQuery(SQL)
        return cnt

    def getStatus(modelId) :
        SQL = "select status from RuleStatus where RuleId = " + str(modelId) 
        status = system.db.runScalarQuery(SQL)
        status=string.upper(status)
        return status
        
    def getSuppressorCount(modelId) :
        SQL = "select count(*) from Suppressors where TargetId = " + str(modelId)
        cnt = system.db.runScalarQuery(SQL)
        return cnt
    
    #----------------------------------------------------------
    value = param

    if param == 'activeAlertCount':
        value = getActiveAlertCount(modelId)
    elif param == 'clearedAlertCount':
        value = getClearedAlertCount(modelId)
    elif param == 'ackdAlertCount':
        value = getAckdAlertCount(modelId)
    elif param == 'suppressedAlertCount':
        value = getSuppressedAlertCount(modelId)
    elif param == 'suppressorCount':
        value = getSuppressorCount(modelId)
    elif param == 'status':
        value = getStatus(modelId)
    else:
        value = "unknown"

    return value