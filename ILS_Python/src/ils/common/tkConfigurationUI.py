'''
Created on Feb 25, 2017

@author: phass
'''


import system

def internalFrameOpened(rootContainer, db=""):
    tabStrip = rootContainer.getComponent("Tab Strip")
    tabStrip.selectedTab = "Queues"
    
    refreshPositions(rootContainer)
    refreshUnits(rootContainer)
    refreshPosts(rootContainer)
    refreshConsoles(rootContainer)
    refreshLogbooks(rootContainer)
    refreshQueues(rootContainer)
    refreshLookups(rootContainer)
    refreshLookupValues(rootContainer.getComponent("Lookup Container"))
    
'''
Lookup Related Functions
'''

def refreshLookups(rootContainer):
    SQL = "select * from LookupType order by LookupTypeName"
    pds= system.db.runQuery(SQL)
    table = rootContainer.getComponent("Lookup Container").getComponent("Lookup Type Table")
    table.data = pds
    
def addLookupType(container):
    print "In addLookupType()"
    
    lookupTypeCode = system.gui.inputBox("Enter new Lookup Type Code:")
    if lookupTypeCode == None:
        return
    
    SQL = "insert into LookupType (LookupTypeCode, LookupTypeName) values ('%s', '%s')" % (lookupTypeCode, lookupTypeCode)
    system.db.runUpdateQuery(SQL)
    refreshLookups(container.parent)
    refreshLookupValues(container)

def deleteLookupType(container):
    print "In deleteLookupType()"
    
    lookupTypeTable = container.getComponent("Lookup Type Table")
    lookupTypeCode = lookupTypeTable.data.getValueAt(lookupTypeTable.selectedRow, 0)

    SQL = "delete from LookupType where LookupTypeCode = '%s'" % (lookupTypeCode)
    system.db.runUpdateQuery(SQL)
    
    refreshLookups(container.parent)
    refreshLookupValues(container)

def saveLookupType(table, row):
    print "In saveLookupType()"
    
    ds = table.data
    lookupTypeCode = ds.getValueAt(row, 0)
    lookupTypeName = ds.getValueAt(row, 1)
    lookupTypeDescription = ds.getValueAt(row, 2)
    
    SQL = "update LookupType set LookupTypeName = '%s', LookupTypeDescription = '%s' where LookupTypeCode = '%s'" % (lookupTypeName, lookupTypeDescription, lookupTypeCode)
    print SQL
    system.db.runUpdateQuery(SQL)
    
    refreshLookups(table.parent.parent)


def refreshLookupValues(container):
    print "In fetchLookupValues()... "
    
    lookupTypeTable = container.getComponent("Lookup Type Table")
    lookupTable = container.getComponent("Lookup Table")
    
    if lookupTypeTable.selectedRow < 0:
        ds = lookupTable.data
        for row in range(ds.rowCount):
            ds = system.dataset.deleteRow(ds, 0)
        lookupTable.data = ds
    
    else:
        lookupTypeCode = lookupTypeTable.data.getValueAt(lookupTypeTable.selectedRow, 0)
    
        SQL = "select * from Lookup where LookupTypeCode = '%s'" % (lookupTypeCode) 
        pds = system.db.runQuery(SQL)
        lookupTable.data = pds
    
def addLookup(container):
    print "In addLookup()"
    
    lookup = system.gui.inputBox("Enter new Lookup :")
    if lookup == None:
        return
    
    lookupTypeTable = container.getComponent("Lookup Type Table")
    lookupTypeCode = lookupTypeTable.data.getValueAt(lookupTypeTable.selectedRow, 0)
    
    SQL = "insert into Lookup (LookupTypeCode, LookupName, Active) values ('%s', '%s', 1)" % (lookupTypeCode, lookup)
    system.db.runUpdateQuery(SQL)
    
    refreshLookupValues(container)

def deleteLookup(container):
    print "In deleteLookup()"
    
    lookupTable = container.getComponent("Lookup Table")
    lookupId = lookupTable.data.getValueAt(lookupTable.selectedRow, 0)
    
    SQL = "delete from Lookup where LookupId = %s" % (str(lookupId))
    system.db.runUpdateQuery(SQL)
    
    refreshLookupValues(container)

def saveLookup(table, row):
    print "In saveLookup(), row %d was edited..." % (row)
    
    ds = table.data
    lookupId = ds.getValueAt(row, 0)
    lookupName = ds.getValueAt(row, 2)
    lookupDescription = ds.getValueAt(row, 3)
    active = ds.getValueAt(row, 4)
    
    SQL = "update Lookup set LookupName = '%s', LookupDescription = '%s', active = %d where LookupId = %d" % (lookupName, lookupDescription, active, lookupId)
    print SQL
    system.db.runUpdateQuery(SQL)
    
    refreshLookupValues(table.parent)


'''
Unit Related Functions
'''

def refreshPositions(rootContainer):
    SQL = "select LookupName from Lookup where LookupTypeCode = 'WindowPosition' order by LookupName"
    pds= system.db.runQuery(SQL)
    rootContainer.queuePositions = pds

def refreshUnits(rootContainer):
    SQL = "select * from TkUnitView order by UnitName"
    pds= system.db.runQuery(SQL)
    table = rootContainer.getComponent("Units Container").getComponent("Power Table")
    table.data = pds

def addUnit(table):
    # Get a default post (the first one that comes up
    SQL = "select PostId, Post from TkPost"
    pds = system.db.runQuery(SQL)
    if len(pds) == 0:
        system.gui.warningBox("Please configure the Post table first!")
        raise ValueError, "No posts are defined"
    record=pds[0]
    postId = record["PostId"]
    post = record["Post"]
    
    table.data = system.dataset.addRow(table.data, [-1,None, None,None,postId,post])


def deleteUnit(table):
    selectedRow = table.selectedRow
    if selectedRow < 0:
        return
    ds = table.data
    unitId = ds.getValueAt(selectedRow, "UnitId")
    if unitId > 0:
        SQL = "delete from TkUnit where UnitId = %s" % (str(unitId))
        system.db.runUpdateQuery(SQL)

    ds = system.dataset.deleteRow(ds, selectedRow)
    table.data = ds

def unitEdited(table, rowIndex, colIndex, colName, oldValue, newValue):
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
            postId = getPostId(post)
            SQL = "Insert into TkUnit (UnitName, UnitPrefix, UnitAlias, PostId) values ('%s', '%s', '%s', %s)" % (unitName, unitPrefix, unitAlias, str(postId))
            unitId = system.db.runUpdateQuery(SQL, getKey=True)
            ds = system.dataset.setValue(ds, rowIndex, "UnitId", unitId)
            print "Inserted a new Unit with id: %d" % (unitId)
        else:
            print "UnitName is required"
        
    else:
        if colName == "Post":
            postId = getPostId(newValue)
            if postId > 0 and postId <> None:
                SQL = "update TkUnit set PostId = %s where UnitId = %s" % (postId, str(unitId))
                rows = system.db.runUpdateQuery(SQL)
                print "Updated %d rows" % (rows)
            else:
                raise ValueError, "Unable to find Id for Post <%s>" % (newValue)
                
        else:
            SQL = "update TkUnit set %s = '%s' where UnitId = %s" % (colName, newValue, str(unitId))
            rows = system.db.runUpdateQuery(SQL)
            print "Updated %d rows" % (rows)
    
    table.data = system.dataset.setValue(ds, rowIndex, colIndex, newValue)

'''
Post Processing
'''
def refreshPosts(rootContainer):
    SQL = "select * from TkPostView order by Post"
    pds= system.db.runQuery(SQL)
    table = rootContainer.getComponent("Posts Container").getComponent("Power Table")
    table.data = pds

def addPost(table):
    # Get a default Queue (the first one that comes up
    pds = system.db.runQuery("select QueueId, QueueKey from QueueMaster")
    if len(pds) == 0:
        system.gui.warningBox("Please configure the Queue table first!")
        raise ValueError, "No Queues are defined"
    record=pds[0]
    queueKey = record["QueueKey"]
    queueId = record["QueueId"]
    
    # Get a default Logbook (the first one that comes up
    pds = system.db.runQuery("select LogbookId, LogbookName from TkLogbook")
    if len(pds) == 0:
        system.gui.warningBox("Please configure the Logbook table first!")
        raise ValueError, "No logbooks are defined"
    record=pds[0]
    logbookId = record["LogbookId"]
    logbookName = record["LogbookName"]

    table.data = system.dataset.addRow(table.data, [-1,None, queueId, queueKey, logbookId, logbookName, False])

def deletePost(table):
    selectedRow = table.selectedRow
    if selectedRow < 0:
        return
    ds = table.data
    postId = ds.getValueAt(selectedRow, "PostId")
    
    if postId > 0:
    
        '''
        Check for Foreign Key constraints that do not have cascade deletes defined.
        I intentionally do not have cascade deletes to prevent accidental deletion of key components.
        '''
        SQL = "select count(*) from LtDisplayTable where PostId = %s" % (str(postId))
        cnt = system.db.runScalarQuery(SQL)
        if cnt > 0:
            system.gui.messageBox("<HTML>Unable to delete this post because it is referenced by a Lab Data display table.<br>All references in Lab Data <b>MUST</b> be removed before the post can be deleted!")
            return;
        
        SQL = "select count(*) from RtRecipeFamily where PostId = %s" % (str(postId))
        cnt = system.db.runScalarQuery(SQL)
        if cnt > 0:
            system.gui.messageBox("<HTML>Unable to delete this post because it is referenced by a Recipe Family.<br>All references in recipe <b>MUST</b> be removed before the post can be deleted!<br>Use DB Manager to delete the post reference!")
            return;
    
        SQL = "select count(*) from SfcControlPanel where PostId = %s" % (str(postId))
        cnt = system.db.runScalarQuery(SQL)
        if cnt > 0:
            system.gui.messageBox("<HTML>Unable to delete this post because it is referenced by a SFC control panel.<br>All references in SfcControlPanel <b>MUST</b> be removed before the post can be deleted!<br>Use SQL*Server to delete the post reference in SfcControlPanel!")
            return;
    
        SQL = "delete from TkPost where PostId = %s" % (str(postId))
        system.db.runUpdateQuery(SQL)

    ds = system.dataset.deleteRow(ds, selectedRow)
    table.data = ds

def postEdited(table, rowIndex, colIndex, colName, oldValue, newValue):
    ds = table.data
    postId = ds.getValueAt(rowIndex, "PostId")
    if postId < 0:
        ds = system.dataset.setValue(ds, rowIndex, colIndex, newValue)
        print "New row in row: ", rowIndex
        post = ds.getValueAt(rowIndex, "Post")
        queueId = ds.getValueAt(rowIndex, "QueueId")
        logbookId = ds.getValueAt(rowIndex, "LogbookId")
        if post <> "" and post <> None:
            postId = system.db.runPrepUpdate("Insert into TkPost (Post, MessageQueueId, LogbookId, DownloadActive) values (?, ?, ?, 0)", [post, queueId, logbookId], getKey=True)
            ds = system.dataset.setValue(ds, rowIndex, "PostId", postId)
            print "Inserted a new Post with id: %d" % (postId)
        else:
            print "Post is required"
        
    else:
        if colName == "QueueKey":
            messageQueueId = getQueueId(newValue)
            if messageQueueId > 0 and messageQueueId <> None:
                SQL = "update TkPost set MessageQueueId = %s where PostId = %s" % (str(messageQueueId), str(postId))
                rows = system.db.runUpdateQuery(SQL)
                print "Updated %d rows" % (rows)
            else:
                raise ValueError, "Unable to find Id for Queue <%s>" % (newValue)
        
        elif colName == "logbookName":
            logbookId = getLogbookId(newValue)
            if logbookId > 0 and logbookId <> None:
                SQL = "update TkPost set LogbookId = %s where PostId = %s" % (str(logbookId), str(postId))
                rows = system.db.runUpdateQuery(SQL)
                print "Updated %d rows" % (rows)
            else:
                raise ValueError, "Unable to find Id for Logbook <%s>" % (newValue)
                
        else:
            SQL = "update TkPost set %s = '%s' where PostId = %s" % (colName, newValue, str(postId))
            rows = system.db.runUpdateQuery(SQL)
            print "Updated %d rows" % (rows)
    
    table.data = system.dataset.setValue(ds, rowIndex, colIndex, newValue)
    
'''
Console Processing
'''
def refreshConsoles(rootContainer):
    SQL = "select * from TkConsoleView order by ConsoleName"
    pds= system.db.runQuery(SQL)
    table = rootContainer.getComponent("Consoles Container").getComponent("Power Table")
    table.data = pds

def addConsole(table):
    # Get a default post (the first one that comes up
    SQL = "select PostId, Post from TkPost"
    pds = system.db.runQuery(SQL)
    if len(pds) == 0:
        system.gui.warningBox("Please configure the Post table first!")
        raise ValueError, "No posts are defined"
    record=pds[0]
    postId = record["PostId"]
    post = record["Post"]
    
    table.data = system.dataset.addRow(table.data, [-1, None, "", 1, postId, post])

def deleteConsole(table):
    selectedRow = table.selectedRow
    if selectedRow < 0:
        return
    ds = table.data
    consoleId = ds.getValueAt(selectedRow, "ConsoleId")
    if consoleId > 0:
        SQL = "delete from TkConsole where ConsoleId = %s" % (str(consoleId))
        rows = system.db.runUpdateQuery(SQL)
        print "Deleted %d rows" % (rows)
        
    table.data = system.dataset.deleteRow(ds, selectedRow)

def consoleEdited(table, rowIndex, colIndex, colName, oldValue, newValue):
    ds = table.data
    consoleId = ds.getValueAt(rowIndex, "ConsoleId")
    if consoleId < 0:
        ds = system.dataset.setValue(ds, rowIndex, colIndex, newValue)
        print "New row in row: ", rowIndex
        consoleName = ds.getValueAt(rowIndex, "ConsoleName")
        windowName = ds.getValueAt(rowIndex, "WindowName")
        priority = ds.getValueAt(rowIndex, "Priority")
        post = ds.getValueAt(rowIndex, "Post")
        postId = getPostId(post)
        if consoleName <> "" and consoleName <> None:
            consoleId = system.db.runPrepUpdate("Insert into TkConsole (ConsoleName, WindowName, Priority, PostId) values (?, ?, ?, ?)", [consoleName, windowName, priority, postId], getKey=True)
            ds = system.dataset.setValue(ds, rowIndex, "ConsoleId", consoleId)
            print "Inserted a new Console with id: %d" % (consoleId)
        else:
            print "ConsoleName is required"
        
    else:
        if colName == "Post":
            postId = getPostId(newValue)
            if postId > 0 and postId <> None:
                SQL = "update TkConsole set PostId = %s where ConsoleId = %s" % (str(postId), str(consoleId))
                rows = system.db.runUpdateQuery(SQL)
                print "Updated %d rows" % (rows)
            else:
                raise ValueError, "Unable to find Id for Post <%s>" % (newValue)
                
        else:
            SQL = "update TkConsole set %s = ? where ConsoleId = %s" % (colName, str(consoleId))
            rows = system.db.runPrepUpdate(SQL, [newValue])
            print "Updated %d rows" % (rows)
    
    table.data = system.dataset.setValue(ds, rowIndex, colIndex, newValue)

'''
Logbook Processing
'''
def refreshLogbooks(rootContainer):
    SQL = "select * from TkLogbook order by LogbookName"
    pds= system.db.runQuery(SQL)
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
    selectedRow = table.selectedRow
    if selectedRow < 0:
        return
    ds = table.data
    logbookId = ds.getValueAt(selectedRow, "LogbookId")
    if logbookId > 0:
        SQL = "delete from TkLogbook where LogbookId = %s" % (str(logbookId))
        system.db.runUpdateQuery(SQL)

    ds = system.dataset.deleteRow(ds, selectedRow)
    table.data = ds

def viewLogbook(table):
    selectedRow = table.selectedRow
    if selectedRow < 0:
        return
    ds = table.data
    logbookName = ds.getValueAt(selectedRow, "LogbookName")
    if logbookName <> "":        
        from java.util import Calendar
        cal = Calendar.getInstance()
        cal.set(Calendar.HOUR_OF_DAY, 0)
        cal.set(Calendar.MINUTE, 0)
        cal.set(Calendar.SECOND, 0)
        cal.set(Calendar.MILLISECOND, 0)
        startDate = cal.getTime()
        
        cal.set(Calendar.HOUR_OF_DAY, 23)
        cal.set(Calendar.MINUTE, 59)
        endDate = cal.getTime()

        print "Opening logbook: ", logbookName 
        win = system.nav.openWindowInstance('Logbook/Logbook Viewer', {"logbook": logbookName, "startDate": startDate, "endDate": endDate})
        system.nav.centerWindow(win)
        

def logbookEdited(table, rowIndex, colIndex, colName, oldValue, newValue):
    ds = table.data
    logbookId = ds.getValueAt(rowIndex, "LogbookId")
    if logbookId < 0:
        ds = system.dataset.setValue(ds, rowIndex, colIndex, newValue)
        print "New row in row: ", rowIndex
        logbookName = ds.getValueAt(rowIndex, "LogbookName")
        logbookFilename = ds.getValueAt(rowIndex, "LogbookFilename")
        if logbookName <> "" and logbookName <> None and logbookName <> "<logbook name>":
            logbookId = system.db.runPrepUpdate("Insert into TkLogbook (LogbookName, LogbookFilename) values (?, ?)", [logbookName, logbookFilename], getKey=True)
            ds = system.dataset.setValue(ds, rowIndex, "LogbookId", logbookId)
            print "Inserted a new Logbook with id: %d" % (logbookId)
        else:
            print "Logbook Name is required"
        
    else:
        rows = system.db.runPrepUpdate("update TkLogbook set %s = ? where LogbookId = %s" % (colName, str(logbookId)), [newValue])
        print "Updated %d rows" % (rows)
    
    table.data = system.dataset.setValue(ds, rowIndex, colIndex, newValue)

'''
Queue Processing
'''
def refreshQueues(rootContainer):
    SQL = "select QueueId, QueueKey, Title, CheckpointTimestamp, Position, AutoViewSeverityThreshold, AutoViewAdmin, AutoViewAE, AutoViewOperator"\
        " from QueueMaster order by QueueKey"

    pds= system.db.runQuery(SQL)
    table = rootContainer.getComponent("Queues Container").getComponent("Power Table")
    table.data = pds

def addQueue(table):
    ds = table.data
    if ds.rowCount == 0:
        # take extra care to add the first row
        ds = system.dataset.toDataSet(["QueueId", "QueueKey", "Title", "CheckpointTimestamp","Position", "AutoViewSeverityThreshold", "AutoViewAdmin", "AutoViewAE", "AutoViewOperator"], 
                                      [[-1, None, None, None, False, 10, False, False, False]])
        table.data = ds
    else:
        table.data = system.dataset.addRow(table.data, [-1, None, None, None, False, 10, False, False, False])

def deleteQueue(table):
    selectedRow = table.selectedRow
    if selectedRow < 0:
        return
    ds = table.data
    queueId = ds.getValueAt(selectedRow, "QueueId")
    if queueId > 0:
        SQL = "delete from QueueMaster where QueueId = %s" % (str(queueId))
        system.db.runUpdateQuery(SQL)

    ds = system.dataset.deleteRow(ds, selectedRow)
    table.data = ds


def viewQueue(table):
    selectedRow = table.selectedRow
    if selectedRow < 0:
        return
    ds = table.data
    queueKey = ds.getValueAt(selectedRow, "QueueKey")
    if queueKey <> "":
        from ils.queue.message import view
        view(queueKey, useCheckpoint=True)


def queueEdited(table, rowIndex, colIndex, colName, oldValue, newValue):
    ds = table.data
    queueId = ds.getValueAt(rowIndex, "QueueId")
    if queueId < 0:
        ds = system.dataset.setValue(ds, rowIndex, colIndex, newValue)
        print "New row in row: ", rowIndex
        queueKey = ds.getValueAt(rowIndex, "QueueKey")
        title = ds.getValueAt(rowIndex, "Title")
        if queueKey == None:
            system.gui.messageBox("Queue Key is required")
        else:
            if title == None:
                title = queueKey + " Console Queue"
                ds = system.dataset.setValue(ds, rowIndex, "Title", title)
                
            queueId = system.db.runPrepUpdate("Insert into QueueMaster (QueueKey, Title) values (?, ?)", [queueKey, title], getKey=True)
            ds = system.dataset.setValue(ds, rowIndex, "QueueId", queueId)
            print "Inserted a new Queue with id: %d" % (queueId)
        
    else:
        rows = system.db.runPrepUpdate("update QueueMaster set %s = ? where QueueId = %s" % (colName, str(queueId)), [newValue])
        print "Updated %d rows" % (rows)
    
    table.data = system.dataset.setValue(ds, rowIndex, colIndex, newValue)


'''
Helpers - These are sort of duplicates of helpers that already exist but these take a transaction id
'''
# Lookup the post id given the name
def getPostId(post):
    pds = system.db.runPrepQuery("select PostId from TkPost where Post = ?", [post])
    return pds[0][0]

# Lookup the unit id given the name
def getUnitId(unitName):
    pds = system.db.runPrepQuery("select UnitId from TkUnit where UnitName = ?", [unitName])
    return pds[0][0]

# Lookup the unit id given the name
def getQueueId(queueKey):
    pds = system.db.runPrepQuery("select QueueId from QueueMaster where QueueKey = ?", [queueKey])
    return pds[0][0]

# Lookup the unit id given the name
def getLogbookId(logbookName):
    pds = system.db.runPrepQuery("select LogbookId from TkLogbook where LogbookName = ?", [logbookName])
    return pds[0][0]