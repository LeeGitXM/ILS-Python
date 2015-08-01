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
    restoreHistory(provider)

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

def restoreHistory(tagProvider):
    log.info("Restoring lab data history...")
    
    tags=[]
    tagValues=[]
    
    # This is run from a project startup script, so it should have the notion of a default database
    database = ""
    
    # Calculate the start and end dates that will be used if no data is found
    endDate = util.getDate()
    cal = Calendar.getInstance()
 
    cal.setTime(endDate)
    cal.add(Calendar.HOUR, -7 * 24)
    oneWeekAgo = cal.getTime()
    
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
                startDate = oneWeekAgo
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
                for lastQV in valueList:
                    rawValue=lastQV.value
                    sampleTime=lastQV.timestamp
                    quality=lastQV.quality
                    log.trace("   %s : %s : %s" % (str(rawValue), str(sampleTime), str(quality)))
                    if quality.isGood():
                        log.trace("      ...inserting...")
                        SQL = "insert into LtHistory (ValueId, RawValue, SampleTime, ReportTime) values (?, ?, ?, getdate())"
                        id=system.db.runPrepUpdate(SQL, [valueId, rawValue, sampleTime],getKey=True)
                
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
