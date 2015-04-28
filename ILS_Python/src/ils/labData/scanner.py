'''
Created on Mar 27, 2015

@author: Pete
'''
import system

# This should persist from one run to the next
lastValueCache = {}

# The purpose of this module is to scan / poll of of the lab data points for new values

def main(database, tagProvider):
    print "In labData.scanner.main()", database, tagProvider

    print "Last Value Cache: ", lastValueCache
    if len(lastValueCache) == 0:
        initializeCache(database)
    
    from ils.labData.limits import fetchLimits
    limits=fetchLimits(database)    
    checkForNewPHDLabValues(database, tagProvider, limits)
    
def checkForNewPHDLabValues(database, tagProvider, limits):
    print "Checking for new Lab values from PHD... "
    
    # Fetch the set of lab values that we need to get from PHD
    SQL = "select Post, ValueId, ValueName, ItemId, InterfaceName from LtPHDValueView"
    pds = system.db.runQuery(SQL, database) 
    
    for record in pds:
        post=record["Post"]
        valueId=record["ValueId"]
        valueName=record["ValueName"]
        itemId=record["ItemId"]
        interfaceName=record["InterfaceName"]
        checkForNewLabValue(post, valueId, valueName, itemId, interfaceName, database, tagProvider, limits)

def checkForNewLabValue(post, valueId, valueName, itemId, interfaceName, database, tagProvider, limits):
    print "Checking for a new lab value for: ", valueName, itemId 
    
    # For simulation and testing purposes, I am going to read the latest tag value from a SQL*Server 
    # Database and hope that Colby can give me an API to do the same thing.
    
    SQL = "select top 1 value, sampleTime from LabDataSimulator where itemId = '%s' order by sampleTime desc" % (itemId)
    pds=system.db.runQuery(SQL, "XOMMigration")
    
    if len(pds)==1:
        record=pds[0]
        rawValue=record['value']
        sampleTime=record['sampleTime']
        if lastValueCache.has_key(valueName):
            print "...there is a value in the cache"
            lastValue=lastValueCache.get(valueName)
            if lastValue.get('rawValue') != rawValue or lastValue.get('sampleTime') != sampleTime:
                print "...found a new value because it does not match what is in the cache..."
                handleNewLabValue(post, valueId, valueName, rawValue, sampleTime, database, tagProvider, limits)
            # TODO Check if the lab value is newer than the cache
        else:
            print "...found a new value because %s does not exist in the cache..." % valueName
            handleNewLabValue(post, valueId, valueName, rawValue, sampleTime, database, tagProvider, limits)

# Handle a new value.  The first thing to do is to check the limits.  If there are validity limits and the value is outside the 
# limits then operator intervention is required before storing the value.  If there are no limits or the value is within the validity limits
# then store the value automatically
def handleNewLabValue(post, valueId, valueName, rawValue, sampleTime, database, tagProvider, limits):
    print "...handling a new lab value for %s..." % (valueName)

    # Evaluate limits - This checks all limit types, but only the result of the validity check is returned 
#    from ils.labData.limits import check
    
    
#    def check(post, valueId, valueName, rawValue, sampleTime, database, tagProvider, limits):
    print "Checking limits for... ", valueName
    
    validSQC = True
    for limit in limits:
        if limit.get("ValueName","") == valueName:
            print "Found a limit: ", limit
            from ils.labData.limits import checkValidityLimit
            validValidity,upperLimit,lowerLimit=checkValidityLimit(post, valueId, valueName, rawValue, sampleTime, database, tagProvider, limit)
            
            from ils.labData.limits import checkSQCLimit
            validSQC=checkSQCLimit(post, valueId, valueName, rawValue, sampleTime, database, tagProvider, limit)
            
            from ils.labData.limits import checkReleaseLimit
            validRelease=checkReleaseLimit(valueId, valueName, rawValue, sampleTime, database, tagProvider, limit)
        
    # If the value is valid then store it to the database and write the value and sample time to the tag (UDT)
    if validValidity:
        storeValue(valueId, valueName, rawValue, sampleTime, database, tagProvider, True)
    else:
        from ils.labData.validityLimitWarning import notify
        notify(post, valueName, valueId, rawValue, sampleTime, tagProvider, upperLimit, lowerLimit)


# Store a new lab value.  This has 4 steps:
#   1) Insert into LtHistory
#   2) Update LtValue with the id of the latest history value
#   3) Insert the latest value into the Cache
#   4) Write the value and sample time to the tag (UDT)
# This is called by one of two callers - directly by the scanner if the value is good or if the value is outside the limits and 
# the operator presses accept 
def storeValue(valueId, valueName, rawValue, sampleTime, database, tagProvider, valid):
    print "Storing..."
    # Step 1 - Insert the value into the lab history table.
    SQL = "insert into LtHistory (valueId, RawValue, SampleTime, ReportTime) values (?, ?, ?, getdate())"
    historyId = system.db.runPrepUpdate(SQL, [valueId, rawValue, sampleTime], database, getKey=1)
    
    # Step 2 - Update LtValue with the id of the latest value
    SQL = "update LtValue set LastHistoryId = %i where valueId = %i" % (historyId, valueId)
    system.db.runUpdateQuery(SQL, database) 
    
    # Step 3 - update the cache
    # TODO add reportTime here
    lastValueCache[valueName]={'valueId': valueId, 'rawValue': rawValue, 'sampleTime': sampleTime}
    
    updateTags(tagProvider, valueName, rawValue, sampleTime, valid)
    
# Update the Lab Data UDT tags
def updateTags(tagProvider, valueName, rawValue, sampleTime, valid):
    tagName="[%s]LabData/%s" % (tagProvider, valueName)
    
    # Always write the raw value and the sample time
    tags=[tagName + "/rawValue", tagName + "/sampleTime"]
    vals=[rawValue, sampleTime]
    
    if valid:
        tags.append(tagName + "/value")
        vals.append(rawValue)
        tags.append(tagName + "/badValue")
        vals.append(False)
        
    else:
        tags.append(tagName + "/badValue")
        vals.append(True)
        
    print "Writing ", vals, " to ", tags
    system.tag.writeAll(tags, vals)

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