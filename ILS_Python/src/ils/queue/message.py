'''
Created on Sep 9, 2014

@author: ILS
'''
import  system

def insert(queueKey, status, message, db = ''):
    from ils.queue.commons import getQueueId
    queueId = getQueueId(queueKey, db)

    SQL = "select statusId from QueueMessageStatus where MessageStatus = '%s'" % (status)
    statusId = system.db.runScalarQuery(SQL, db)
    
    SQL = "insert into QueueDetail (QueueId, Timestamp, StatusId, Message) values (%s, getdate(), %s, '%s')" % (str(queueId), str(statusId), message)

    system.db.runUpdateQuery(SQL, db)

def clear(queueKey, db = ''):
    from ils.queue.commons import getQueueId
    queueId = getQueueId(queueKey, db)

    SQL = "delete from QueueDetail where QueueId = %i" % (queueId)
    system.db.runUpdateQuery(SQL, db)

def initializeView(rootContainer):
    queueKey = rootContainer.getPropertyValue("key")
    
    SQL = "select Title from QueueMaster where QueueKey = '%s'" % (queueKey)
    print SQL
    pds = system.db.runQuery(SQL)
    
    if len(pds) == 1:
        record = pds[0]
        title = record['Title']
        print "title: ", title
        rootContainer.setPropertyValue('title', title) 

    table = rootContainer.getComponent("Power Table")
    for messageStatus in ['Info', 'Warning', 'Error']:
        SQL = "select color from QueueMessageStatus where messageStatus = '%s'" % (messageStatus)
        color = system.db.runScalarQuery(SQL)
        
        if messageStatus == 'Info':
            table.setPropertyValue('infoColor', color)
        elif messageStatus == 'Warning':
            table.setPropertyValue('warningColor', color)
        elif messageStatus == 'Error':
            table.setPropertyValue('errorColor', color)
    
    print "Done initializing"