'''
Created on Apr 28, 2015

@author: Pete
'''
import system
from java.util import Calendar
import ils.common.util as util
log = system.util.getLogger("com.ils.labData")

def gateway():
    from ils.labData.version import version
    version, revisionDate = version()
    log.info("Starting Lab Data Toolkit gateway version %s - %s" % (version, revisionDate))
    from ils.common.config import getTagProvider
    provider = getTagProvider()
    createTags("[" + provider + "]")
    
    # History should be restored on startup, but generally the site needs to perform a site specific selector
    # configuration BEFORE the history is performed.
    

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
    restoreSelectorHistory(tagProvider, database)

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
    SQL = "select UnitName, ValueId, ValueName, ItemId, SampleTime, InterfaceName from LtPHDValueView"
    pds = system.db.runQuery(SQL, database)
    for record in pds:
        hdaInterface = record["InterfaceName"]
        valueId=record["ValueId"]
        valueName=record["ValueName"]
        itemId=record["ItemId"]
        sampleTime=record["SampleTime"]
        unitName=record["UnitName"]
        
        serverIsAvailable=system.opchda.isServerAvailable(hdaInterface)
        if not(serverIsAvailable):
            log.error("HDA interface %s is not available - unable to restore history!" % (hdaInterface))
        else:
            log.trace("---------------------")
            log.trace("...reading lab data values from HDA for %s - %s - %s- %s - %s" % (valueId, valueName, itemId, sampleTime, hdaInterface))

            itemIds=[itemId]
        
            if sampleTime == None:
                startDate = restoreStart
                log.trace("No history found for %s - restoring all data since %s" % (valueName, str(startDate)))
            else:
                startDate = sampleTime
                log.trace("...restoring incremental history for %s since %s" % (valueName, str(startDate)))
            
            maxValues=0
            boundingValues=0
            retVals=system.opchda.readRaw(hdaInterface, itemIds, startDate, endDate, maxValues, boundingValues)
        
            valueList=retVals[0]
            if str(valueList.serviceResult) != 'Good':
                log.error("   -- The returned value for %s was %s --" % (itemId, valueList.serviceResult))
        
            elif valueList.size()==0:
                log.error("   -- no data found for %s --" % (itemId))

            else:
                id = None
                
                try:
                    for lastQV in valueList:
                        rawValue=lastQV.value
                        sampleTime=lastQV.timestamp
                        quality=lastQV.quality
                        log.trace("   %s : %s : %s" % (str(rawValue), str(sampleTime), str(quality)))
                        if quality.isGood():
                            log.trace("      ...inserting...")
                            SQL = "insert into LtHistory (ValueId, RawValue, SampleTime, ReportTime) values (?, ?, ?, getdate())"
                            id=system.db.runPrepUpdate(SQL, [valueId, rawValue, sampleTime],getKey=True)
                except:
                    log.trace("Error restoring a value for %s - probably due to a duplicate value" % (valueName))
                    
                if id != None:
                    # Write the last value to the tag and then to LastHistoryUd in LtValue
                    SQL = "update ltValue set lastHistoryId = %i where valueId = %i" % (id, valueId)
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
    
    results=system.tag.writeAll(tags, tagValues)


# Restoring the history to selectors uses the data we just restored to the values
def restoreSelectorHistory(tagProvider, database=""):
    log.info("Restoring lab data selector history...")
    
    # Fetch the list of selectors and process them one at a time 
    SQL = "select S.valueId SelectorValueId, V1.valueName SelectorValueName, S.SourceValueId, V2.ValueName SourceValueName, "\
        " H.ReportTime "\
        " from LtSelector S, LtValue V1, LtValue V2, LtHistory H"\
        " where S.ValueId = V1.ValueId "\
        " and S.SourceValueId = V2.ValueId "\
        " and V2.LastHistoryId = H.HistoryId"
    print SQL
    pds = system.db.runQuery(SQL, database)
    for record in pds:
        print "processing..."
        selectorValueId=record["SelectorValueId"]
        selectorValueName=record["SelectorValueName"]
        sourceValueId=record["SourceValueId"]
        sourceValueName=record["SourceValueName"]
        reportTime=record["ReportTime"]

        # Insert by selecting from one table into the other...
        log.trace("...restoring selector lab data %s from %s whose last value was read at %s" % (selectorValueName, sourceValueName, str(reportTime)))
        SQL = "Insert into ltHistory (valueId, rawValue, SampleTime, ReportTime) "\
            " select %i, rawValue, SampleTime, ReportTime "\
            " from LtHistory where ValueId = ? and reportTime > ?" % (selectorValueId)
        rows = system.db.runPrepUpdate(SQL, [sourceValueId, reportTime], database)
        print "   ...inserted %i rows" % (rows)
        
        # We don't need to worry about writing the last value to the selector tags because the selector expressions should 
        # do that automatically when the source was restored.

