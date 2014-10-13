'''
Created on Sep 9, 2014

@author: ILS
'''
import system

# Fetch the queue  id given the Queue Key 
def getQueueId(queueKey, db = ''):
    SQL = "select id from QueueMaster where QueueKey = '%s'" % (queueKey)
    queueId = system.db.runScalarQuery(SQL, db)
    return queueId