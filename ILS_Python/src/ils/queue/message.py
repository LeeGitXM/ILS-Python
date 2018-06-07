'''
Created on Sep 9, 2014

@author: ILS
'''
import  system, string
from ils.queue.constants import QUEUE_DETAIL_MESSAGE_LENGTH
from ils.common.error import catchError
from ils.common.config import getDatabaseClient
from ils.common.windowUtil import positionWindow
from system.ils.blt.diagram import getProductionDatabase
from ils.common.user import isAE, isOperator, isAdmin
log = system.util.getLogger("com.ils.queue")

def insertPostMessage(post, status, message, db='', project='', console=''):
    from ils.queue.commons import getQueueForPost
    queueKey=getQueueForPost(post)
    
    if queueKey == None:
        log.warn("Unable to insert a message into queue for post <%s> (key: <%s>" % (post, str(queueKey)))
        return
    
    insert(queueKey, status, message, db, project, console)

# Expected status are Info, Warning, or Error
def insert(queueKey, status, message, db='', project='', console=''):
    from ils.queue.commons import getQueueId
    queueId = getQueueId(queueKey, db)
    
    if queueId == None:
        log.warn("Unable to insert a message into queue with key <%s> and id: <%s>" % (queueKey, str(queueId)))
        return
    
    _insert(queueKey, queueId, status, message, db, project)


# Expected status are Info, Warning, or Error
def _insert(queueKey, queueId, status, message, db='', project=''):
    from ils.common.util import escapeSqlQuotes
    message = escapeSqlQuotes(message)
    SQL = "select statusId, severity from QueueMessageStatus where MessageStatus = '%s'" % (status)
    pds = system.db.runQuery(SQL, db)
    if len(pds) <> 1:
        return
    
    record = pds[0]
    statusId = record["statusId"]
    severity = record["severity"]
    
    message=message[:QUEUE_DETAIL_MESSAGE_LENGTH - 2]
    SQL = "insert into QueueDetail (QueueId, Timestamp, StatusId, Message) values (%s, getdate(), %s, '%s')" % (str(queueId), str(statusId), message)

    system.db.runUpdateQuery(SQL, db)
    
    autoView(queueKey, queueId, severity, project, db)


def autoView(queueKey, queueId, severity, project, db):
    SQL = "select autoViewSeverityThreshold, autoViewAdmin, autoViewAE, autoViewOperator from QueueMaster where queueId = %d" % (queueId)
    pds = system.db.runQuery(SQL, db)
    if len(pds) <> 1:
        return
    
    record = pds[0]
    autoViewSeverityThreshold = record["autoViewSeverityThreshold"]
    autoViewAdmin = record["autoViewAdmin"]
    autoViewAE = record["autoViewAE"]
    autoViewOperator = record["autoViewOperator"]

    log.tracef("The message severity is %f and the autoViewSeverityThreshold is %f", severity, autoViewSeverityThreshold)

    if severity >= autoViewSeverityThreshold:
        log.tracef("The view should be auto posted...")
        sendOpenMessage(queueKey, autoViewAdmin, autoViewAE, autoViewOperator, db, project)

    else:
        log.tracef("The view should NOT be auto posted")


def queueSQL(queueKey, useCheckpoint, order, db =''):
    
    SQL = "select checkpointTimestamp from QueueMaster where QueueKey = '%s'" % (queueKey)
    checkPointTimestamp = system.db.runScalarQuery(SQL, db)
    
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

    '''
    If the filename contains a * then replace it with the datetime.
    '''
    if filepath.find('*') > -1:
        # Get the timestamp formatted for including in a filename
#        from ils.common.util import getDate
#        theDate = getDate()
        theDate = system.date.now()
    
        from ils.common.util import formatDateTime
        theDate = formatDateTime(theDate, 'yyyy-MM-dd-hh-mm-ss')
        print "The timestamp is: ", theDate

        filepath = string.replace(filepath, '*', theDate)
        print "The new filename is: ", filepath

    SQL = queueSQL(queueKey, useCheckpoint, "ASC", db)
    pds = system.db.runQuery(SQL, db)
    
    # Note: Noetpad does not recognize \n as a carriage return but worpad does.
    
    try:
        header = "Created,Severity,Message\n"
        system.file.writeFile(filepath, header, False)
        
        for record in pds:
            txt = str(record["Timestamp"]) + "," + record["Status"] + "," + record["Message"] + "\n"
            system.file.writeFile(filepath, txt, True)
    except:
        txt = catchError("Error saving message queue <%s> to <%s>" % (queueKey, filepath))
        log.error(txt)

def clear(queueKey, db = ''):
    from ils.queue.commons import getQueueId
    queueId = getQueueId(queueKey, db)
    
    if queueId == None:
        log.warn("Unable to clear queue with key <%s> and id: <%s>" % (queueKey, str(queueId)))
        return
    
    SQL = "update QueueMaster set CheckpointTimestamp = getdate() where QueueId = %i" % (queueId)

    system.db.runUpdateQuery(SQL, db)


'''
This is called in client scope, generally from a button 
'''
def view(queueKey, useCheckpoint=False, silent=False, position="", scale=1.0):
    
    db = getDatabaseClient()
    
    if position == "":
        SQL = "select Position from QueueMaster where QueueKey = '%s'" % (queueKey)
        position = system.db.runScalarQuery(SQL, database=db)
        print "Using the position from QueueMaster: %s" % (position)
        
    #just to make sure it's set to something :-)
    if position == "":
        position = "center"
    

    windowName = 'Queue/Message Queue'
    
    # First check if this queue is already displayed
    windows = system.gui.findWindow(windowName)
    for window in windows:
        qk = window.rootContainer.key
        print "found a window with key: ", qk
        if qk == queueKey:
            window.toFront()
            system.nav.centerWindow(window)
            if silent == False:
                system.gui.messageBox("The queue is already open!")
            return

    print "Opening a queue window..."
    window=system.nav.openWindowInstance(windowName, {'key': queueKey, 'useCheckpoint': useCheckpoint})
    positionWindow(window, position, scale)
    

def initializeView(rootContainer, db=""):
    queueKey = rootContainer.getPropertyValue("key")
    
    SQL = "select Title from QueueMaster where QueueKey = '%s'" % (queueKey)
    pds = system.db.runQuery(SQL, db)
    
    if len(pds) == 1:
        record = pds[0]
        title = record['Title']
        rootContainer.setPropertyValue('title', title) 

    table = rootContainer.getComponent("Power Table")
    for messageStatus in ['Info', 'Warning', 'Error']:
        SQL = "select color from QueueMessageStatus where messageStatus = '%s'" % (messageStatus)
        color = system.db.runScalarQuery(SQL, db)
        
        if messageStatus == 'Info':
            table.setPropertyValue('infoColor', color)
        elif messageStatus == 'Warning':
            table.setPropertyValue('warningColor', color)
        elif messageStatus == 'Error':
            table.setPropertyValue('errorColor', color)


def updateView(rootContainer, db=""):
    table = rootContainer.getComponent('Power Table')
    queueKey = rootContainer.key
    useCheckpoint = rootContainer.useCheckpoint
    
    SQL = queueSQL(queueKey, useCheckpoint, "DESC")
    pds = system.db.runQuery(SQL, db)
    table.data = pds

def initializeSuperView(rootContainer):
    listWidget = rootContainer.getComponent('List')
    listWidget.selectedIndex = -1

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

def updateSuperView(rootContainer):
    listWidget = rootContainer.getComponent('List')
    table = rootContainer.getComponent('Power Table')
    
    startDate = rootContainer.getComponent('Start Date').date
    endDate = rootContainer.getComponent('End Date').date
    
    queueKeys=listWidget.getSelectedValues()
    queueKeys="','".join(map(str,queueKeys))
    
    SQL = "select Timestamp, M.QueueKey, MessageStatus as Status, Message "\
        " from QueueDetail D, QueueMaster M, QueueMessageStatus QMS " \
        " where M.QueueKey in ('%s') "\
        " and M.QueueId = D.QueueId "\
        " and D.StatusId = QMS.StatusId " \
        " and Timestamp > ? and Timestamp < ?" \
        " order by Timestamp DESC" % (queueKeys)
            
    print SQL
    
    pds = system.db.runPrepQuery(SQL, [startDate, endDate])
    table.data = pds

def messageDetail(txt):
    windowName = 'Queue/Message Detail'

    print "Opening a queue window..."
    window=system.nav.openWindowInstance(windowName, {'txt': txt})
    system.nav.centerWindow(window)

'''
Send a message to every client to open the message queue if they are interested in the console.
The idea is that a client can determine on its own if it is interested in this queue without considering any other clients.
This will not work from gateway scope.
'''
def sendOpenMessage(queueKey, autoViewAdmin, autoViewAE, autoViewOperator, db, project=''):
    if project == '':
        project = system.util.getProjectName()

    handler = "showQueue"
    payload = {"queueKey": queueKey, "database": db, "autoViewAdmin": autoViewAdmin, "autoViewAE": autoViewAE, "autoViewOperator": autoViewOperator}
    system.util.sendMessage(project, handler, payload, "C")

'''
This runs in every client and is called by the messageHandler script for a showQueue message
'''
def handleMessage(payload):
    print "Handling a showQueue message with payload: ", payload

    queueKey = payload["queueKey"]
    db = payload["database"]
    if db == "":
        db = getProductionDatabase()
    
    clientDB = getDatabaseClient()
    if clientDB <> db:
        print "Not showing the queue because the client database does not match the queue database!"
        return
    
    autoViewAdmin = payload["autoViewAdmin"]
    autoViewAE = payload["autoViewAE"]
    autoViewOperator = payload["autoViewOperator"]
    
    if autoViewAdmin and isAdmin():
        print "Autoshowing because this queue is autoView enabled for Admins and this is an Admin"
        view(queueKey, useCheckpoint=True, silent=True)
        return

    if autoViewAE and isAE():
        print "Autoshowing because this queue is autoView enabled for AEs and this is an AE"
        view(queueKey, useCheckpoint=True, silent=True)
        return
    
    if autoViewOperator and isOperator():
        print "Autoshowing because this queue is autoView enabled for Operators and this is an Operator"
        view(queueKey, useCheckpoint=True, silent=True)
        return
    
    print "The queue will NOT be autoshown"