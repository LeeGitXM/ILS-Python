'''
Created on Apr 28, 2015

@author: Pete
'''
import system
import time
from java.util import Calendar
import ils.common.util as util
log = system.util.getLogger("com.ils.labData")


# History should be restored on startup, but generally the site needs to perform a site specific selector
# configuration BEFORE the history is performed.
def gateway():
    from ils.labData.version import version
    version, revisionDate = version()
    log.info("---------------------------------------------------------")
    log.info("Starting Lab Data Toolkit gateway version %s - %s" % (version, revisionDate))
    log.info("---------------------------------------------------------")
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
    system.tag.writeAll(tagNames, tagValues)
        

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
    data.append([path, "pollingEnabledIsolation", "Boolean", "False"])
    data.append([path, "standardDeviationsToValidityLimits", "Float8", "4.5"])
    data.append([path, "manualEntryPermitted", "Boolean", "False"])
    data.append([path, "communicationHealthy", "Boolean", "True"])
    data.append([path, "labDataWriteEnabled", "Boolean", "True"])
    data.append([path, "sqcPlotFreshDataColor", "String", "Green"])
    data.append([path, "sqcPlotStaleDataColor", "String", "Gray"])

    ds = system.dataset.toDataSet(headers, data)
    from ils.common.tagFactory import createConfigurationTags
    createConfigurationTags(ds, log)


def restoreHistory(tagProvider, historyProvider, daysToRestore=7):
    # This is run from a project startup script, so it should have the notion of a default database
    database = ""
    
    # wait for the HDA services to be available - We need lab data so this will hang the startup untill it is available
    allAvailable=waitForHDAInterfaces()
    if not(allAvailable):
        log.error("Unable to restore lab data history because the HDA server is unavailable!")
        return
    
    restoreValueHistory(tagProvider, historyProvider, daysToRestore, database)
    restoreSelectorHistory(tagProvider, daysToRestore, database)

def waitForHDAInterfaces(delay=5, iterations=20, database=""):
    print "Waiting for the HDA interfaces to come on-line..."
    
    SQL = "select distinct InterfaceName from LtPHDValueView"
    pds = system.db.runQuery(SQL, database)
    allAvailable=False
    cnt = 0
    while not(allAvailable) and cnt < iterations:
        print "Checking interfaces..."
        allAvailable=True
        for record in pds:
            hdaInterface = record["InterfaceName"]        
            serverIsAvailable=system.opchda.isServerAvailable(hdaInterface)
            if not(serverIsAvailable):
                allAvailable = False
        
        time.sleep(delay)
        cnt = cnt + 1

    return allAvailable

# When restoring a number of values for a parameter, the last value will be written to the 
# lab data tag so that it will propagate through to diagnostic.  Because this propagates values
# to tags this should be called after lab data selectors have been configured.  Therefore, 
# this is not automatically called as part of the lab data modules initialization but rather must
# be called from the site's site specific startup module.
def restoreValueHistory(tagProvider, historyProvider, daysToRestore=7, database=""):
    log.info("Restoring lab data value history...")
    
    tags=[]
    tagValues=[]
    fetchGradeHistoryForUnits=[]
    gradeHistory={}
    
    # Calculate the start and end dates that will be used if no data is found
    endDate = util.getDate()
    cal = Calendar.getInstance()
 
    cal.setTime(endDate)
    cal.add(Calendar.HOUR, daysToRestore * -24)
    restoreStart = cal.getTime()
    
    log.info("...restoring incremental history since %s" % (str(restoreStart)))
    
    # Fetch the set of lab values that we need to get from PHD
    SQL = "select UnitName, ValueId, ValueName, ItemId, InterfaceName from LtPHDValueView"
    pds = system.db.runQuery(SQL, database)
    for record in pds:
        hdaInterface = record["InterfaceName"]
        valueId=record["ValueId"]
        valueName=record["ValueName"]
        itemId=record["ItemId"]
        unitName=record["UnitName"]
        
        if unitName not in fetchGradeHistoryForUnits:
            fetchGradeHistoryForUnits.append(unitName)
            gradeHistory=fetchGradeHistory(gradeHistory, unitName, daysToRestore, historyProvider)
            print "The grade history is: ", gradeHistory
        
        serverIsAvailable=system.opchda.isServerAvailable(hdaInterface)
        if not(serverIsAvailable):
            log.error("HDA interface %s is not available - unable to restore history!" % (hdaInterface))
        else:
            log.info("---------------------")
            log.info("...reading lab data values from HDA for %s - %s - %s- %s" % (valueId, valueName, itemId, hdaInterface))

            itemIds=[itemId]

            maxValues=0
            boundingValues=0
            retVals=system.opchda.readRaw(hdaInterface, itemIds, restoreStart, endDate, maxValues, boundingValues)
        
            valueList=retVals[0]
            
            if str(valueList.serviceResult) != 'Good':
                log.error("   -- The returned value for %s was %s --" % (itemId, valueList.serviceResult))
        
            elif valueList.size()==0:
                log.error("   -- no data found for %s --" % (itemId))

            else:
                log.info("   ...fetched %i records from HDA..." % (valueList.size()))    
                lastValueId = None
                
                rows = 0
                for qv in valueList:
                    rawValue=qv.value
                    sampleTime=qv.timestamp
                    quality=qv.quality
                    grade=getGradeForHistoricLabValue(gradeHistory, unitName, sampleTime) 
                    
                    if quality.isGood():
                        from ils.labData.scanner import insertHistoryValue
                        success,insertedRows=insertHistoryValue(valueName, valueId, rawValue, sampleTime, grade, database)
                        if success and insertedRows > 0:
                            log.info("     ...inserted %s : %s (Grade: %s)" % (str(rawValue), str(sampleTime), str(grade)))
                            rows=rows+insertedRows
                            
                log.info("   ...restored %i rows" % (rows))

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
    
    system.tag.writeAll(tags, tagValues)

def fetchGradeHistory(gradeHistory, unitName, daysToRestore, historyProvider):
    import datetime
    ds=gradeHistory.get("unitName", None)
    if ds==None:
        log.trace("Fetching grade history for unit %s..." % (unitName))
        tagPath="[%s]Site/%s/Grade/grade" % (historyProvider, unitName)
        endTime = datetime.datetime.now()
        rangeHours = -1 * 24 * daysToRestore
        ds = system.tag.queryTagHistory(
                paths=[tagPath],
                endTime=endTime, 
                rangeHours=rangeHours, 
                aggregationMode="LastValue",
                noInterpolation=True,
                includeBoundingValue=False
                )
        gradeHistory[unitName]=ds

    return gradeHistory

def getGradeForHistoricLabValue(gradeHistory, unitName, sampleTime):
    ds=gradeHistory.get(unitName, None)
    if ds==None:
        print "Could not find the grade history for: ", unitName, " in ", gradeHistory
        return -1
    
    lastGrade=None
    pds=system.dataset.toPyDataSet(ds)
    for record in pds:
        historyTime=record[0]
        grade=record[1]
        if sampleTime <= historyTime:
            log.trace("...found grade %s" % (str(grade)))
            return lastGrade
        lastGrade=grade
        
    log.warn("-- Did not find a grade for unit %s at %s --" % (unitName, str(sampleTime)))
    return lastGrade

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

