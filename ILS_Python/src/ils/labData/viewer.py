'''
Created on Mar 29, 2015

@author: Pete
'''
import system
import ils.common.util as util
from com.sun.org.apache.xalan.internal import templates

# This is called from the button on the data table chooser screen.  We want to allow multiple lab data table screens,
# but not multiple screens showing the same table.
def launcher(displayTableTitle):
    print "Launching..."

    # Check to see if this lab table is already open
    windowName = 'Lab Data/Lab Data Viewer'
    
    # First check if this queue is already displayed
    windows = system.gui.findWindow(windowName)
    for window in windows:
        windowDisplayTableTitle = window.rootContainer.displayTableTitle
        print "found a window with key: ", windowDisplayTableTitle
        if windowDisplayTableTitle == displayTableTitle:
            system.nav.centerWindow(window)
            system.gui.messageBox("The lab table is already open!")
            return

    window = system.nav.openWindowInstance(windowName, {'displayTableTitle' : displayTableTitle})
    system.nav.centerWindow(window)
    

# Initialize the lab data viewer page with all of the parameters that are defined for 
# this page.  There is really only one component on this window - the template repeater.
# Once the repeater is configured, each component in the repeater knows how to configure itself.
def internalFrameActivated(rootContainer):
    print "In internalFrameActivated()"
     
    displayTableTitle = rootContainer.displayTableTitle
    print "The table being displayed is: ", displayTableTitle
    
    SQL = "select V.ValueName LabValueName, V.ValueId, V.Description, V.DisplayDecimals "\
        " from LtValue V, LtDisplayTable T "\
        " where V.displayTableId = T.DisplayTableId "\
        " and T.DisplayTableTitle = '%s' "\
        " order by ValueName" % (displayTableTitle)
    print SQL
    pds = system.db.runQuery(SQL)
    for record in pds:
        print record["LabValueName"], record["ValueId"], record["Description"], record["DisplayDecimals"]
    
    repeater=rootContainer.getComponent("Template Repeater")
    repeater.templateParams=pds


#  This configures the table inside the template that is in the repeater.  It is called by the container AND by the timer 
def configureLabDatumTable(container):
    username = system.security.getUsername()
    print "Checking for lab data viewed by ", username
    valueName=container.LabValueName
    valueDescription=container.Description
    displayDecimals=container.DisplayDecimals
    print "Configuring the Lab Datum Viewer table for ", valueName
    
    from ils.labData.common import fetchValueId
    valueId = fetchValueId(valueName)
        
    SQL = "select top 13 RawValue as '%s', SampleTime, HistoryId "\
        " from LtHistory "\
        " where ValueId = %i "\
        " order by SampleTime desc" % (valueName, valueId)
    print SQL
    pds = system.db.runQuery(SQL)
    
    SQL = "Select HistoryId from LtValueViewed where ValueId = %i and Username = '%s'" % (valueId, username)
    lastHistoryIdViewed = system.db.runScalarQuery(SQL)

    header = [str(valueDescription), 'seen', 'historyId']
    print "Fetched ", len(pds), " rows, the header is ", header
    data = []
    tableData = []
    newestHistoryId=-1
    for record in pds:
        historyId = record['HistoryId']
        
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
        
        if historyId > lastHistoryIdViewed:
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
    username = system.security.getUsername()
    
    repeater=rootContainer.getComponent("Template Repeater")
    templates=getTemplates(repeater, "Lab Datum Viewer")

    for template in templates:
        valueId = template.getPropertyValue("ValueId")
        valueName = template.getPropertyValue("LabValueName")
        print "Processing values that have been seen for %s - %i by %s" % (valueName, valueId, username)
        
        # Get the id that is stored for this user and this value.
        SQL = "select HistoryId from LtValueViewed where ValueId = %i and username = '%s' " % (valueId, username)
        lastHistoryId = system.db.runScalarQuery(SQL)
        if lastHistoryId == None:
            lastHistoryId = -1

        print "  ...the id of the last value seen is %i..." % (lastHistoryId)
        # Get the dataset from the property of the container (not from the table in the template)        
        ds = template.getPropertyValue("data")

        # Now iterate through the dataset looking for measurements whose id is greater than the id that is stored in the database.
        update = False
        for row in range(ds.rowCount):
            seen = ds.getValueAt(row,'seen')
            historyId = ds.getValueAt(row, 'historyId')
#            print seen, " -> ", historyId
            if historyId > lastHistoryId:
                lastHistoryId = historyId
                update = True
        
        # If we found an id that is greater than the last one I've recorded then update the database
        if update:
            print "There is a lab datum that needs to be marked as seen"
            SQL = "update LtValueViewed set HistoryId = %i where ValueId = %i and username = '%s'" % (lastHistoryId, valueId, username)
            rows = system.db.runUpdateQuery(SQL)
            if rows == 0:
                print "...inserting a row since none existed..."
                SQL = "insert into LtValueViewed (HistoryId, ValueId, Username) values(%i, %i, '%s')" % (lastHistoryId, valueId, username)
                rows = system.db.runUpdateQuery(SQL)


# This configures the table inside the template that is in the repeater.  It is called by the container AND by the timer 
# This is ALWAYS run from a client.  For now, the "Get History" button appears on every lab data table, regardless of its source,
# even though it can only work for data that comes from PHD.  It can't work for DCS data, selectors, or derived values.
def fetchHistory(container):
    print "Fetching history looking for missing data..."
    valueName=container.LabValueName
    valueId=container.ValueId
    
    print "Configuring the Lab Datum Viewer table for %s - %i" % (valueName, valueId)
    
    SQL = "Select InterfaceName, ItemId from LtPHDValueView where ValueId = %i" % (valueId)
    pds = system.db.runQuery(SQL)
    
    if len(pds) == 0:
        system.gui.warningBox("This lab data does not have history because it's source is not PHD!")
        return

    # If they choose a lab selector, should the request be transferred to the source of the selector?
    
    hdaInterface=pds[0]["InterfaceName"]
    itemId=pds[0]["ItemId"]
    maxValues=0
    boundingValues=0
    
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

    retVals=system.opchda.readRaw(hdaInterface, [itemId], startDate, endDate, maxValues, boundingValues)
    print "...back from HDA read, read %i values!" % (len(retVals))

    # We are fetching the history for a single lab value.
    valueList=retVals[0]

    if str(valueList.serviceResult) != 'Good':
        system.gui.errorBox("The data returned from the PHD historian was %s --" % (valueList.serviceResult))
        return

    if valueList.size()==0:
        system.gui.warningBox("No data was found for %s" % (itemId))
        return
    
    system.db.runUpdateQuery("SET IDENTITY_INSERT LtHistory ON")
    
    historyId = system.db.runScalarQuery("select min(HistoryId) from LtHistory")
    print "The minimum history id is: %i", historyId

    # We found some data so now process it - we found data, but that doesn't mean it is new!
    rows=0
    for qv in valueList:
        sampleTime = qv.timestamp
        rawValue = qv.value
        quality = qv.quality

        # Only process Good values
        if quality.isGood():
            
            SQL = "select HistoryId from LtHistory where ValueId = ? and RawValue = ? and SampleTime = ?"
            pds = system.db.runPrepQuery(SQL, [valueId, rawValue, sampleTime]) 
            if len(pds) == 0:
                print "*** NEED TO INSERT A MISSING VALUE: ", valueName, itemId, rawValue, sampleTime, quality
                
                # Insert the value into the lab history table.
                historyId = historyId - 1
                SQL = "insert into LtHistory (historyId, valueId, RawValue, SampleTime, ReportTime) values (?, ?, ?, ?, getdate())"
                system.db.runPrepUpdate(SQL, [historyId, valueId, rawValue, sampleTime])
                print "    Inserted value with history id: ", historyId 
                rows = rows + 1
#        # Step 2 - Update LtValue with the id of the latest history value
#        SQL = "update LtValue set LastHistoryId = %i where valueId = %i" % (historyId, valueId)
#        system.db.runUpdateQuery(SQL, database)

    system.db.runUpdateQuery("SET IDENTITY_INSERT LtHistory OFF")
    
    if rows == 0:
        system.gui.messageBox("No new data was found!")
    else:
        configureLabDatumTable(container)
        system.gui.messageBox("%i new values were loaded!" % (rows))
        