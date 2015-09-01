'''
Created on Apr 28, 2015

@author: Pete
'''
import system
from java.util import Calendar
import ils.common.util as util
log = system.util.getLogger("com.ils.labData")


# History should be restored on startup, but generally the site needs to perform a site specific selector
# configuration BEFORE the history is performed.
def gateway():
    from ils.labData.version import version
    version, revisionDate = version()
    log.info("Starting Lab Data Toolkit gateway version %s - %s" % (version, revisionDate))
    from ils.common.config import getTagProvider
    provider = getTagProvider()
    createTags("[" + provider + "]")
    resetSelectorTriggers("[" + provider + "]")    


# The Lab Selector Value UDT has a trigger tag which acts as a semaphore and needs to be reset on startup
def resetSelectorTriggers(provider):
    log.info("Resetting Lab Data Selector Trigger tags...")
    selectors=system.tag.browseTags(parentPath=provider, udtParentType="Lab Data/Lab Selector Value", recursive=True)
    
    tagNames=[]
    tagValues=[]
    for selector in selectors:
        tagNames.append(selector.fullPath + "/trigger")
        tagValues.append(False)
    system.tag.writeAllSynchronous(tagNames, tagValues)
        

def client():
    from ils.labData.version import version
    version = version()
    log.info("Initializing the Lab Data Toolkit client version %s" % (version))
    

def createTags(tagProvider):
    print "Creating Lab Data configuration tags...."
    headers = ['Path', 'Name', 'Data Type', 'Value']
    data = []
    path = tagProvider + "Configuration/LabData/"

    data.append([path, "pollingEnabled", "Boolean", "True"])
    data.append([path, "standardDeviationsToValidityLimits", "Float8", "4.5"])
    data.append([path, "manualEntryPermitted", "Boolean", "False"])
    data.append([path, "communicationHealthy", "Boolean", "True"])
    data.append([path, "labDataWriteEnabled", "Boolean", "True"])

    ds = system.dataset.toDataSet(headers, data)
    from ils.common.tagFactory import createConfigurationTags
    createConfigurationTags(ds, log)


def restoreHistory(tagProvider, daysToRestore=7):
    # This is run from a project startup script, so it should have the notion of a default database
    database = ""
    restoreValueHistory(tagProvider, daysToRestore, database)
    restoreSelectorHistory(tagProvider, daysToRestore, database)


def restoreValueHistory(tagProvider, daysToRestore=7, database=""):
    log.info("Restoring lab data value history...")
    
    tags=[]
    tagValues=[]

    # Calculate the start and end dates that will be used if no data is found
    endDate = util.getDate()
    cal = Calendar.getInstance()
 
    cal.setTime(endDate)
    cal.add(Calendar.HOUR, daysToRestore * -24)
    restoreStart = cal.getTime()
    
    # Fetch the set of lab values that we need to get from PHD
    SQL = "select UnitName, ValueId, ValueName, ItemId, InterfaceName from LtPHDValueView"
    pds = system.db.runQuery(SQL, database)
    for record in pds:
        hdaInterface = record["InterfaceName"]
        valueId=record["ValueId"]
        valueName=record["ValueName"]
        itemId=record["ItemId"]
        unitName=record["UnitName"]
        
        serverIsAvailable=system.opchda.isServerAvailable(hdaInterface)
        if not(serverIsAvailable):
            log.error("HDA interface %s is not available - unable to restore history!" % (hdaInterface))
        else:
            log.info("---------------------")
            log.info("...reading lab data values from HDA for %s - %s - %s- %s" % (valueId, valueName, itemId, hdaInterface))

            itemIds=[itemId]
            log.info("...restoring incremental history for %s since %s" % (valueName, str(restoreStart)))
            
            maxValues=0
            boundingValues=0
            retVals=system.opchda.readRaw(hdaInterface, itemIds, restoreStart, endDate, maxValues, boundingValues)
        
            valueList=retVals[0]
            if str(valueList.serviceResult) != 'Good':
                log.error("   -- The returned value for %s was %s --" % (itemId, valueList.serviceResult))
        
            elif valueList.size()==0:
                log.error("   -- no data found for %s --" % (itemId))

            else:
                lastValueId = None
                
                try:
                    rows = 0
                    for qv in valueList:
                        rawValue=qv.value
                        sampleTime=qv.timestamp
                        quality=qv.quality
                        log.trace("   %s : %s : %s" % (str(rawValue), str(sampleTime), str(quality)))
                        if quality.isGood():
                            log.trace("      ...inserting...")
                            SQL = "insert into LtHistory (ValueId, RawValue, SampleTime, ReportTime) values (?, ?, ?, getdate())"
                            lastValueId=system.db.runPrepUpdate(SQL, [valueId, rawValue, sampleTime],getKey=True)
                            rows = rows + 1
                    log.info("   ...restored %i rows" % (rows))
                except:
                    log.trace("Error restoring a value for %s - probably due to a duplicate value" % (valueName))
                    
                if lastValueId != None:
                    # Write the last value to the tag and then to LastHistoryUd in LtValue
                    SQL = "update ltValue set lastHistoryId = %i where valueId = %i" % (lastValueId, valueId)
                    system.db.runUpdateQuery(SQL)
    
                    tagName="[%s]LabData/%s/%s" % (tagProvider, unitName, valueName)
                    tags.append(tagName + "/rawValue")
                    tagValues.append(rawValue)
                    tags.append(tagName + "/sampleTime")
                    tagValues.append(sampleTime)
                    tags.append(tagName + "/value")
                    tagValues.append(rawValue)
                    tags.append(tagName + "/badValue")
                    tagValues.append(False)
                    tags.append(tagName + "/status")
                    tagValues.append("Restore")
    
    system.tag.writeAllSynchronous(tags, tagValues)


# Restoring the history to selectors uses the data we just restored to the values.  
# In other words, we don't use HDA to restore selector history - we use the history that we have already
# restored from HDA but is now in our local database.
def restoreSelectorHistory(tagProvider, daysToRestore=7, database=""):
    log.info("Restoring lab data selector history...")
    
    # Calculate the start and end dates that will be used if no data is found
    endDate = util.getDate()
    cal = Calendar.getInstance()
 
    cal.setTime(endDate)
    cal.add(Calendar.HOUR, daysToRestore * -24)
    restoreStart = cal.getTime()
    
    # Fetch the list of selectors and their current source 
    SQL = "SELECT LtValue.ValueName AS SelectorValueName, LtValue.ValueId AS SelectorValueId, "\
        " LtValue_1.ValueId AS SourceValueId, LtValue_1.ValueName AS SourceValueName "\
        " FROM LtValue INNER JOIN "\
        " LtSelector ON LtValue.ValueId = LtSelector.ValueId INNER JOIN "\
        " LtValue AS LtValue_1 ON LtSelector.sourceValueId = LtValue_1.ValueId LEFT OUTER JOIN "\
        " LtHistory ON dbo.LtValue.LastHistoryId = dbo.LtHistory.HistoryId"

    pds = system.db.runQuery(SQL, database)
    log.info("...there are %i selectors..." % (len(pds)))
    for record in pds:
        selectorValueId=record["SelectorValueId"]
        selectorValueName=record["SelectorValueName"]
        sourceValueId=record["SourceValueId"]
        sourceValueName=record["SourceValueName"]

        log.info("...restoring incremental history for %s from %s since %s" % (selectorValueName, sourceValueName, str(restoreStart)))

        # Restore values one at a time by selecting from the source of the selector
        SQL = "select rawValue, SampleTime, ReportTime from LtHistory where ValueId = ? and reportTime > ?"
        pdsVals = system.db.runPrepQuery(SQL, [sourceValueId, restoreStart], database)
        
        rows = 0
        for valRecord in pdsVals: 
            SQL = "Insert into ltHistory (valueId, rawValue, SampleTime, ReportTime) values (%i, ?, ?, ?)" % (selectorValueId)
            try:
                system.db.runPrepUpdate(SQL, [valRecord["rawValue"], valRecord["SampleTime"], valRecord["ReportTime"]], database)
                rows = rows + 1
            except:
                log.trace("Error restoring history for selector: %s, value: %s, sample time: %s" % (selectorValueName, str(valRecord["rawValue"]), str(valRecord["SampleTime"])))

        log.info("      ...inserted %i rows" % (rows))
        
        # We don't need to worry about writing the last value to the selector tags because the selector expressions should 
        # do that automatically when the source was restored.

