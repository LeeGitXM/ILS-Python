'''
Created on Mar 29, 2015

@author: Pete
'''
import system

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

    header = [str(valueDescription), 'seen']
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
            
        data.append([val,seen])
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

# This is called when the lab data table window is closed.  As long as the window is open, then we want the rows highlighted. 
# They may want to add a button that calls this to make the red go away, but for now just call it when the window closes.
def setSeen(rootContainer):
    username = system.security.getUsername()
    
    repeater=rootContainer.getComponent("Template Repeater")
                
    ds = repeater.templateParams
    repeater_pds = system.dataset.toPyDataSet(ds)
    for record in repeater_pds:
        valueId=record['ValueId']
        valueName=record['LabValueName']

        print "Setting SEEN for %s - %s" % (valueName, valueId)
        print "Updating %s as seen by %s..." % (valueName, username)

        SQL = "select LastHistoryId from LtValue where ValueId = %i " % (valueId)
        lastHistoryId = system.db.runScalarQuery(SQL)
        
        if lastHistoryId != None and lastHistoryId != -1:
            SQL = "update LtValueViewed set HistoryId = %i where ValueId = %i and username = '%s'" % (lastHistoryId, valueId, username)
            rows = system.db.runUpdateQuery(SQL)
            if rows == 0:
                print "inserting a row since none existed..."
                SQL = "insert into LtValueViewed (HistoryId, ValueId, Username) values(%i, %i, '%s')" % (lastHistoryId, valueId, username)
                rows = system.db.runUpdateQuery(SQL)
        else:
            print "Skipping %s, probably because it does not have any data..." % (valueName)

        
        