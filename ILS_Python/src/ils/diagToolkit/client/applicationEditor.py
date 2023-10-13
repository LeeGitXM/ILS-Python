'''
Created on Apr 15, 2022

@author: ils
'''

import system
from ils.config.client import getDatabase
from ils.queue.commons import getQueueId
from ils.common.database import lookupIdFromKey, getUnitId
from ils.diagToolkit.common import fetchOutputsForApplication

from ils.log import getLogger
log = getLogger(__name__)

CONTAINER_WIDTH = 700
CONTAINER_HEIGHT = 400
CENTER_X = 0
CENTER_Y = 0
RIGHT_X = 700
DURATION = 500
MAX_INDEX = 4

def internalFrameOpened(event):
    log.infof("In %s.internalFrameOpened()", __name__)
    rootContainer = event.source.rootContainer
    resetPages(rootContainer)
    
    ''' Now reset various components '''
    outputList = rootContainer.getComponent("Page2").getComponent("List")
    outputList.selectedIndex = -1
    
    tagTree = rootContainer.getComponent("Page4").getComponent("Tag Browse Tree")
    ds = tagTree.selectedPaths
    ds = system.dataset.clearDataset(ds)
    tagTree.selectedPaths = ds
    
    ''' Refresh the window '''
    refresh(rootContainer)

'''
Page 1 button callbacks.
'''
def saveCallback(event):
    log.infof("In %s.saveCallback()", __name__)
    db = getDatabase()
    saved = save(event.source.parent.parent, db)
    if saved:
        system.nav.closeParentWindow(event)

def applyCallback(event):
    log.infof("In %s.apply()", __name__)
    db = getDatabase()
    save(event.source.parent.parent, db)
    
'''
Page 2 callbacks
'''
def editQuantOutputCallback(event):
    log.infof("In %s.editQuantOutputCallback()", __name__)
    editQuantOutput(event)
    pageLeft(event.source.parent.parent)

def addQuantOutputCallback(event):
    log.infof("In %s.addQuantOutputCallback()", __name__)
    createNewQuantOutput(event)
    pageLeft(event.source.parent.parent)
    
def deleteQuantOutputCallback(event):
    '''
    Remove the selected QuantOutput from the quantOutputNames and quantOutputs datasets on the 
    rootContainer.  This doesn't delete anything from the database, that will happen when they press SAVE. 
    '''
    log.infof("In %s.deleteQuantOutputCallback()", __name__)
    db = getDatabase()
    container = event.source.parent
    quantOutputlist = container.getComponent("List")
    row = quantOutputlist.selectedIndex
    rootContainer = container.parent
    applicationName = rootContainer.applicationName
    
    ''' 
    Fetch the id of the selected output - if we can't fetch an ID then it means that the output was just created and has not 
    been saved to the DB yet, so it is safe to delete and don't check for references.
    '''
    ds = rootContainer.quantOutputNames
    quantOutputName = ds.getValueAt(row, 0)
    SQL = "SELECT QuantOutputId from DtQuantOutputDefinitionView where ApplicationName = '%s' and QuantOutputName = '%s' " % (applicationName, quantOutputName)
    quantOutputId = system.db.runScalarQuery(SQL, database=db)
    if quantOutputId == None:
        log.infof("Deleting a new output that hasn't been added to the database yet")
    else:
        SQL = "select count(*) from DtRecommendationDefinition where QuantOutputId = %d" % (quantOutputId)
        referenceCount = system.db.runScalarQuery(SQL, database=db)
        if referenceCount > 0:
            system.gui.messageBox("Warning: Unable to delete %s because there are %d Final Diagnosis that reference it." % (quantOutputName, referenceCount))
            return
    
    confirmed = system.gui.confirm("Are you sure you want to delete output <%s>?" % (quantOutputName))
    if confirmed:
        ds = system.dataset.deleteRow(ds, row)
        rootContainer.quantOutputNames = ds
    
        ds = rootContainer.quantOutputs
        ds = system.dataset.deleteRow(ds, row)
        rootContainer.quantOutputs = ds

'''
Page 3 button callbacks
'''
def stashQuantOutputCallback(event):
    '''
    This is called by the "Left" button on Page 3 - the quant output editor screen.
    It stashes the values on the screen on the dataset - this does not update the database, that happens when the 
    user presses Save on the first screen. 
    '''
    log.infof("In %s.stashQuantOutputCallback()", __name__)
    container = event.source.parent
    rootContainer = container.parent
    mode = container.mode
    
    ''' Validate that the name is unique.  This is trickier than it sounds, we need to handle new inputs and editing an existing input. ''' 
    
    if mode == "add":
        ''' If they are adding a new output, but then decide not to, they need a way to get back. '''
        if container.quantOutputName == "":
            pageRight(rootContainer)
            return
    
        if container.tagPath == "":
            system.gui.messageBox("You must specify a tag path for the output!")
            return
        
        log.infof("Checking that the name is unique for a new input")
        ds = rootContainer.quantOutputNames
        for row in range(ds.rowCount):
            if ds.getValueAt(row, 0) == container.quantOutputName:
                system.gui.messageBox("The output name is not unique!")
                return
            
    elif mode == "edit":
        ''' Do some really basic validation '''
        if container.quantOutputName == "":
            system.gui.messageBox("You must specify at name for the output!")
            return
        
        if container.tagPath == "":
            system.gui.messageBox("You must specify a tag path for the output!")
            return
    
        outputList = rootContainer.getComponent("Page2").getComponent("List")
        selectedRow = outputList.selectedIndex
        ds = rootContainer.quantOutputNames

        for row in range(ds.rowCount):
            if row != selectedRow and ds.getValueAt(row, 0) == container.quantOutputName:
                system.gui.messageBox("The output name is not unique!")
                return
    
    ''' OK to save '''
   
    if mode == "edit":
        listWidget = rootContainer.getComponent("Page2").getComponent("List")
        row = listWidget.selectedIndex
        
        ds = rootContainer.quantOutputs
        ds = system.dataset.setValue(ds, row, "QuantOutputName", container.quantOutputName)
        ds = system.dataset.setValue(ds, row, "TagPath", container.tagPath)
        ds = system.dataset.setValue(ds, row, "MostNegativeIncrement", container.mostNegativeIncrement)
        ds = system.dataset.setValue(ds, row, "MostPositiveIncrement", container.mostPositiveIncrement)
        ds = system.dataset.setValue(ds, row, "MinimumIncrement", container.minimumIncrement)
        ds = system.dataset.setValue(ds, row, "SetpointHighLimit", container.setpointHighLimit)
        ds = system.dataset.setValue(ds, row, "SetpointLowLimit", container.setpointLowLimit)
        ds = system.dataset.setValue(ds, row, "IncrementalOutput", container.incrementalOutput)
        ds = system.dataset.setValue(ds, row, "FeedbackMethod", container.feedbackMethod)
        rootContainer.quantOutputs = ds
        
        ds = rootContainer.quantOutputNames
        ds = system.dataset.setValue(ds, row, 0, container.quantOutputName)
        rootContainer.quantOutputNames = ds
    else:
        ds = rootContainer.quantOutputs
        ds = system.dataset.addRow(ds, [-1, container.quantOutputName, container.tagPath, container.mostNegativeIncrement,
                container.mostPositiveIncrement, False, container.minimumIncrement, container.setpointHighLimit, container.setpointLowLimit,
                container.incrementalOutput, container.feedbackMethod])
        rootContainer.quantOutputs = ds
        
        ds = rootContainer.quantOutputNames
        ds = system.dataset.addRow(ds, [container.quantOutputName])
        rootContainer.quantOutputNames = ds
        
    pageRight(rootContainer)
    
        
def resetPages(rootContainer):
    '''
    Generally only called on internalFrameOpened() 
    '''
    log.infof("In %s.resetPages()", __name__)
    container = rootContainer.getComponent("Page1")
    system.gui.transform(container, newX=CENTER_X, newY=CENTER_Y, newWidth=CONTAINER_WIDTH, newHeight=CONTAINER_HEIGHT)
    container.visible = True
    
    for page in ["Page2", "Page3", "Page4"]:
        container = rootContainer.getComponent(page)
        container.visible = True
        system.gui.transform(container, newX=RIGHT_X, newY=CENTER_Y, newWidth=CONTAINER_WIDTH, newHeight=CONTAINER_HEIGHT)
    rootContainer.pageIndex = 1
    
def pageRight(rootContainer):
    '''
    Move the top page to the right
    '''
    log.infof("In %s.pageRight()", __name__)
    pageIndex = rootContainer.pageIndex
    if pageIndex == 0:
        system.gui.messageBox("No more pages")
        return
    
    container = rootContainer.getComponent("Page" + str(pageIndex))
    system.gui.transform(container, newX=RIGHT_X, duration=DURATION)
    rootContainer.pageIndex = pageIndex - 1

def pageLeft(rootContainer):
    log.infof("In %s.pageLeft()", __name__)
    pageIndex = rootContainer.pageIndex + 1
    if pageIndex > MAX_INDEX:
        system.gui.messageBox("No more pages")
        return
    
    container = rootContainer.getComponent("Page" + str(pageIndex))
    system.gui.transform(container, newX=CENTER_X, duration=DURATION)
    rootContainer.pageIndex = pageIndex

def refresh(rootContainer):
    '''
    Generally only called on internalFrameOpened() 
    '''
    db = getDatabase()
    applicationId = rootContainer.applicationId
    if applicationId > 0:
        SQL = "select ApplicationName, Description, UnitName, QueueKey, Managed, GroupRampMethodName "\
            " from DtApplicationView where ApplicationId = %d" % (applicationId)
        pds = system.db.runQuery(SQL, database=db)
        if len(pds) == 0:
            system.gui.messageBox("Error fetching family with id <%s>" % (str(applicationId)) )
            return
        
        record = pds[0]
        applicationName = record["ApplicationName"]
        rootContainer.applicationName = applicationName
        rootContainer.description = record["Description"]
        rootContainer.unitName = record["UnitName"]
        rootContainer.queueKey = record["QueueKey"]
        rootContainer.managed = record["Managed"]
        rootContainer.groupRampMethodName = record["GroupRampMethodName"]
        
        pds = fetchOutputsForApplication(applicationName, db)
        log.infof("fetched %d outputs...", len(pds))
        ds = system.dataset.toDataSet(pds)
        rootContainer.quantOutputs = ds

        quantOutputNames = []        
        for record in pds:
            quantOutputNames.append([record["QuantOutputName"]])
        ds = system.dataset.toDataSet(["QuantOutput"], quantOutputNames)
        rootContainer.quantOutputNames = ds
    else:
        log.infof("Editing a new application")
        rootContainer.applicationName = ""
        rootContainer.description = ""
        rootContainer.unitName = ""
        rootContainer.queueKey = ""
        rootContainer.managed = ""
        rootContainer.groupRampMethodName = ""
        
        ''' Clear the datasets '''
        ds = rootContainer.quantOutputs
        ds = system.dataset.clearDataset(ds)
        rootContainer.quantOutputs = ds

        ds = rootContainer.quantOutputNames
        ds = system.dataset.clearDataset(ds)
        rootContainer.quantOutputNames = ds
        

def save(rootContainer, db):
    log.infof("In %s.save()", __name__)
    applicationId = rootContainer.applicationId
    applicationName = rootContainer.applicationName
    description = rootContainer.description
    queueKey = rootContainer.queueKey
    groupRampMethodName = rootContainer.groupRampMethodName
    managed = rootContainer.managed
    unitName = rootContainer.unitName
    
    valid = validate(rootContainer, applicationName, queueKey, unitName, groupRampMethodName)
    if not(valid):
        return False
    
    messageQueueId = getQueueId(queueKey, db)
    groupRampMethodId = lookupIdFromKey("GroupRampMethod", groupRampMethodName, db)
    unitId = getUnitId(unitName, db)
    notificationStrategy = "ocAlert"
    
    if applicationId == -1:
        log.infof("Insert a new application")
        SQL = "insert  DtApplication (ApplicationName, Description, MessageQueueId, GroupRampMethodId, NotificationStrategy, UnitId, Managed) "\
            "values(?, ?, ?, ?, ?, ?, ?)"
        vals = [applicationName, description, messageQueueId, groupRampMethodId, notificationStrategy, unitId, managed]
        applicationId = system.db.runPrepUpdate(SQL, vals, database=db, getKey=True)
        rootContainer.applicationId = applicationId
        log.infof("Inserted application with id #%d", applicationId)
    else:
        log.infof("Update an existing application...")
        SQL = "update DtApplication set ApplicationName = ?, Description = ?, MessageQueueId = ?, GroupRampMethodId = ?, NotificationStrategy = ?, "\
            "UnitId = ?, Managed = ? where ApplicationId = ?"
        rows = system.db.runPrepUpdate(SQL, [applicationName, description, messageQueueId, groupRampMethodId, notificationStrategy, unitId, managed, applicationId], database=db)
        log.infof("Updated %d rows", rows)
        
    ''' 
    Update, insert, and delete the quant outputs 
    In order to do the delete, I need to check if there is a quantOutput in the database that is not in the table, use QuantOutputIds rather than names.
    '''
    log.infof("Updating Quant Outputs...")
    SQL = "SELECT QuantOutputId from DtQuantOutputDefinitionView where ApplicationName = '%s'" % (applicationName)
    pds = system.db.runQuery(SQL, database=db)
    quantOutputIdsInDatabase = []
    for record in pds:
        quantOutputIdsInDatabase.append(record["QuantOutputId"])

    ds = rootContainer.quantOutputs
    for row in range(ds.rowCount):
        quantOutputId = ds.getValueAt(row, "QuantOutputId")
        if quantOutputId in quantOutputIdsInDatabase:
            log.infof("Removing %s from the database list..", str(quantOutputId))
            quantOutputIdsInDatabase.remove(quantOutputId)
        quantOutputName = ds.getValueAt(row, "QuantOutputName")
        log.infof("Saving %s...", quantOutputName)
        tagPath = ds.getValueAt(row, "TagPath")
        mostNegativeIncrement = ds.getValueAt(row, "MostNegativeIncrement")
        mostPositiveIncrement = ds.getValueAt(row, "MostPositiveIncrement")
        ignoreMinimumIncrement = ds.getValueAt(row, "IgnoreMinimumIncrement")
        minimumIncrement = ds.getValueAt(row, "MinimumIncrement")
        setpointHighLimit = ds.getValueAt(row, "SetpointHighLimit")
        setpointLowLimit = ds.getValueAt(row, "SetpointLowLimit")
        incrementalOutput = ds.getValueAt(row, "IncrementalOutput")
        feedbackMethod = ds.getValueAt(row, "FeedbackMethod")
        
        feedbackMethodId = lookupIdFromKey("FeedbackMethod", feedbackMethod, db)
        
        if quantOutputId < 0:
            SQL = "Insert into DtQuantOutput(ApplicationId, QuantOutputName, TagPath, MostNegativeIncrement, MostPositiveIncrement, "\
                "IgnoreMinimumIncrement, MinimumIncrement, SetpointHighLimit, SetpointLowLimit, IncrementalOutput, FeedbackMethodId) values (?,?,?,?,?,?,?,?,?,?,?)"
            vals = [applicationId, quantOutputName, tagPath, mostNegativeIncrement, mostPositiveIncrement, ignoreMinimumIncrement, minimumIncrement, setpointHighLimit, 
                    setpointLowLimit, incrementalOutput, feedbackMethodId]
            quantOutputId = system.db.runPrepUpdate(SQL, vals, database=db, getKey=True)
            log.infof("...inserted new quant output <%s> and assigned id: %d!", quantOutputName, quantOutputId)
        else:
            SQL = "update DtQuantOutput set QuantOutputName=?, TagPath=?, MostNegativeIncrement=?, MostPositiveIncrement=?, IgnoreMinimumIncrement=?, "\
                " MinimumIncrement=?, SetpointHighLimit=?, SetpointLowLimit=?, IncrementalOutput=?, FeedbackMethodId=? where quantOutputId = ?"
            vals = [quantOutputName, tagPath, mostNegativeIncrement, mostPositiveIncrement, ignoreMinimumIncrement, minimumIncrement, setpointHighLimit, 
                    setpointLowLimit, incrementalOutput, feedbackMethodId, quantOutputId]
            rows = system.db.runPrepUpdate(SQL, vals, database=db)
            log.infof("...updated %d rows", rows)
    
    ''' Now remove any quant outputs from the database that were removed from editor '''
    for quantOutputId in quantOutputIdsInDatabase:
        log.infof("Delete %s from the database...", str(quantOutputId))
        SQL = "delete from DtQuantOutput where QuantOutputId = %d" % (quantOutputId)
        rows = system.db.runUpdateQuery(SQL, database=db)
        log.infof("...deleted %d rows!", rows)

    return True
        
def validate(rootContainer, applicationName, queueKey, unitName, groupRampMethodName):
    if applicationName == "":
        system.gui.messageBox("<HTML>You must specify an <b>Application Name</b>.")
        return False
    
    if queueKey == "":
        system.gui.messageBox("<HTML>You select a <b>Message Queue</b>.")
        return False

    if groupRampMethodName == "":
        system.gui.messageBox("<HTML>You select a <b>Ramp Method</b>.")
        return False

    if unitName == "":
        system.gui.messageBox("<HTML>You select a <b>Unit</b>.")
        return False
    
    return True


def editQuantOutput(event):
    '''
    There are two datasets: quantOutputs and quantOutputNames.
    There are in the same order so the same index can go back and forth.
    '''
    container = event.source.parent
    rootContainer = container.parent
    ds = rootContainer.quantOutputs
    page3Container = rootContainer.getComponent('Page3')

    listWidget = container.getComponent("List")
    if listWidget.selectedIndex >= 0:
        quantOutputName = ds.getValueAt(listWidget.selectedIndex, "QuantOutputName")
        page3Container.mode = "edit"
        page3Container.quantOutputName = quantOutputName
        page3Container.tagPath = ds.getValueAt(listWidget.selectedIndex, "TagPath")
        page3Container.mostPositiveIncrement = ds.getValueAt(listWidget.selectedIndex, "MostPositiveIncrement")
        page3Container.mostNegativeIncrement = ds.getValueAt(listWidget.selectedIndex, "MostNegativeIncrement")
        page3Container.minimumIncrement = ds.getValueAt(listWidget.selectedIndex, "MinimumIncrement")
        page3Container.setpointHighLimit = ds.getValueAt(listWidget.selectedIndex, "SetpointHighLimit")
        page3Container.setpointLowLimit = ds.getValueAt(listWidget.selectedIndex, "SetpointLowLimit")
        page3Container.incrementalOutput = ds.getValueAt(listWidget.selectedIndex, "IncrementalOutput")
        page3Container.feedbackMethod = ds.getValueAt(listWidget.selectedIndex, "FeedbackMethod")

def createNewQuantOutput(event):
    '''
    There are two datasets: quantOutputs and quantOutputNames.
    There are in the same order so the same index can go back and forth.
    '''
    container = event.source.parent
    rootContainer = container.parent
    page3Container = rootContainer.getComponent('Page3')

    quantOutputName = ""
    page3Container.mode = "add"
    page3Container.quantOutputName = quantOutputName
    page3Container.tagPath = ""
    page3Container.mostPositiveIncrement = 10.0
    page3Container.mostNegativeIncrement = -10.0
    page3Container.minimumIncrement = 0.5
    page3Container.setpointHighLimit = 1000.0
    page3Container.setpointLowLimit = -1000.0
    page3Container.incrementalOutput = True
    page3Container.feedbackMethod = "Average"
    