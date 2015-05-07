'''
Created on Sep 9, 2014

@author: ILS
'''
import system

def insert(message, database=""):
    queue = "Logfile"
    _insert(queue, message, database)

def _insert(queue, message, database=""):
    from ils.queue.commons import getQueueId
    queueId = getQueueId(queue, database)

    SQL = "select StatusId from QueueMessageStatus where MessageStatus = 'Info'"
    statusId = system.db.runScalarQuery(SQL, database)
    
    SQL = "insert into QueueDetail (QueueId, Timestamp, StatusId, Message) values (%i, getdate(), %i, '%s')" % (queueId, statusId, message)
    system.db.runUpdateQuery(SQL, database)

def initializeView(rootContainer):
    queueKey = rootContainer.getPropertyValue("key")
    
    SQL = "select * from QueueMaster where QueueKey = '%s'" % (queueKey)
    pds = system.db.runQuery(SQL)
    
    if len(pds) == 1:
        record = pds[0]
        title = record['Title']
        rootContainer.setPropertyValue('title', title) 

    print "Done initializing"
