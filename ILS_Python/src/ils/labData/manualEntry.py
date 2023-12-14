'''
Created on Apr 30, 2015

@author: Pete
'''
import system
from ils.io.util import readTag
from ils.config.client import getDatabase
from ils.log import getLogger
log = getLogger(__name__)

# Everything in this module runs in the client, so the use of loggers isn't too important since nothing will go 
# to the wrapper log anyway.

# This is called from the "Manual Entry" button on the "Lab Data Table Chooser" screen
def launchChooser(rootContainer):
    log.infof("In %s.launchChooser()...", __name__)
    post = rootContainer.selectedPost
    window=system.nav.openWindow("Lab Data/Manual Entry Value Chooser",{"post": post})
    system.nav.centerWindow(window)

  
def chooserInitialization(rootContainer):
    log.infof("In %s.chooserInitialization()...", __name__)
    post = rootContainer.post
    db = getDatabase()
    
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
    log.tracef("Selecting the local lab values...")
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
        
        log.tracef("...adding lab data from PHD that allow manual entry...")
        SQL = "select ValueName, ValueId "\
            " from LtPHDValueView "\
            " where Post = '%s' and AllowManualEntry = 1 "\
            " order by ValueName" % (post)
        pds = system.db.runQuery(SQL, database=db)
        ds = appendDatasets(ds, pds)
        
        log.tracef("...adding lab data from the DCS that allow manual entry...")
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
    log.infof("In %s.launchEntryForm()...", __name__)
    post = rootContainer.post
    chooseList = rootContainer.getComponent("List")
    ds=chooseList.data
    selections = chooseList.getSelectedIndices()
    
    if len(selections) == 1:
        idx=chooseList.selectedIndex
        if idx < 0:
            system.gui.warningBox("Please select a Lab Parameter and then press 'Enter Data'")
            return
        valueName=ds.getValueAt(idx,'ValueName')
        valueId=ds.getValueAt(idx,'ValueId')
        
        log.tracef("Editing selection #%d: %s - %s", idx, valueName, str(valueId))
        
        window=system.nav.openWindow("Lab Data/Manual Entry",{"valueName": valueName, "valueId":valueId})
        system.nav.centerWindow(window)
    elif len(selections) > 1:
        log.tracef("Launch the entry table!")
        valueNames = []
        valueIds = []
        for selection in selections:
            valueName=ds.getValueAt(selection,'ValueName')
            valueNames.append(valueName)
            
            valueId=ds.getValueAt(selection,'ValueId')
            valueIds.append(str(valueId))
    
        window=system.nav.openWindow("Lab Data/Manual Entry Table",{"post": post, "valueNames": ",".join(valueNames), "valueIds": ",".join(valueIds)})
        system.nav.centerWindow(window)

    
def entryFormInitialization(rootContainer):
    log.infof("In %s.entryFormInitialization()...", __name__)
    
    db = getDatabase()
    dateFormat = readTag("Configuration/LabData/dateFormatLong").value
    rootContainer.formatString = dateFormat
    valueId = rootContainer.valueId
    valueName = rootContainer.valueName
    
    # Fetch the unit for this value
    SQL = "select U.UnitName, V.StringValue from TkUnit U, LtValue V "\
        " where V.UnitId = U.UnitId and V.ValueId = %s" % (str(valueId))
    pds = system.db.runQuery(SQL, database=db)
    if len(pds) != 1:
        system.gui.errorBox("Error fetching the unit for this lab data!")
        return
    record=pds[0]
    
    unitName = record["UnitName"]
    rootContainer.unitName = unitName
    
    stringValue = record["StringValue"]
    rootContainer.stringValue = stringValue
    
    if stringValue:
        rootContainer.upperValidityLimitEnabled=False
        rootContainer.lowerValidityLimitEnabled=False
        rootContainer.upperSQCLimitEnabled=False
        rootContainer.lowerSQCLimitEnabled=False
        rootContainer.upperReleaseLimitEnabled=False
        rootContainer.lowerReleaseLimitEnabled=False
    else:
        # Fetch the limits for this value
        SQL = "select * from LtLimit where ValueId = %s" % (str(valueId))
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

    refreshRecentValues(rootContainer, valueId, stringValue, db)


'''
Now select the recent values for this lab datum
'''
def refreshRecentValues(rootContainer, valueId, stringValue, db):
    dateFormat = readTag("Configuration/LabData/dateFormatLong").value
    
    if stringValue:
        SQL = "select top 10 SampleTime, RawStringValue as 'RawValue' from LtHistory "\
            " where ValueId = %i order by SampleTime desc" % (valueId)
    else:
        SQL = "select top 13 SampleTime, RawValue from LtHistory "\
            " where ValueId = %i order by SampleTime desc" % (valueId)         
    
    pds = system.db.runQuery(SQL, database=db)
    data = []
    for record in pds:
        sampleTime = system.date.format(record["SampleTime"], dateFormat)
        val = record["RawValue"]
        data.append([sampleTime, val])
         
    ds = system.dataset.toDataSet(["Sample Time", "Value"], data)
    table = rootContainer.getComponent("Recent Value Container").getComponent("Value Table")
    table.data = ds
    

# This is called when the operator presses the 'Enter' button on the Manual Entry screen
def entryFormEnterData(rootContainer, db=""):
    log.infof("In %s.entryFormEnterData()", __name__)
    
    from ils.config.client import getTagProvider
    provider = getTagProvider()
    
    stringValue = rootContainer.stringValue
    valueId = rootContainer.valueId
    valueName = rootContainer.valueName
    unitName = rootContainer.unitName
    sampleTime = rootContainer.getComponent("Sample Time").date
    
    if stringValue:
        log.tracef("...handling a string value...")
        sampleValue = rootContainer.getComponent("String Lab Value Field").text
        
        # Check for an exact duplicate with the same value and time
        SQL = "select count(*) from LtHistory where ValueId = ? and SampleTime = ? and rawStringValue = ?" 
        pds = system.db.runPrepQuery(SQL, [valueId, sampleTime, sampleValue], database=db)
        count = pds[0][0]
        if count > 0:
            system.gui.warningBox("This result has already been entered!")
            return
        
    else:
        sampleValue = rootContainer.getComponent("Lab Value Field").floatValue
    
        upperValidityLimitEnabled = rootContainer.upperValidityLimitEnabled
        upperValidityLimit = rootContainer.upperValidityLimit
        lowerValidityLimitEnabled = rootContainer.lowerValidityLimitEnabled
        lowerValidityLimit = rootContainer.lowerValidityLimit
    
        log.tracef("The validity limits are from %s to %s (enabled = %s, %s)", str(lowerValidityLimit), str(upperValidityLimit), str(upperValidityLimitEnabled), str(lowerValidityLimitEnabled))
        
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
        pds = system.db.runPrepQuery(SQL, [valueId, sampleTime, sampleValue], database=db)
        count = pds[0][0]
        if count > 0:
            system.gui.warningBox("This result has already been entered!")
            return

    # Store the value locally in the database
    from ils.labData.scanner import storeValue 
    storeValue(valueId, valueName, sampleValue, sampleTime, unitName, stringValue, log, provider, db)
    
    # Store the value in the Lab Data UDT memory tags, which are local to Ignition
    from ils.labData.scanner import updateTags
    tags, tagValues = updateTags(provider, unitName, valueName, sampleValue, sampleTime, True, True, [], [], log)
    print "Writing ", tagValues, " to ", tags
    system.tag.writeBlocking(tags, tagValues)
    
    # Refresh the table of recent values to show what we just entered.
    refreshRecentValues(rootContainer, valueId, stringValue, db)
    
    # If the lab datum is "local" then write the value to PHD, the destination is ALWAYS the historian so use an HDA write. 
    SQL = "select LV.ItemId, PHD.InterfaceName "\
        " from LtLocalValue LV, LtHdaInterface PHD "\
        " where LV.ValueId = %s "\
        " and LV.InterfaceId = PHD.InterfaceId" % (str(valueId))
 
    pds = system.db.runQuery(SQL, database=db)
    if len(pds) != 0:
        record = pds[0]
        itemId = record["ItemId"]
        serverName = record["InterfaceName"]
        
        # Check if writing is enabled
        labDataWriteEnabled= readTag("[" + provider + "]Configuration/LabData/labDataWriteEnabled").value
        globalWriteEnabled = readTag("[" + provider + "]Configuration/Common/writeEnabled").value
        writeEnabled = labDataWriteEnabled and globalWriteEnabled
        
        if writeEnabled and itemId not in ["", None] and serverName not in ["", None]:
            log.tracef("Writing local value %s for %s to %s...", str(sampleValue), valueName, itemId)
            returnQuality = system.opchda.insertReplace(serverName, itemId, sampleValue, sampleTime, 192)
            log.tracef("...the returnQuality is: %s", str(returnQuality))
        else:
            log.tracef("*** Skipping *** Write of local value %s for %s to %s", str(sampleValue), valueName, itemId)
    else:
        log.tracef("Skipping write of manual lab data because it is not LOCAL (%s %s)", str(sampleValue), valueName)
    
    # There is a cache of last values but we can't update it from here because the cache is in the gateway...
    system.gui.messageBox("Lab value of %s has been stored for %s!" % (str(sampleValue), valueName))
    