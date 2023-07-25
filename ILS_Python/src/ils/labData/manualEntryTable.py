'''
Created on Jul 24, 2023

@author: ils
'''

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

    
def internalFrameOpened(rootContainer):
    log.infof("In %s.internalFormOpened()...", __name__)
    
    table = rootContainer.getComponent("Power Table")
    db = getDatabase()
    txt = rootContainer.valueIds
    valueIds = txt.split(",")
    print "The ids are: ", valueIds
    
    txt = rootContainer.valueNames
    valueNames = txt.split(",")
    print "ValueNames: ", valueNames
    
    if len(valueIds) < 2:
        print "This only works for 2 or more lab values"
        return
    
    valueId = str(valueIds[0])
    
    ''' Fetch the unit for the first lab value, by definition, all lab values from the chooser are from the same unit '''
    SQL = "select UnitName from TkUnit U, LtValue V "\
        " where V.UnitId = U.UnitId and V.ValueId = %s" % (str(valueId))
    unitName = system.db.runScalarQuery(SQL, database=db)
    if unitName == None:
        system.gui.errorBox("Error fetching the unit for this lab data!")
        return

    rootContainer.unitName = unitName
    print "   using unit %s" % (str(unitName))

    header = [""]
    data = []
    
    vals = ["Value:"]
    blanks = [""]
    for valueName in valueNames:
        blanks.append("")
        header.append(valueName)
        vals.append("")
    data.append(vals)
    
    vals = ["Id:"]
    for valueId in valueIds:
        vals.append(valueId)
    data.append(vals)

    ''' Do this just for debugging '''
    ds = system.dataset.toDataSet(header, data)
    table.data = ds
    
    ''' Set up the dataset with blank limits '''
    data.append(["Upper Release Limit"] + blanks)
    data.append(["Upper Validity Limit"] + blanks)
    data.append(["Upper SQC Limit"] + blanks)
    data.append(["Lower SQC Limit"] + blanks)
    data.append(["Lower Validity Limit"] + blanks)
    data.append(["Lower Release Limit"] + blanks)

    ds = system.dataset.toDataSet(header, data)

    ''' Fetch the limits for each value '''
    foundReleaseLimits = False
    foundValidityLimits = False
    foundSQCLimits = False
    
    UPPER_RELEASE_LIMIT_ROW = 2
    UPPER_VALIDITY_LIMIT_ROW = 3
    UPPER_SQC_LIMIT_ROW = 4
    LOWER_SQC_LIMIT_ROW = 5
    LOWER_VALIDITY_LIMIT_ROW = 6
    LOWER_RELEASE_LIMIT_ROW = 7
    
    col = 1
    for valueId in valueIds:
        SQL = "select * from LtLimit where ValueId = %s" % (str(valueId))
        print SQL
        pds = system.db.runQuery(SQL, database=db)
        for record in pds:
            
            # Validity Limits
            if record["UpperValidityLimit"] != None:
                foundValidityLimits = True
                ds = system.dataset.setValue(ds, UPPER_VALIDITY_LIMIT_ROW, col, record["UpperValidityLimit"])
    
            if record["LowerValidityLimit"] != None:
                foundValidityLimits = True
                ds = system.dataset.setValue(ds, LOWER_VALIDITY_LIMIT_ROW, col, record["LowerValidityLimit"])

            # SQC Limits
            if record["UpperSQCLimit"] != None:
                foundSQCLimits = True
                ds = system.dataset.setValue(ds, UPPER_SQC_LIMIT_ROW, col, record["UpperSQCLimit"])
    
            if record["LowerSQCLimit"] != None:
                foundSQCLimits = True
                ds = system.dataset.setValue(ds, LOWER_SQC_LIMIT_ROW, col, record["LowerSQCLimit"])
            
            # Release Limits
            if record["UpperReleaseLimit"] != None:
                foundReleaseLimits = True
                ds = system.dataset.setValue(ds, UPPER_RELEASE_LIMIT_ROW, col, record["UpperReleaseLimit"])
    
            if record["LowerReleaseLimit"] != None:
                foundReleaseLimits = True
                ds = system.dataset.setValue(ds, LOWER_RELEASE_LIMIT_ROW, col, record["LowerReleaseLimit"])
        
        col = col + 1

        print "Found Release Limits:  ", foundReleaseLimits
        print "Found Validity Limits: ", foundValidityLimits
        print "Found SQC Limits:      ", foundSQCLimits

    table = rootContainer.getComponent("Power Table")
    table.data = ds

    return

    #refreshRecentValues(rootContainer, valueId, db)


'''
Now select the recent values for this lab datum
'''
def refreshRecentValues(rootContainer, valueId, db):    
    SQL = "select top 10  SampleTime, RawValue from LtValueView where ValueId = %d order by SampleTime DESC" % (valueId) 
    pds = system.db.runQuery(SQL, database=db)
    table = rootContainer.getComponent("Recent Value Container").getComponent("Value Table")
    table.data = pds
    

# This is called when the operator presses the 'Enter' button on the Manual Entry screen
def enterCallback(rootContainer, db=""):
    log.infof("In %s.enterCallback()", __name__)
    
    unitName = rootContainer.unitName
    
    from ils.config.client import getTagProvider
    provider = getTagProvider()
    
    sampleTime = rootContainer.getComponent("Sample Time").date
    
    table = rootContainer.getComponent("Power Table")
    ds = table.data
    cols = ds.getColumnCount()
    
    ID_ROW = 1
    VALUE_ROW = 0
    
    for col in range(0, cols):
        valueId = ds.getValueAt(ID_ROW, col)
        val = ds.getValueAt(VALUE_ROW, col)
        log.infof("Value Id: %s - Value: %s", valueId, val) 

        if val != "":
            print "SAVE IT!"
            

    
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
    pds = system.db.runPrepQuery(SQL, [valueId, sampleTime, sampleValue], database=db)
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
            print "Writing local value %s for %s to %s..." % (str(sampleValue), valueName, itemId)
            returnQuality = system.opchda.insertReplace(serverName, itemId, sampleValue, sampleTime, 192)
            print "...the returnQuality is: %s" % (str(returnQuality))
        else:
            print "*** Skipping *** Write of local value %s for %s to %s" % (str(sampleValue), valueName, itemId)
    else:
        print "Skipping write of manual lab data because it is not LOCAL (%s %s)" % (str(sampleValue), valueName)
    
    # There is a cache of last values but we can't update it from here because the cache is in the gateway...
    system.gui.messageBox("Lab value of %s has been stored for %s!" % (str(sampleValue), valueName))
    