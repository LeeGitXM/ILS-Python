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

# Write the contents of the queu to a file

def save(queueKey, useCheckpoint, filepath, db = ''):

    if useCheckpoint:
        SQL = "select Timestamp, MessageStatus as Status, Message "\
            " from QueueDetail D, QueueMaster M, QueueMessageStatus QMS " \
            " where M.QueueKey = '%s' "\
            " and M.QueueId = D.QueueId "\
            " and D.StatusId = QMS.StatusId " \
            " and D.Timestamp > M.CheckpointTimestamp "\
            " order by Timestamp DESC" % (queueKey)
    else:
        SQL = "select top 1000 Timestamp, MessageStatus as Status, Message "\
            " from QueueDetail D, QueueMaster M, QueueMessageStatus QMS " \
            " where M.QueueKey = '%s' "\
            " and M.QueueId = D.QueueId "\
            " and D.StatusId = QMS.StatusId " \
            " order by Timestamp DESC" % (queueKey)
     
    print SQL
    pds = system.db.runQuery(SQL)
    
    header = "Created,Severity,Message\n"
    system.file.writeFile(filepath, header, False)
    
    for record in pds:
        txt = str(record["Timestamp"]) + "," + record["Status"] + "," + record["Message"] + "\n"
        system.file.writeFile(filepath, txt, True)
        

def clear(queueKey, db = ''):
    from ils.queue.commons import getQueueId
    queueId = getQueueId(queueKey, db)

    SQL = "update QueueMaster set CheckpointTimestamp = getdate() where QueueId = %i" % (queueId)

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

def updateView(rootContainer):
    table = rootContainer.getComponent('Power Table')
    queueKey = rootContainer.key
    useCheckpoint = rootContainer.useCheckpoint
    
    if useCheckpoint:
        SQL = "select Timestamp, MessageStatus as Status, '<HTML>' + Message as Message "\
            " from QueueDetail D, QueueMaster M, QueueMessageStatus QMS " \
            " where M.QueueKey = '%s' "\
            " and M.QueueId = D.QueueId "\
            " and D.StatusId = QMS.StatusId " \
            " and D.Timestamp > M.CheckpointTimestamp "\
            " order by Timestamp DESC" % (queueKey)
    else:
        SQL = "select top 1000 Timestamp, MessageStatus as Status, '<HTML>' + Message as Message "\
            " from QueueDetail D, QueueMaster M, QueueMessageStatus QMS " \
            " where M.QueueKey = '%s' "\
            " and M.QueueId = D.QueueId "\
            " and D.StatusId = QMS.StatusId " \
            " order by Timestamp DESC" % (queueKey)

    pds = system.db.runQuery(SQL)
    table.data = pds
    
     