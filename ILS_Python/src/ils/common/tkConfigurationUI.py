'''
Created on Feb 25, 2017

@author: phass
'''

import system

def internalFrameOpened(rootContainer, db=""):
    tabStrip = rootContainer.getComponent("Tab Strip")
    tabStrip.selectedTab = "Units"
    
    txId = rootContainer.txId
    if txId != "":
        try:
            system.db.rollbackTransaction(txId)
            system.db.closeTransaction(txId)
        except:
            print "Caught an exception clearing the transaction"
        
    txId = system.db.beginTransaction(db,timeout=300000)
    rootContainer.txId = txId
    
    refreshUnits(rootContainer)
    refreshPosts(rootContainer)
    refreshConsoles(rootContainer)
    refreshLogbooks(rootContainer)

'''
Unit Related Functions
'''

def refreshUnits(rootContainer):
    txId = rootContainer.txId
    SQL = "select * from TkUnitView order by UnitName"
    pds= system.db.runQuery(SQL, tx=txId)
    table = rootContainer.getComponent("Units Container").getComponent("Power Table")
    table.data = pds

def addUnit(table):
    rootContainer = table.parent.parent
    txId = rootContainer.txId
    
    # Get a default post (the first one that comes up
    SQL = "select PostId, Post from TkPost"
    pds = system.db.runQuery(SQL, tx=txId)
    if len(pds) == 0:
        system.gui.warningBox("Please configure the Post table first!")
        raise ValueError, "No posts are defined"
    record=pds[0]
    postId = record["PostId"]
    post = record["Post"]
    
    table.data = system.dataset.addRow(table.data, [-1,None, None,None,postId,post])


def deleteUnit(table):
    rootContainer = table.parent.parent
    txId = rootContainer.txId
    selectedRow = table.selectedRow
    if selectedRow < 0:
        return
    ds = table.data
    unitId = ds.getValueAt(selectedRow, "UnitId")
    if unitId > 0:
        SQL = "delete from TkUnit where UnitId = %s" % (str(unitId))
        system.db.runUpdateQuery(SQL, tx=txId)
        
    ds = system.dataset.deleteRow(ds, selectedRow)
    table.data = ds

def unitEdited(table, rowIndex, colIndex, colName, oldValue, newValue):
    rootContainer = table.parent.parent
    txId = rootContainer.txId
    print "Something was edited"
    ds = table.data
    unitId = ds.getValueAt(rowIndex, "UnitId")
    if unitId < 0:
        ds = system.dataset.setValue(ds, rowIndex, colIndex, newValue)
        print "New row in row: ", rowIndex
        unitName = ds.getValueAt(rowIndex, "UnitName")
        unitAlias = ds.getValueAt(rowIndex, "UnitAlias")
        unitPrefix = ds.getValueAt(rowIndex, "UnitPrefix")
        post = ds.getValueAt(rowIndex, "Post")
        print unitName, unitAlias, unitPrefix, post
        if unitName <> "" and unitName <> None:
            postId = getPostId(post, txId)
            SQL = "Insert into TkUnit (UnitName, UnitPrefix, UnitAlias, PostId) values ('%s', '%s', '%s', %s)" % (unitName, unitPrefix, unitAlias, str(postId))
            unitId = system.db.runUpdateQuery(SQL, getKey=True, tx=txId)
            ds = system.dataset.setValue(ds, rowIndex, "UnitId", unitId)
            print "Inserted a new Unit with id: %d" % (unitId)
        else:
            print "UnitName is required"
        
    else:
        if colName == "Post":
            postId = getPostId(newValue, txId)
            if postId > 0 and postId <> None:
                SQL = "update TkUnit set PostId = %s where UnitId = %s" % (postId, str(unitId))
                rows = system.db.runUpdateQuery(SQL, tx=txId)
                print "Updated %d rows" % (rows)
            else:
                raise ValueError, "Unable to find Id for Post <%s>" % (newValue)
                
        else:
            SQL = "update TkUnit set %s = '%s' where UnitId = %s" % (colName, newValue, str(unitId))
            rows = system.db.runUpdateQuery(SQL, tx=txId)
            print "Updated %d rows" % (rows)
    
    table.data = system.dataset.setValue(ds, rowIndex, colIndex, newValue)

'''
Post Processing
'''
def refreshPosts(rootContainer):
    txId = rootContainer.txId
    SQL = "select * from TkPostView order by Post"
    pds= system.db.runQuery(SQL, tx=txId)
    table = rootContainer.getComponent("Posts Container").getComponent("Power Table")
    table.data = pds

def addPost(table):
    rootContainer = table.parent.parent
    txId = rootContainer.txId
    
    # Get a default Queue (the first one that comes up
    pds = system.db.runQuery("select QueueId, QueueKey from QueueMaster", tx=txId)
    if len(pds) == 0:
        system.gui.warningBox("Please configure the Queue table first!")
        raise ValueError, "No Queues are defined"
    record=pds[0]
    queueKey = record["QueueKey"]
    queueId = record["QueueId"]
    
    # Get a default Logbook (the first one that comes up
    pds = system.db.runQuery("select LogbookId, LogbookName from TkLogbook", tx=txId)
    if len(pds) == 0:
        system.gui.warningBox("Please configure the Logbook table first!")
        raise ValueError, "No logbooks are defined"
    record=pds[0]
    logbookId = record["LogbookId"]
    logbookName = record["LogbookName"]

    table.data = system.dataset.addRow(table.data, [-1,None, queueId, queueKey, logbookId, logbookName, False])

def deletePost(table):
    rootContainer = table.parent.parent
    txId = rootContainer.txId
    selectedRow = table.selectedRow
    if selectedRow < 0:
        return
    ds = table.data
    postId = ds.getValueAt(selectedRow, "PostId")
    if postId > 0:
        SQL = "delete from TkPost where PostId = %s" % (str(postId))
        system.db.runUpdateQuery(SQL, tx=txId)

    ds = system.dataset.deleteRow(ds, selectedRow)
    table.data = ds

def postEdited(table, rowIndex, colIndex, colName, oldValue, newValue):
    rootContainer = table.parent.parent
    txId = rootContainer.txId
    ds = table.data
    postId = ds.getValueAt(rowIndex, "PostId")
    if postId < 0:
        ds = system.dataset.setValue(ds, rowIndex, colIndex, newValue)
        print "New row in row: ", rowIndex
        post = ds.getValueAt(rowIndex, "Post")
        queueId = ds.getValueAt(rowIndex, "QueueId")
        logbookId = ds.getValueAt(rowIndex, "LogbookId")
        if post <> "" and post <> None:
            postId = system.db.runPrepUpdate("Insert into TkPost (Post, MessageQueueId, LogbookId, DownloadActive) values (?, ?, ?, 0)", [post, queueId, logbookId], getKey=True, tx=txId)
            ds = system.dataset.setValue(ds, rowIndex, "PostId", postId)
            print "Inserted a new Post with id: %d" % (postId)
        else:
            print "Post is required"
        
    else:
        if colName == "QueueKey":
            messageQueueId = getQueueId(newValue, txId)
            if messageQueueId > 0 and messageQueueId <> None:
                SQL = "update TkPost set MessageQueueId = %s where PostId = %s" % (str(messageQueueId), str(postId))
                rows = system.db.runUpdateQuery(SQL, tx=txId)
                print "Updated %d rows" % (rows)
            else:
                raise ValueError, "Unable to find Id for Queue <%s>" % (newValue)
        
        elif colName == "logbookName":
            logbookId = getLogbookId(newValue, txId)
            if logbookId > 0 and logbookId <> None:
                SQL = "update TkPost set LogbookId = %s where PostId = %s" % (str(logbookId), str(postId))
                rows = system.db.runUpdateQuery(SQL, tx=txId)
                print "Updated %d rows" % (rows)
            else:
                raise ValueError, "Unable to find Id for Logbook <%s>" % (newValue)
                
        else:
            SQL = "update TkPost set %s = '%s' where PostId = %s" % (colName, newValue, str(postId))
            rows = system.db.runUpdateQuery(SQL, tx=txId)
            print "Updated %d rows" % (rows)
    
    table.data = system.dataset.setValue(ds, rowIndex, colIndex, newValue)
    
'''
Console Processing
'''
def refreshConsoles(rootContainer):
    txId = rootContainer.txId
    SQL = "select * from TkConsoleView order by ConsoleName"
    pds= system.db.runQuery(SQL, tx=txId)
    table = rootContainer.getComponent("Consoles Container").getComponent("Power Table")
    table.data = pds

def addConsole(table):
    rootContainer = table.parent.parent
    txId = rootContainer.txId
    
    # Get a default post (the first one that comes up
    SQL = "select PostId, Post from TkPost"
    pds = system.db.runQuery(SQL, tx=txId)
    if len(pds) == 0:
        system.gui.warningBox("Please configure the Post table first!")
        raise ValueError, "No posts are defined"
    record=pds[0]
    postId = record["PostId"]
    post = record["Post"]
    
    table.data = system.dataset.addRow(table.data, [-1, None, "", 1, postId, post])

def deleteConsole(table):
    rootContainer = table.parent.parent
    txId = rootContainer.txId
    selectedRow = table.selectedRow
    if selectedRow < 0:
        return
    ds = table.data
    consoleId = ds.getValueAt(selectedRow, "ConsoleId")
    if consoleId > 0:
        SQL = "delete from TkConsole where ConsoleId = %s" % (str(consoleId))
        rows = system.db.runUpdateQuery(SQL, tx=txId)
        
    table.data = system.dataset.deleteRow(ds, selectedRow)

def consoleEdited(table, rowIndex, colIndex, colName, oldValue, newValue):
    rootContainer = table.parent.parent
    txId = rootContainer.txId
    ds = table.data
    consoleId = ds.getValueAt(rowIndex, "ConsoleId")
    if consoleId < 0:
        ds = system.dataset.setValue(ds, rowIndex, colIndex, newValue)
        print "New row in row: ", rowIndex
        consoleName = ds.getValueAt(rowIndex, "ConsoleName")
        windowName = ds.getValueAt(rowIndex, "WindowName")
        priority = ds.getValueAt(rowIndex, "Priority")
        post = ds.getValueAt(rowIndex, "Post")
        postId = getPostId(post, txId)
        if consoleName <> "" and consoleName <> None:
            consoleId = system.db.runPrepUpdate("Insert into TkConsole (ConsoleName, WindowName, Priority, PostId) values (?, ?, ?, ?)", [consoleName, windowName, priority, postId], getKey=True, tx=txId)
            ds = system.dataset.setValue(ds, rowIndex, "ConsoleId", consoleId)
            print "Inserted a new Console with id: %d" % (consoleId)
        else:
            print "ConsoleName is required"
        
    else:
        if colName == "Post":
            postId = getPostId(newValue, txId)
            if postId > 0 and postId <> None:
                SQL = "update TkConsole set PostId = %s where ConsoleId = %s" % (str(postId), str(consoleId))
                rows = system.db.runUpdateQuery(SQL, tx=txId)
                print "Updated %d rows" % (rows)
            else:
                raise ValueError, "Unable to find Id for Post <%s>" % (newValue)
                
        else:
            SQL = "update TkConsole set %s = ? where ConsoleId = %s" % (colName, str(consoleId))
            rows = system.db.runPrepUpdate(SQL, [newValue], tx=txId)
            print "Updated %d rows" % (rows)
    
    table.data = system.dataset.setValue(ds, rowIndex, colIndex, newValue)

'''
Logbook Processing
'''
def refreshLogbooks(rootContainer):
    txId = rootContainer.txId
    SQL = "select * from TkLogbook order by LogbookName"
    pds= system.db.runQuery(SQL, tx=txId)
    table = rootContainer.getComponent("Logbook Container").getComponent("Power Table")
    table.data = pds

def addLogbook(table):
    ds = table.data
    if ds.rowCount == 0:
        # take extra care to add the first row
        ds = system.dataset.toDataSet(["LogbookId", "LogbookName", "LogbookFilename"], [[-1, None, None]])
        table.data = ds
    else:
        table.data = system.dataset.addRow(table.data, [-1, None, None])

def deleteLogbook(table):
    rootContainer = table.parent.parent
    txId = rootContainer.txId
    selectedRow = table.selectedRow
    if selectedRow < 0:
        return
    ds = table.data
    logbookId = ds.getValueAt(selectedRow, "LogbookId")
    if logbookId > 0:
        SQL = "delete from TkLogbook where LogbookId = %s" % (str(logbookId))
        system.db.runUpdateQuery(SQL, tx=txId)

    ds = system.dataset.deleteRow(ds, selectedRow)
    table.data = ds

def logbookEdited(table, rowIndex, colIndex, colName, oldValue, newValue):
    rootContainer = table.parent.parent
    txId = rootContainer.txId
    ds = table.data
    logbookId = ds.getValueAt(rowIndex, "LogbookId")
    if logbookId < 0:
        ds = system.dataset.setValue(ds, rowIndex, colIndex, newValue)
        print "New row in row: ", rowIndex
        logbookName = ds.getValueAt(rowIndex, "LogbookName")
        logbookFilename = ds.getValueAt(rowIndex, "LogbookFilename")
        if logbookName <> "" and logbookName <> None and logbookName <> "<logbook name>":
            logbookId = system.db.runPrepUpdate("Insert into TkLogbook (LogbookName, LogbookFilename) values (?, ?)", [logbookName, logbookFilename], getKey=True, tx=txId)
            ds = system.dataset.setValue(ds, rowIndex, "LogbookId", logbookId)
            print "Inserted a new Logbook with id: %d" % (logbookId)
        else:
            print "Logbook Name is required"
        
    else:
        rows = system.db.runPrepUpdate("update TkLogbook set %s = ? where LogbookId = %s" % (colName, str(logbookId)), [newValue], tx=txId)
        print "Updated %d rows" % (rows)
    
    table.data = system.dataset.setValue(ds, rowIndex, colIndex, newValue)


'''
End of Life Processing
'''
    
def cancelCallback(event):
    print "Cancelling..."
    rootContainer=event.source.parent
    try:
        txId = rootContainer.txId
        system.db.rollbackTransaction(txId)
        system.db.closeTransaction(txId)
    except:
        print "Caught an error closing the transaction"
        
    rootContainer.txId = ""
    closeWindow(event)
    
def okCallback(event):
    print "OK..."
    rootContainer=event.source.parent
    applyCallback(event)
    txId = rootContainer.txId
    system.db.closeTransaction(txId)
    rootContainer.txId = ""
    closeWindow(event)
    
    
def applyCallback(event):
    print "Apply..."
    rootContainer=event.source.parent
    txId = rootContainer.txId
    system.db.commitTransaction(txId)

# Close the window unless we are in designer
def closeWindow(event):
    flags = system.util.getSystemFlags()
    isDesigner = flags & 1
    if not(isDesigner):
        system.nav.closeParentWindow(event)

'''
Helpers - These are sort of duplicates of helpers that already exist but these take a transaction id
'''
# Lookup the post id given the name
def getPostId(post, txId):
    pds = system.db.runPrepQuery("select PostId from TkPost where Post = ?", [post], tx=txId)
    return pds[0][0]

# Lookup the unit id given the name
def getUnitId(unitName, txId):
    pds = system.db.runPrepQuery("select UnitId from TkUnit where UnitName = ?", [unitName], tx=txId)
    return pds[0][0]

# Lookup the unit id given the name
def getQueueId(queueKey, txId):
    pds = system.db.runPrepQuery("select QueueId from QueueMaster where QueueKey = ?", [queueKey], tx=txId)
    return pds[0][0]

# Lookup the unit id given the name
def getLogbookId(logbookName, txId):
    pds = system.db.runPrepQuery("select LogbookId from TkLogbook where LogbookName = ?", [logbookName], tx=txId)
    return pds[0][0]