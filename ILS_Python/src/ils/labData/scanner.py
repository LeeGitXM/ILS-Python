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
    
    from ils.labData.common import fetchLimits
    limitpds=fetchLimits(database)    
    checkForNewPHDLabValues(database, tagProvider, limitpds)
    
def checkForNewPHDLabValues(database, tagProvider, limitpds):
    print "Checking for new Lab values from PHD... "
    
    # Fetch the set of lab values that we need to get from PHD
    SQL = "select ValueId, ValueName, ItemId, InterfaceName from LtPHDValueView"
    pds = system.db.runQuery(SQL, database) 
    
    for record in pds:
        valueId=record["ValueId"]
        valueName=record["ValueName"]
        itemId=record["ItemId"]
        interfaceName=record["InterfaceName"]
        checkForNewLabValue(valueId, valueName, itemId, interfaceName, database, tagProvider, limitpds)

def checkForNewLabValue(valueId, valueName, itemId, interfaceName, database, tagProvider, limitpds):
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
            print "There is a value in the cache"
            lastValue=lastValueCache.get(valueName)
            if lastValue.get('rawValue') != rawValue or lastValue.get('sampleTime') != sampleTime:
                print "Storing the lab value because it does not match what is in the cache..."
                storeNewLabValue(valueId, valueName, rawValue, sampleTime, database, tagProvider, limitpds)
            # TODO Check if the lab value is newer than the cache
        else:
            print "Storing the lab value because %s does not exist in the cache..." % valueName
            storeNewLabValue(valueId, valueName, rawValue, sampleTime, database, tagProvider, limitpds)

# Store a new lab value.  This has 3 steps:
#   1) Insert into LtHistory
#   2) Update LtValue with the id of the latest history value
#   3) Insert the latest value into the Cache
#   4) Write the value and sample time to the tag (UDT) 
def storeNewLabValue(valueId, valueName, rawValue, sampleTime, database, tagProvider, limitpds):
    print "Storing a new lab value"
    
    # Step 1 - Insert the value into the lab history table.
    SQL = "insert into LtHistory (valueId, RawValue, SampleTime, ReportTime) values (?, ?, ?, getdate())"
    historyId = system.db.runPrepUpdate(SQL, [valueId, rawValue, sampleTime], database, getKey=1)
    
    # Step 2 - Update LtValue with the id of the latest value
    SQL = "update LtValue set LastHistoryId = %i where valueId = %i" % (historyId, valueId)
    system.db.runUpdateQuery(SQL, database) 
    
    # Step 3 - update the cache
    # TODO add reportTime here
    lastValueCache[valueName]={'valueId': valueId, 'rawValue': rawValue, 'sampleTime': sampleTime}
    
    # Step 4 - write the value and sample time to the tag (UDT)
    tagName="[%s]LabData/%s" % (tagProvider, valueName)
    tags=[tagName + "/rawValue", tagName + "/sampleTime"]
    vals=[rawValue, sampleTime]
    print "Writing ", vals, " to ", tags
    system.tag.writeAll(tags, vals)
    
    # Step 5 - evaluate limits
    from ils.labData.limits import check
    check(valueId, valueName, rawValue, database, tagProvider, limitpds)
    
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