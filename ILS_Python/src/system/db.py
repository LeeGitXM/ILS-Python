'''
Created on Aug 27, 2014

@author: ILS
'''
DOUBLE="DOUBLE"
INTEGER="INTEGER"
TIMESTAMP="TIMESTAMP"
VARCHAR="VARCHAR"

READ_UNCOMMITTED = 1

def beginTransaction(SQL):
    return True

def closeTransaction(tx):
    return True

# Returns a procedure call context
def createSProcCall(procname):
    pass

def commitTransaction(tx):
    return True

def dateFormat(timestamp, format):
    return True

# Returns a result set
def execSProcCall(context):
    pass

def getConnectionInfo(dbName):
    pass

def getConnections():
    pass

def refresh(component,name):
    pass

def rollbackTransaction(tx):
    return True

def runPrepQuery(SQL):
    return True

def runPrepUpdate(SQL):
    return True

def runQuery(SQL, database, tx):
    return True

def runScalarQuery(SQL):
    return 6

def runScalarPrepQuery(SQL):
    return 6

def runUpdateQuery(SQL):
    return True