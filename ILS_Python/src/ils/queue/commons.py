'''
Created on Sep 9, 2014

@author: ILS
'''
import system, string

# Fetch the queue  id given the Queue Key 
def getQueueId(queueKey, db = ''):
    queueKey=string.upper(str(queueKey))    
    SQL = "select QueueId from QueueMaster where QueueKey = '%s'" % (queueKey)
    queueId = system.db.runScalarQuery(SQL, db)
    return queueId

# Fetch the queue  id given the Queue Key 
def getQueueForPost(post, db = ''):
    SQL = "select QueueKey from QueueMaster QM, TkPost P where P.MessageQueueId = QM.QueueId and Post = '%s'" % (post)
    queueKey = system.db.runScalarQuery(SQL, db)
    return queueKey

def getQueueForDiagnosticApplication(applicationName, db = ''):
    SQL = "select QueueKey from QueueMaster QM, DtApplication A "\
        "where A.MessageQueueId = QM.QueueId and ApplicationName = '%s'" % (applicationName)
    queueKey = system.db.runScalarQuery(SQL, db)
    return queueKey

# Get the names of all current queues
def getQueueNames(db = ''):
    SQL = "select QueueKey from QueueMaster"
    results = system.db.runQuery(SQL, db)
    names = list()
    for row in results:
        names.append(row[0])
    return names
