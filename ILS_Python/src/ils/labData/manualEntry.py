'''
Created on Apr 30, 2015

@author: Pete
'''
import system
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.labData")
sqlLog = LogUtil.getLogger("com.ils.SQL.labData")

# This is called from the "Manual Entry" button on the "Lab Data Table Chooser" screen
def launchChooser(rootContainer):
    print "Launching the Manual Lab Data Entry Chooser Screen"
    post = rootContainer.selectedPost
    window=system.nav.openWindow("Lab Data/Manual Entry Value Chooser",{"post": post})
    system.nav.centerWindow(window)

  
def chooserInitialization(rootContainer):
    print "In ils.labData.manualEntry.chooserInitialization()..."
    post = rootContainer.post
    
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
    sqlLog.trace(SQL)
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
    
    from ils.labData.scanner import storeValue 
    storeValue(valueId, valueName, sampleValue, sampleTime, db)
    
    from ils.common.config import getTagProvider
    provider = '[' + getTagProvider() + ']'
    
    from ils.labData.scanner import updateTags
    tags, tagValues = updateTags(provider, valueName, sampleValue, sampleTime, True, [], [])
    
    # There is a cache of last values but we can't update it from here because the cache is in the gateway...
    