'''
Created on Mar 29, 2015

@author: Pete
'''
import system, string
import ils.common.util as util
from ils.config.client import getTagProvider, getDatabase
from ils.io.util import readTag
from ils.labData.scanner import simulateReadRaw
from ils.log import getLogger
log = getLogger(__name__)

# This is called from the button on the data table chooser screen.  We want to allow multiple lab data table screens,
# but not multiple screens showing the same table.
def launcher(displayTableTitle):
    log.infof("In %s.launcher()...", __name__)

    # Check to see if this lab table is already open
    windowName = 'Lab Data/Lab Data Viewer'
    
    # First check if this queue is already displayed
    windows = system.gui.findWindow(windowName)
    print "Found %d lab data viewer windows" % (len(windows))
    for window in windows:
        print "Window: ", window
        windowDisplayTableTitle = window.rootContainer.displayTableTitle
        log.tracef("...found a window with key: %s", windowDisplayTableTitle)
        if windowDisplayTableTitle == displayTableTitle:
            system.nav.centerWindow(window)
            system.gui.messageBox("The lab table is already open!")
            return

    window = system.nav.openWindowInstance(windowName, {'displayTableTitle' : displayTableTitle})
    system.nav.centerWindow(window)
    

# Initialize the lab data viewer page with all of the parameters that are defined for 
# this page.  There is really only one component on this window - the template repeater.
# Once the repeater is configured, each component in the repeater knows how to configure itself.
def internalFrameActivated(event):
    log.infof("In %s.internalFrameActivated()", __name__)
    rootContainer = event.source.rootContainer
    displayTableTitle = rootContainer.displayTableTitle
    log.tracef("The table being displayed is: %s", displayTableTitle)
    
    SQL = "select V.ValueName LabValueName, V.ValueId, V.Description, V.DisplayDecimals "\
        " from LtValue V, LtDisplayTable DT, LtDisplayTableDetails DTD "\
        " where DT.displayTableId = DTD.DisplayTableId "\
        " and DTD.valueId = V.ValueId "\
        " and DT.DisplayTableTitle = '%s' "\
        " order by DTD.DisplayOrder" % (displayTableTitle)
    log.tracef(SQL)
    pds = system.db.runQuery(SQL)
    ds = system.dataset.toDataSet(pds)
    for row in range(ds.rowCount):
        if ds.getValueAt(row, "Description") in [None, ""]:
            valueName = ds.getValueAt(row, "LabValueName")
            ds = system.dataset.setValue(ds, row, "Description", valueName)
             
        log.tracef("%s %s %s %s",ds.getValueAt(row, "LabValueName"), ds.getValueAt(row, "ValueId"), ds.getValueAt(row, "Description"), ds.getValueAt(row, "DisplayDecimals"))
    
    repeater=rootContainer.getComponent("Template Repeater")
    repeater.templateParams=ds

    log.tracef("...leaving internalFrameActivated()!")

'''
This runs in client scope and is called from a client message handler...
'''
def newLabDataMessageHandler(payload):
    log.tracef("In %s.newLabDataMessageHandler() - Handling a new lab data message...", __name__)
    db = getDatabase()
    
    windows = system.gui.getOpenedWindows()
    for window in windows:
        windowPath = window.getPath()
        if windowPath == "Lab Data/Lab Data Viewer":
            rootContainer = window.rootContainer
            log.tracef("-------------------")
            log.tracef("There is an open lab data viewer titled: %s", rootContainer.displayTableTitle)
            
            repeater = rootContainer.getComponent("Template Repeater")
            
            templateList = repeater.getLoadedTemplates()
            
            for template in templateList:
                log.tracef("  Processing %s", template.LabValueName)
                configureLabDatumTable(template, db)

#  This configures the table inside the template that is in the repeater.  It is called by the container AND by the timer 
def configureLabDatumTable(container, db):
    username = system.security.getUsername()
    log.tracef("In %s.configureLabDatumTable(), checking for lab data viewed by %s", __name__, username)
    valueName=container.LabValueName
    valueDescription=container.Description
    displayDecimals=container.DisplayDecimals
    log.tracef("Configuring the Lab Datum Viewer table for %s", valueName)
    
    from ils.labData.common import fetchValueId
    valueId = fetchValueId(valueName, db)
        
    SQL = "select top 13 RawValue as '%s', SampleTime, ReportTime, HistoryId "\
        " from LtHistory "\
        " where ValueId = %i "\
        " order by SampleTime desc" % (valueName, valueId)
    log.tracef(SQL)
    pds = system.db.runQuery(SQL, database=db)
    
    SQL = "Select ViewTime from LtValueViewed where ValueId = %i and Username = '%s'" % (valueId, username)
    lastViewedTime = system.db.runScalarQuery(SQL, database=db)

    header = [str(valueDescription), 'seen', 'historyId']
    log.tracef("Fetched %d rows, the header is %s", len(pds),  str(header))
    data = []
    tableData = []
    newestHistoryId=-1
    for record in pds:
        historyId = record['HistoryId']
        reportTime = record['ReportTime']
        
        if newestHistoryId == -1:
            container.NewestHistoryId=historyId
        
        val = record[valueName]
        
        if displayDecimals == 0:
            val = "%.0f" % (val)
        elif displayDecimals == 1:
            val = "%.1f" % (val)
        elif displayDecimals == 2:
            val = "%.2f" % (val)
        elif displayDecimals == 3:
            val = "%.3f" % (val)
        elif displayDecimals == 4:
            val = "%.4f" % (val)
        elif displayDecimals == 5:
            val = "%.5f" % (val)
        else:
            val = "%f" % (val)
            
        myDateString=system.db.dateFormat(record["SampleTime"], "HH:mm MM/d")
        val = "%s at %s" % (val, myDateString)
        
        if lastViewedTime == None or reportTime > lastViewedTime:
            seen = 0
        else:
            seen = 1
            
        data.append([val,seen, historyId])
        tableData.append([val])
    
    ds = system.dataset.toDataSet(header, data)
    container.data=ds

    # We need to update the column attribute dataset because we change the column name for every parameter and this 
    # freaks out the table widget (same is true for the power table).
    table=container.getComponent("Power Table")
    columnAttributesData=table.columnAttributesData
    columnAttributesData=system.dataset.setValue(columnAttributesData, 0, "name", valueName)
    columnAttributesData=system.dataset.setValue(columnAttributesData, 0, "label", valueDescription)
    table.columnAttributesData=columnAttributesData
    
    ds = system.dataset.toDataSet([str(valueDescription)], tableData)
    table.data=ds

# This is a pretty generic routine that I needed for Lab Data but it could be used anywhere.  Given a template repeater, it
# digs inside the repeater structure and returns a list of all the templates that are being repeated.  The caller can then iterate
# over the list to access any data inside the template that is needed.
def getTemplates(repeater, templateName):
    templates=[]
    aList = repeater.getComponents()
    for comp in aList:
        bList = comp.getComponents()
        for bComp in bList:
            cList = bComp.getComponents()
            for cComp in cList:
                dList = cComp.getComponents()
                for dComp in dList:
                    if dComp.name == templateName:
                        templates.append(dComp)
    return templates


# This is called when the lab data table window is closed.  As long as the window is open, then we want the rows highlighted. 
# They may want to add a button that calls this to make the red go away, but for now just call it when the window closes.
# The original implementation looked at the last value id for the value and then updated that value for the user as having been seen,
# but somehow that didn't work for Mike and he had rows in the middle that were red, so somehow things came in in some strange order.
def setSeen(rootContainer):
    log.tracef("In %s.labData.viewer.setSeen()...", __name__)
    username = system.security.getUsername()
    
    repeater=rootContainer.getComponent("Template Repeater")
    templates=getTemplates(repeater, "Lab Datum Viewer")

    for template in templates:
        valueId = template.getPropertyValue("ValueId")
        valueName = template.getPropertyValue("LabValueName")
        log.tracef("Processing values that have been seen for %s - %d by %s", valueName, valueId, username)
        
        # Get the id that is stored for this user and this value.
        SQL = "update LtValueViewed set ViewTime = getdate() where ValueId = %i and username = '%s' " % (valueId, username)
        rows = system.db.runUpdateQuery(SQL)
        
        if rows == 0:
            # If no rows were updated then do an insert
            SQL = "insert into LtValueViewed (ValueId, UserName, ViewTime) values (%i, '%s', getdate())" % (valueId, username)
            rows = system.db.runUpdateQuery(SQL)
            log.tracef("Inserted %i rows into LtValueViewed", rows)

    '''
    Send a message to every client to update their Lab Data Chooser so that red buttons can be turned grey.
    (Not sure if I should only update the local client, if so then use the client id in the message)
    '''
    project = system.util.getProjectName()
    system.util.sendMessage(project, messageHandler="newLabData", payload={}, scope="C")


'''
This is ALWAYS run from a client.  For now, the "Get History" button appears on every lab data table, regardless of its source,
even though it can only work for data that comes from PHD.  It can't work for DCS data, selectors, or derived values.
'''
def fetchHistory(container):
    valueName=container.LabValueName
    valueId=container.ValueId
    tagProvider = getTagProvider()
    db = getDatabase()
    
    log.tracef("In labData.viewer.fetchHistory(), fetching missing data for %s - %d", valueName, valueId)
    
    if system.tag.exists("[%s]Configuration/Common/simulateHDA" % (tagProvider)):
        simulateHDA = readTag("[%s]Configuration/Common/simulateHDA" % (tagProvider)).value
    else:
        simulateHDA = False
    
    log.tracef("Simulate: %s", str(simulateHDA))
    
    '''
    For now, "Get History" is not supported for derived lab values
    '''
    SQL = "Select * from LtDerivedValueView where ValueId = %i" % (valueId)
    pds = system.db.runQuery(SQL, database=db)
    
    if len(pds) > 0:
        log.tracef("The selected lab data is a derived value, Get History is not supported")
        system.gui.warningBox("%s is a derived value which does not support Get History!" % (valueName))
        return
    
    '''
    Handle Selectors by redirecting the query to the source value
    '''
    SQL = "Select SourceValueId, SourceValueName from LtSelectorView where ValueId = %i" % (valueId)
    pds = system.db.runQuery(SQL, database=db)
    
    if len(pds) > 0:
        valueName = pds[0]["SourceValueName"]
        valueId = pds[0]["SourceValueId"]
        log.tracef("The selected lab data is a selector, redirecting the fetch to the source lab data: %s - %s", valueName, str(valueId))
        if valueId == None:
            system.gui.warningBox("A source is not configured for this selector.")
            return
    
    SQL = "Select InterfaceName, ItemId, UnitName from LtPHDValueView where ValueId = %i" % (valueId)
    pds = system.db.runQuery(SQL, database=db)
    
    if len(pds) == 0:
        system.gui.warningBox("This lab data does not have history because it's source is not PHD!")
        return

    # If they choose a lab selector, should the request be transferred to the source of the selector?
    
    hdaInterface=pds[0]["InterfaceName"]
    itemId=pds[0]["ItemId"]
    unitName=pds[0]["UnitName"]
    maxValues=0
    boundingValues=0
    
    if simulateHDA:
        serverIsAvailable = True
    else:
        # Check that the HDA interface is healthy
        serverIsAvailable=system.opchda.isServerAvailable(hdaInterface)
        
    if not(serverIsAvailable):
        system.gui.warningBox("Unable to fetch history because the HDA interface <%s> is not available!" % (hdaInterface))
        return
    
    # Get the start and stop time for the query
    endDate = util.getDate()
    from java.util import Calendar
    cal = Calendar.getInstance()
 
    cal.setTime(endDate)
    cal.add(Calendar.HOUR, -24 * 14)
    startDate = cal.getTime()

    if simulateHDA:
        retVals = simulateReadRaw([itemId], startDate, endDate)
        valueList=retVals[0]
    else:
        retVals=system.opchda.readRaw(hdaInterface, [itemId], startDate, endDate, maxValues, boundingValues)
        log.tracef("...back from HDA read, read %d values!", len(retVals))
    
        # We are fetching the history for a single lab value.
        valueList=retVals[0]
    
        if str(valueList.serviceResult) != 'Good':
            system.gui.errorBox("The data returned from the PHD historian was %s --" % (valueList.serviceResult))
            return
    
        if valueList.size()==0:
            system.gui.warningBox("No data was found for %s" % (itemId))
            return
    
    # Use the current grade for all of the missing values
    tagProvider = getTagProvider()
    from ils.common.grade import getGradeForUnit
    grade=getGradeForUnit(unitName, tagProvider)

    # We found some data so now process it - we found data, but that doesn't mean it is new!
    rows=0
    for qv in valueList:
        print qv
        if simulateHDA:
            sampleTime = qv.get("timestamp", None)
            rawValue = qv.get("value", None)
            quality = qv.get("quality", None)
            if quality == "Good":
                isGood = True
            else:
                isGood = False
        else:
            sampleTime = qv.timestamp
            rawValue = qv.value
            quality = qv.quality
            isGood = quality.isGood()

        # Only process good values
        if isGood:
            # Before we insert it, see if it already exists
            SQL = "select HistoryId from LtHistory where ValueId = ? and RawValue = ? and SampleTime = ?"
            pds = system.db.runPrepQuery(SQL, [valueId, rawValue, sampleTime], database=db) 
            if len(pds) == 0:
                log.tracef("...Inserting a missing value: %s - %s - %s - %s", valueName, itemId, str(rawValue), str(sampleTime))
                
                # Insert the value into the lab history table.
                from ils.labData.scanner import insertHistoryValue
                success,insertedRows = insertHistoryValue(valueName, valueId, rawValue, sampleTime, grade, log, db)    
                if success:
                    rows = rows + insertedRows
        else:
            log.infof("skipping value because the value is bad!")

    if rows == 0:
        system.gui.messageBox("No new data was found!")
    else:
        configureLabDatumTable(container, db)
        system.gui.messageBox("%i new values were loaded!" % (rows))