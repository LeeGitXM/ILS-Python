'''
Created on Aug 27, 2014

@author: ILS
'''

def beginTransaction(SQL):
    return True

def closeTransaction(tx):
    return True

def commitTransaction(tx):
    return True

def dateFormat(timestamp, format):
    return True

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

def runUpdateQuery(SQL):
    return True