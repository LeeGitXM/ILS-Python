'''
Created on Mar 27, 2015

@author: Pete
'''
import system
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.labData")
import ils.common.util as util

# This should persist from one run to the next
lastValueCache = {}

# The purpose of this module is to scan / poll of of the lab data points for new values

def main(database, tagProvider):
    log.info("Scanning for lab data (%s, %s)..." % (database, tagProvider))

    log.trace("Last Value Cache: %s" % (str(lastValueCache)))
    if len(lastValueCache) == 0:
        initializeCache(database)
    
    from ils.labData.limits import fetchLimits
    limits=fetchLimits(database)    
    checkForNewLabValues(database, tagProvider, limits)
    
    log.trace("The updated last Value Cache is: %s" % (str(lastValueCache)))


def checkForNewLabValues(database, tagProvider, limits):
    log.info("Checking for new Lab values ... ")
    
    endDate = util.getDate()
    from java.util import Calendar
    cal = Calendar.getInstance()
 
    cal.setTime(endDate)
    cal.add(Calendar.HOUR, -8)
    startDate = cal.getTime()
    
    # Fetch the set of lab values that we need to get from PHD
    SQL = "Select distinct InterfaceName from LtPHDValueView"
    interfacePDS = system.db.runQuery(SQL, database)
    for interfaceRecord in interfacePDS:
        hdaInterface = interfaceRecord["InterfaceName"]
        print "...reading lab data values from HDA server: %s..." % (hdaInterface)
        
        # Now select the itemIds that use that interface
        SQL = "select Post, ValueId, ValueName, ItemId from LtPHDValueView where InterfaceName = '%s'" % (hdaInterface)
        tagInfoPds = system.db.runQuery(SQL, database) 
        itemIds=[]
        for record in tagInfoPds:
            itemIds.append(record["ItemId"])

        maxValues=0
        boundingValues=0
        retVals=system.opchda.readRaw(hdaInterface, itemIds, startDate, endDate, maxValues, boundingValues)
        print "...back from HDA read!"
        print "retVals: ", retVals
        
        if len(tagInfoPds) != len(retVals):
            print "The number of elements in the tag info dataset does not match the number of values returned!"
            return
    
        writeTags=[]
        writeTagValues=[]
    
        for i in range(len(tagInfoPds)):
            tagInfo=tagInfoPds[i]
            valueList=retVals[i]

            post=tagInfo["Post"]
            valueId=tagInfo["ValueId"]
            valueName=tagInfo["ValueName"]
            itemId=tagInfo["ItemId"]

            writeTags, writeTagValues = checkForNewLabValue(post, valueId, valueName, itemId, database, tagProvider, \
                                                        limits, tagInfo, valueList, writeTags, writeTagValues)
        
        log.trace("Writing %s to %s" % (str(writeTagValues), str(writeTags)))
        system.tag.writeAll(writeTags, writeTagValues)


def checkForNewLabValue(post, valueId, valueName, itemId, database, tagProvider, limits, tagInfo, valueList, writeTags, writeTagValues):
    log.trace("Checking for a new lab value for: %s - %s..." % (str(valueName), str(itemId)))
    
    if str(valueList.serviceResult) != 'Good':
        print "   -- The returned value for %s was %s --" % (itemId, valueList.serviceResult)
        return writeTags, writeTagValues
    
    if valueList.size()==0:
        print "   -- no data found for %s --" % (itemId)
        return writeTags, writeTagValues
    
    # Get the last value out of the list of values - I couldn't find a way to get this directlt, but there must be a way
#    lastQV=valueList[valueList.size()-1]
    for lastQV in valueList:
        pass
        
    rawValue=lastQV.value
    sampleTime=lastQV.timestamp
    quality=lastQV.quality
    
    log.trace("...checking value %s at %s (%s)..." % (str(rawValue), str(sampleTime), quality))
    if lastValueCache.has_key(valueName):
        log.trace("...there is a value in the cache")
        lastValue=lastValueCache.get(valueName)
        if lastValue.get('rawValue') != rawValue or lastValue.get('sampleTime') != sampleTime:
            log.trace("...found a new value because it does not match what is in the cache...")
            writeTags, writeTagValues = handleNewLabValue(post, valueId, valueName, rawValue, sampleTime, database, tagProvider, limits, writeTags, writeTagValues)
            # TODO Check if the lab value is newer than the cache
    else:
        log.trace("...found a new value because %s does not exist in the cache..." % (valueName))
        writeTags, writeTagValues = handleNewLabValue(post, valueId, valueName, rawValue, sampleTime, database, tagProvider, limits, writeTags, writeTagValues)

    return writeTags, writeTagValues


# Handle a new value.  The first thing to do is to check the limits.  If there are validity limits and the value is outside the 
# limits then operator intervention is required before storing the value.  If there are no limits or the value is within the validity limits
# then store the value automatically
def handleNewLabValue(post, valueId, valueName, rawValue, sampleTime, database, tagProvider, limits, writeTags, writeTagValues):
    log.trace("...handling a new lab value for %s, checking limits" % (valueName))
    
    validValidity = True
    for limit in limits:
        if limit.get("ValueName","") == valueName:
            log.trace("Found a limit: %s" % (str(limit)))
            from ils.labData.limits import checkValidityLimit
            validValidity,upperLimit,lowerLimit=checkValidityLimit(post, valueId, valueName, rawValue, sampleTime, database, tagProvider, limit)
            
            from ils.labData.limits import checkSQCLimit
            validSQC=checkSQCLimit(post, valueId, valueName, rawValue, sampleTime, database, tagProvider, limit)
            
            from ils.labData.limits import checkReleaseLimit
            validRelease=checkReleaseLimit(valueId, valueName, rawValue, sampleTime, database, tagProvider, limit)
        
    # If the value is valid then store it to the database and write the value and sample time to the tag (UDT)
    if validValidity:
        storeValue(valueId, valueName, rawValue, sampleTime, database)
        writeTags, writeTagValues = updateTags(tagProvider, valueName, rawValue, sampleTime, True, writeTags, writeTagValues)
        updateCache(valueId, valueName, rawValue, sampleTime)
    else:
        from ils.labData.validityLimitWarning import notify
        notify(post, valueName, valueId, rawValue, sampleTime, tagProvider, database, upperLimit, lowerLimit)
        writeTags, writeTagValues = updateTags(tagProvider, valueName, rawValue, sampleTime, False, writeTags, writeTagValues)
        updateCache(valueId, valueName, rawValue, sampleTime)
        
    return writeTags, writeTagValues


# Store a new lab value.  Insert the value into LtHistory and update LtValue with the id of the latest history value.
# This is called by one of two callers - directly by the scanner if the value is good or if the value is outside the limits and 
# the operator presses accept 
def storeValue(valueId, valueName, rawValue, sampleTime, database):
    log.trace("Storing %s..." % (valueName))
    # Step 1 - Insert the value into the lab history table.
    SQL = "insert into LtHistory (valueId, RawValue, SampleTime, ReportTime) values (?, ?, ?, getdate())"
    historyId = system.db.runPrepUpdate(SQL, [valueId, rawValue, sampleTime], database, getKey=1)
    
    # Step 2 - Update LtValue with the id of the latest value
    SQL = "update LtValue set LastHistoryId = %i where valueId = %i" % (historyId, valueId)
    system.db.runUpdateQuery(SQL, database)

# This is called by a selector tag change script.  There is a listener on the SampleTime and on the value.  They both call this handler.
# When a measurement is received from the lab system the sampleTime tag and the value tag are updated almost atomically.  That action
# will fire off two calls to this procedure, this procedure doesn't know or care who called it.  It will read both tags to get the 
# current value.  Two identical insert statements will be attempted but the database will reject the second because of the unique index.
def storeSelector(tagPath, database):
    print "TagPath: ", tagPath
    if tagPath.find('/value') > 0:
        path=tagPath[:tagPath.find("/value")]
    else:
        path=tagPath[:tagPath.find("/sampleTime")]
    print "Path: <%s>" % (path)
    valueName=path[path.find('LabData/') + 8:]
    print "Value name: <%s>" % (valueName)

    # Read the value and the sample time
    vals = system.tag.readAll([path + '/value', path + '/sampleTime'])
    value=vals[0].value
    sampleTime=vals[1].value
    print "Handling %s at %s" % (str(value), str(sampleTime))
    
    # Fetch the value id using the name
    SQL = "select ValueId from LtValue where ValueName = '%s'" % (valueName)
    valueId=system.db.runScalarQuery(SQL)
    
    # If the value and the sample time tags are updated nearly simultaneously then there will be two parallel threads running.  There is 
    # a unique index on the history table so we do not need to worry about duplicate data, but we should catch the error and swallow it
    try:
        storeValue(valueId, valueName, value, sampleTime, database)
    except:
        print "Store failed - probably due to simultaeous updates to the value and the sample time."

    
def updateCache(valueId, valueName, rawValue, sampleTime):
    lastValueCache[valueName]={'valueId': valueId, 'rawValue': rawValue, 'sampleTime': sampleTime}

    
# Update the Lab Data UDT tags - this is called 
def updateTags(tagProvider, valueName, rawValue, sampleTime, valid, tags, tagValues):
    print "Updating tags..."
    tagName="[%s]LabData/%s" % (tagProvider, valueName)
    
    # Always write the raw value
    tags.append(tagName + "/rawValue")
    tagValues.append(rawValue)
    
    if valid:
        tags.append(tagName + "/sampleTime")
        tagValues.append(sampleTime)
        tags.append(tagName + "/value")
        tagValues.append(rawValue)
        tags.append(tagName + "/badValue")
        tagValues.append(False)
        
    else:
        tags.append(tagName + "/badValue")
        tagValues.append(True)
        
    return tags, tagValues


# This is called on startup to load the most recent measurement into the cache
def initializeCache(database):
    print "Initializing the last Value Cache..."
    
    SQL = "select * from LtLastValueView"
    pds = system.db.runQuery(SQL, database)
    for record in pds:
        valueName=record['ValueName']
        valueId=record['ValueId']
        rawValue=record['RawValue']
        sampleTime=record['SampleTime']
        reportTime=record['ReportTime']
        lastValueCache[valueName]={'valueId':valueId, 'rawValue': rawValue, 'sampleTime': sampleTime, 'reportTime': reportTime}
    print "Loaded %i measurements into the last value cache..." % (len(pds))
    print lastValueCache