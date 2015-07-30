'''
Created on Sep 9, 2014

@author: ILS
'''
import  system, string

# Insert / post a message to a queue from an SFC.
# If the queueKey if left blank then the current default queue for the unit procedure is used.
# Expected status are Info, Warning, or Error
def post(chartScope, status, message, queueKey=""):
    from ils.sfc.gateway.api import getCurrentMessageQueue
    from ils.sfc.common.util import getDatabaseName
    
    # If the queue was not specified then use the current default queue
    if queueKey == "":
        queueKey=getCurrentMessageQueue(chartScope)

    db=getDatabaseName(chartScope)
    insert(queueKey, status, message, db)

# Expected status are Info, Warning, or Error
def insert(queueKey, status, message, db = ''):
    from ils.queue.commons import getQueueId
    queueId = getQueueId(queueKey, db)

    SQL = "select statusId from QueueMessageStatus where MessageStatus = '%s'" % (status)
    statusId = system.db.runScalarQuery(SQL, db)
    
    SQL = "insert into QueueDetail (QueueId, Timestamp, StatusId, Message) values (%s, getdate(), %s, '%s')" % (str(queueId), str(statusId), message)

    system.db.runUpdateQuery(SQL, db)

# This version of the insert stems from translation of "build-msg-on-wksp"
def insertFromWorkspace(message,color,x,y,wksp):
    status   = 'Info'
    queueKey = 'default'
    insert(queueKey,status,message)
    return 200,10  # Width, height - not used

def queueSQL(queueKey, useCheckpoint, order):
    
    SQL = "select checkpointTimestamp from QueueMaster where QueueKey = '%s'" % (queueKey)
    checkPointTimestamp = system.db.runScalarQuery(SQL)
    
    # Power tables handle wrap text without doing anything special, so no need to add <HTML>
    if useCheckpoint and checkPointTimestamp != None:
        SQL = "select Timestamp, MessageStatus as Status, Message "\
            " from QueueDetail D, QueueMaster M, QueueMessageStatus QMS " \
            " where M.QueueKey = '%s' "\
            " and M.QueueId = D.QueueId "\
            " and D.StatusId = QMS.StatusId " \
            " and D.Timestamp >= M.CheckpointTimestamp "\
            " order by Timestamp %s" % (queueKey, order)
    else:
        SQL = "select top 1000 Timestamp, MessageStatus as Status, Message "\
            " from QueueDetail D, QueueMaster M, QueueMessageStatus QMS " \
            " where M.QueueKey = '%s' "\
            " and M.QueueId = D.QueueId "\
            " and D.StatusId = QMS.StatusId " \
            " order by Timestamp %s" % (queueKey, order)
    # This fills up the console by printing every few seconds!!
    # print SQL
    return SQL 
            
# Write the contents of the queue to a file
def save(queueKey, useCheckpoint, filepath, db = ''):

    if filepath.find('*') > -1:
        # Get the timestamp formatted for including in a filename
        from ils.common.util import getDate
        theDate = getDate()
    
        from ils.common.util import formatDateTime
        theDate = formatDateTime(theDate, 'yyyy-MM-dd-hh-mm-ss')
        print "The timestamp is: ", theDate

        filepath = string.replace(filepath, '*', theDate)
        print "The new filename is: ", filepath



    SQL = queueSQL(queueKey, useCheckpoint, "ASC")
    pds = system.db.runQuery(SQL, db)
    
    # Note: Noetpad does not recognize \n as a carriage return but worpad does.
    
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


def view(queueKey, useCheckpoint=False):
    windowName = 'Queue/Message Queue'
    
    # First check if this queue is already displayed
    windows = system.gui.findWindow(windowName)
    for window in windows:
        qk = window.rootContainer.key
        print "found a window with key: ", qk
        if qk == queueKey:
            system.nav.centerWindow(window)
            system.gui.messageBox("The queue is already open!")
            return

    print "Opening a queue window..."
    window=system.nav.openWindowInstance(windowName, {'key': queueKey, 'useCheckpoint': useCheckpoint})
    system.nav.centerWindow(window)
    

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
    
#    ds = table.columnAttributesData
#    ds=system.dataset.setValue(ds, 0, "", 20)
#    table.columnAttributesData = ds
    print "Done initializing"

def updateView(rootContainer):
    table = rootContainer.getComponent('Power Table')
    queueKey = rootContainer.key
    useCheckpoint = rootContainer.useCheckpoint
    
    SQL = queueSQL(queueKey, useCheckpoint, "DESC")
    pds = system.db.runQuery(SQL)
    table.data = pds
    