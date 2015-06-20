'''
Created on Apr 30, 2015

@author: Pete
'''
import system

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
    
    communicationHealthy = system.tag.read("Configuration/LabData/communicationHealthy").value
    manualEntryPermitted = system.tag.read("Configuration/LabData/manualEntryPermitted").value
    from ils.common.user import isAE
    isAE = isAE()
    
    if not(communicationHealthy) or manualEntryPermitted or isAE:
        SQL = "select V.ValueName, V.ValueId "\
            " from LtValue V, TkUnit U, TkPost P "\
            " where V.UnitId = U.UnitId "\
            " and U.PostId = P.PostId "\
            " and P.Post = '%s' "\
            " order by ValueName" % (post) 
    else: 
        SQL = "select V.ValueName, V.ValueId "\
            " from LtLocalValue LV, LtValue V, TkUnit U, TkPost P "\
            " where LV.ValueId = V.ValueId "\
            " and V.UnitId = U.UnitId "\
            " and U.PostId = P.PostId "\
            " and P.Post = '%s' "\
            " order by ValueName" % (post) 
    
    pds = system.db.runQuery(SQL)
    
    chooseList = rootContainer.getComponent("List")
    chooseList.data = pds
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
    
    valueId = rootContainer.valueId
    valueName = rootContainer.valueName
    
    SQL = "select * from LtLimit where ValueId = %s" % (str(valueId))
    print SQL
    pds = system.db.runQuery(SQL)

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
        print "Error fetching limits "
        rootContainer.upperValidityLimitEnabled=False
        rootContainer.lowerValidityLimitEnabled=False
        rootContainer.upperSQCLimitEnabled=False
        rootContainer.lowerSQCLimitEnabled=False
        rootContainer.upperReleaseLimitEnabled=False
        rootContainer.lowerReleaseLimitEnabled=False

# This is called when the operator presses the 'Enter' button on the Manual Entry screen
def entryFormEnterData(rootContainer, db = ""):
    print "In ils.labData.limits.manualEntry.entryFormEnterData()"
    
    sampleTime = rootContainer.getComponent("Sample Time").date
    sampleValue = rootContainer.getComponent("Lab Value Field").floatValue
    
    valueId = rootContainer.valueId
    valueName = rootContainer.valueName
    
    # Store the value locally in the X O M database
    from ils.labData.scanner import storeValue 
    storeValue(valueId, valueName, sampleValue, sampleTime, db)
    
    # Store the value in the Lab Data UDT memory tags, which are local to Ignition
    from ils.common.config import getTagProvider
    provider = '[' + getTagProvider() + ']'
    
    from ils.labData.scanner import updateTags
    tags, tagValues = updateTags(provider, valueName, sampleValue, sampleTime, True, [], [])
    
    # If the lab datum is "local" then write the value to PHD (use a regular OPC write, so we won't 
    # capture the sample time)
    SQL = "select LV.ItemId, WL.ServerName "\
        " from LtLocalValue LV, TkWriteLocation WL "\
        " where LV.ValueId = %s "\
        " and LV.WriteLocationId = WL.WriteLocationId" % (str(valueId))
 
    pds = system.db.runQuery(SQL, db)
    if len(pds) != 0:
        record = pds[0]
        itemId = record["ItemId"]
        serverName = record["ServerName"]
        returnQuality = system.opc.writeValue(serverName, itemId, sampleValue)
        if returnQuality.isGood():
            print "Write <%s> to %s-%s for %s local lab data was successful" % (str(sampleValue), serverName, itemId, valueName)
        else:
            print "ERROR: Write <%s> to %s-%s for %s local lab data failed" % (str(sampleValue), serverName, itemId, valueName)
    else:
        print "Skipping write of manual lab data because it is not LOCAL (%s %s %s %s)" % (str(sampleValue), serverName, itemId, valueName)
    
    # There is a cache of last values but we can't update it from here because the cache is in the gateway...
    
    system.gui.messageBox("Lab value of %s has been stored for %s!" % (str(sampleValue), valueName))
    