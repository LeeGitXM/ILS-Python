'''
Created on Apr 30, 2015

@author: Pete
'''
import system
from ils.io.util import readTag
from ils.common.config import getDatabaseClient
from ils.log import getLogger
log = getLogger(__name__)

# Everything in this module runs in the client, so the use of loggers isn't too important since nothing will go 
# to the wrapper log anyway.

# This is called from the "Manual Entry" button on the "Lab Data Table Chooser" screen
def launchChooser(rootContainer):
    print "Launching the Manual Lab Data Entry Chooser Screen"
    post = rootContainer.selectedPost
    window=system.nav.openWindow("Lab Data/Manual Entry Value Chooser",{"post": post})
    system.nav.centerWindow(window)

  
def chooserInitialization(rootContainer):
    print "In ils.labData.manualEntry.chooserInitialization()..."
    post = rootContainer.post
    db = getDatabaseClient()
    
    def appendDatasets(ds, pds):
        for record in pds:
            vals = [record["ValueName"], record["ValueId"]]
            ds = system.dataset.addRow(ds, vals)
        return ds
    
    communicationHealthy = readTag("Configuration/LabData/communicationHealthy").value
    manualEntryPermitted = readTag("Configuration/LabData/manualEntryPermitted").value
    from ils.common.user import isAE
    isAE = isAE()
    
    ''' We always present the local lab values. '''
    print "Selecting the local lab values..."
    SQL = "select V.ValueName, V.ValueId "\
        " from LtLocalValue LV, LtValue V, TkUnit U, TkPost P "\
        " where LV.ValueId = V.ValueId "\
        " and V.UnitId = U.UnitId "\
        " and U.PostId = P.PostId "\
        " and P.Post = '%s' "\
        " order by ValueName" % (post) 
    
    pds = system.db.runQuery(SQL, database=db)
    ds = system.dataset.toDataSet(pds)
    
    ''' 
    If the user is an AE or comms are down or the manualEntry has been enabled, then add in DCS, and HDA lab values. 
    The HDA / Lab data watchdog considers the communication state and the overrride tag and then sets manualEntryPermitted.
    So it shouldn't be necessary to check communicationHealthy here unless the watchdog isn't running.
    '''
    if not(communicationHealthy) or manualEntryPermitted or isAE:
        
        print "...adding lab data from PHD..."
        SQL = "select ValueName, ValueId "\
            " from LtPHDValueView "\
            " where Post = '%s' and AllowManualEntry = 1 "\
            " order by ValueName" % (post)
        pds = system.db.runQuery(SQL, database=db)
        ds = appendDatasets(ds, pds)
        
        print "...adding lab data from the DCS..."
        SQL = "select ValueName, ValueId "\
            " from LtDCSValueView "\
            " where Post = '%s' and AllowManualEntry = 1 "\
            " order by ValueName" % (post)
        pds = system.db.runQuery(SQL, database=db)
        ds = appendDatasets(ds, pds)
        ds = system.dataset.sort(ds, "ValueName")
    
    chooseList = rootContainer.getComponent("List")
    chooseList.data = ds
    chooseList.selectedIndex = -1

# This is call from the "Enter Data" button on the "Manual Entry Value Chooser" screen
def launchEntryForm(rootContainer):
    print "Launching the Manual Lab Data Entry Form"
    chooseList = rootContainer.getComponent("List")
    ds=chooseList.data
    idx=chooseList.selectedIndex
    if idx < 0:
        system.gui.warningBox("Please select a Lab Parameter and then press 'Enter Data'")
        return
    valueName=ds.getValueAt(idx,'ValueName')
    valueId=ds.getValueAt(idx,'ValueId')
    
    print "Editing %s - %s" % (valueName, str(valueId))
    
    window=system.nav.openWindow("Lab Data/Manual Entry",{"valueName": valueName, "valueId":valueId})
    system.nav.centerWindow(window)
    
def entryFormInitialization(rootContainer):
    print "In ils.labData.manualEntry.entryFormInitialization()..."
    
    db = getDatabaseClient()
    valueId = rootContainer.valueId
    valueName = rootContainer.valueName
    
    # Fetch the unit for this value
    SQL = "select UnitName from TkUnit U, LtValue V "\
        " where V.UnitId = U.UnitId and V.ValueId = %s" % (str(valueId))
    pds = system.db.runQuery(SQL, database=db)
    if len(pds) != 1:
        system.gui.errorBox("Error fetching the unit for this lab data!")
        return
    record=pds[0]
    unitName = record["UnitName"]
    rootContainer.unitName = unitName
    print "   using unit %s" % (str(unitName))
    
    # Fetch the limits for this value
    SQL = "select * from LtLimit where ValueId = %s" % (str(valueId))
    print SQL
    pds = system.db.runQuery(SQL, database=db)

    if len(pds) == 1:
        record=pds[0]
        
        # Validity Limits
        if record["UpperValidityLimit"] == None:
            rootContainer.upperValidityLimitEnabled=False
        else:
            rootContainer.upperValidityLimitEnabled=True
            rootContainer.upperValidityLimit = record["UpperValidityLimit"]

        if record["LowerValidityLimit"] == None:
            rootContainer.lowerValidityLimitEnabled=False
        else:
            rootContainer.lowerValidityLimitEnabled=True
            rootContainer.lowerValidityLimit = record["LowerValidityLimit"]

        # SQC Limits
        if record["UpperSQCLimit"] == None:
            rootContainer.upperSQCLimitEnabled=False
        else:
            rootContainer.upperSQCLimitEnabled=True
            rootContainer.upperSQCLimit = record["UpperSQCLimit"]

        if record["LowerSQCLimit"] == None:
            rootContainer.lowerSQCLimitEnabled=False
        else:
            rootContainer.lowerSQCLimitEnabled=True
            rootContainer.lowerSQCLimit = record["LowerSQCLimit"]
        
        # Release Limits
        if record["UpperReleaseLimit"] == None:
            rootContainer.upperReleaseLimitEnabled=False
        else:
            rootContainer.upperReleaseLimitEnabled=True
            rootContainer.upperReleaseLimit = record["UpperReleaseLimit"]

        if record["LowerReleaseLimit"] == None:
            rootContainer.lowerReleaseLimitEnabled=False
        else:
            rootContainer.lowerReleaseLimitEnabled=True
            rootContainer.lowerReleaseLimit = record["LowerReleaseLimit"]
        
    else:
        print "Error fetching limits, fetched %d records" % (len(pds))
        rootContainer.upperValidityLimitEnabled=False
        rootContainer.lowerValidityLimitEnabled=False
        rootContainer.upperSQCLimitEnabled=False
        rootContainer.lowerSQCLimitEnabled=False
        rootContainer.upperReleaseLimitEnabled=False
        rootContainer.lowerReleaseLimitEnabled=False

    refreshRecentValues(rootContainer, valueId, db)


'''
Now select the recent values for this lab datum
'''
def refreshRecentValues(rootContainer, valueId, db):    
    SQL = "select top 10  SampleTime, RawValue from LtValueView where ValueId = %d order by SampleTime DESC" % (valueId) 
    pds = system.db.runQuery(SQL, database=db)
    table = rootContainer.getComponent("Recent Value Container").getComponent("Value Table")
    table.data = pds
    

# This is called when the operator presses the 'Enter' button on the Manual Entry screen
def entryFormEnterData(rootContainer, db = ""):
    print "In ils.labData.limits.manualEntry.entryFormEnterData()"
    
    from ils.common.config import getTagProviderClient
    provider = getTagProviderClient()
    
    from ils.common.config import getTagProvider
    productionProvider = getTagProvider()
    
    sampleTime = rootContainer.getComponent("Sample Time").date
    sampleValue = rootContainer.getComponent("Lab Value Field").floatValue
    
    valueId = rootContainer.valueId
    valueName = rootContainer.valueName
    unitName = rootContainer.unitName
    
    upperValidityLimitEnabled = rootContainer.upperValidityLimitEnabled
    upperValidityLimit = rootContainer.upperValidityLimit
    lowerValidityLimitEnabled = rootContainer.lowerValidityLimitEnabled
    lowerValidityLimit = rootContainer.lowerValidityLimit

    print "The validity limits are from %s to %s (enabled = %s, %s)" % (str(lowerValidityLimit), str(upperValidityLimit), str(upperValidityLimitEnabled), str(lowerValidityLimitEnabled))
    
    if lowerValidityLimitEnabled and lowerValidityLimit != None and lowerValidityLimit != "":
        if sampleValue < lowerValidityLimit:
            confirm = system.gui.confirm("The value you entered, %.4f, is less than the lower validity limit, %.4f, are you sure?" % (sampleValue, lowerValidityLimit))
            if not(confirm):
                return
    
    if upperValidityLimitEnabled and upperValidityLimit != None and upperValidityLimit != "":
        if sampleValue > upperValidityLimit:
            confirm = system.gui.confirm("The value you entered, %s, is greater than the upper validity limit, %s, are you sure?" % (str(sampleValue), str(upperValidityLimit)))
            if not(confirm):
                return

    # Check for an exact duplicate with the same value and time
    SQL = "select count(*) from LtHistory where ValueId = ? and SampleTime = ? and rawValue = ?" 
    print SQL
    pds = system.db.runPrepQuery(SQL, [valueId, sampleTime, sampleValue])
    count = pds[0][0]
    if count > 0:
        system.gui.warningBox("This result has already been entered!")
        return

    # Store the value locally in the X O M database
    from ils.labData.scanner import storeValue 
    storeValue(valueId, valueName, sampleValue, sampleTime, unitName, log, provider, db)
    
    # Store the value in the Lab Data UDT memory tags, which are local to Ignition
    from ils.labData.scanner import updateTags
    tags, tagValues = updateTags(provider, unitName, valueName, sampleValue, sampleTime, True, True, [], [], log)
    print "Writing ", tagValues, " to ", tags
    system.tag.writeBlocking(tags, tagValues)
    
    # Refresh the table of recent values to show what we just entered.
    refreshRecentValues(rootContainer, valueId, db)
    
    # If the lab datum is "local" then write the value to PHD, the destination is ALWAYS the historian so use an HDA write. 
    SQL = "select LV.ItemId, PHD.InterfaceName "\
        " from LtLocalValue LV, LtHdaInterface PHD "\
        " where LV.ValueId = %s "\
        " and LV.InterfaceId = PHD.InterfaceId" % (str(valueId))
 
    pds = system.db.runQuery(SQL, db)
    if len(pds) != 0:
        record = pds[0]
        itemId = record["ItemId"]
        serverName = record["InterfaceName"]
        
        # Check if writing is enabled
        labDataWriteEnabled= readTag("[" + provider + "]Configuration/LabData/labDataWriteEnabled").value
        globalWriteEnabled = readTag("[" + provider + "]Configuration/Common/writeEnabled").value
        writeEnabled = provider != productionProvider or (labDataWriteEnabled and globalWriteEnabled)
        
        if writeEnabled:
            print "Writing local value %s for %s to %s..." % (str(sampleValue), valueName, itemId)
            returnQuality = system.opchda.insertReplace(serverName, itemId, sampleValue, sampleTime, 192)
            print "...the returnQuality is: %s" % (str(returnQuality))
        else:
            print "*** Skipping *** Write of local value %s for %s to %s" % (str(sampleValue), valueName, itemId)
    else:
        print "Skipping write of manual lab data because it is not LOCAL (%s %s)" % (str(sampleValue), valueName)
    
    # There is a cache of last values but we can't update it from here because the cache is in the gateway...
    
    system.gui.messageBox("Lab value of %s has been stored for %s!" % (str(sampleValue), valueName))
    