'''
Created on Mar 27, 2015


@author: Pete
'''

# This import will show an error, but it is required to handle calculation methods that are in project scope.
import project 

import sys, system, string, traceback
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
from java.util import Calendar
log = LogUtil.getLogger("com.ils.labData")
derivedLog = LogUtil.getLogger("com.ils.labData.derivedValues")
import ils.common.util as util

# This should persist from one run to the next
lastValueCache = {}
triggerCache = {}
derivedCalculationCache = {}

# The purpose of this module is to scan / poll of of the lab data points for new values


def main(database, tagProvider):
    log.info("Scanning for lab data (%s, %s)..." % (database, tagProvider))

    log.trace("Last Value Cache: %s" % (str(lastValueCache)))
    if len(lastValueCache) == 0:
        initializeCache(database)
    
    from ils.labData.limits import fetchLimits
    limits=fetchLimits(database)
    writeTags=[]
    writeTagValues=[] 
    writeTags, writeTagValues = checkForNewPHDLabValues(database, tagProvider, limits, writeTags, writeTagValues)
    writeTags, writeTagValues = checkForNewDCSLabValues(database, limits, writeTags, writeTagValues)
    checkForDerivedValueTriggers(database)
    writeTags, writeTagValues = checkDerivedCalculations(database, tagProvider, writeTags, writeTagValues)
    
    log.trace("Writing %i new lab values to local lab data tags" % (len(writeTags)))
    system.tag.writeAll(writeTags, writeTagValues)

#-------------
# Handle a new value.  The first thing to do is to check the limits.  If there are validity limits and the value is outside the 
# limits then operator intervention is required before storing the value.  If there are no limits or the value is within the validity limits
# then store the value automatically
def checkForDerivedValueTriggers(database):
    derivedLog.trace("Checking the derived value triggers ... ")

    derivedLog.trace("------------------------------")
    derivedLog.trace("The derived value trigger cache is: %s" % (str(triggerCache)))

    SQL = "select * from LtDerivedValueView"
    pds = system.db.runQuery(SQL, database)
    for record in pds:
        valueName=record['ValueName']
        valueId=record['ValueId']
        derivedValueId=record['DerivedValueId']
        triggerValueName=record['TriggerValueName']
        triggerValueId=record['TriggerValueId']
        triggerRawValue=record['TriggerRawValue']
        triggerSampleTime=record['TriggerSampleTime']
        triggerReportTime=record['TriggerReportTime']
        
        derivedLog.trace("   checking %s which is triggered by %s" % (valueName, triggerValueName))
        
        tv=triggerCache.get(valueName,None)
        if tv == None:
            derivedLog.trace("%s was not in the trigger cache, adding it now..." % (valueName))
            
            d = {'valueName': valueName, 
                 'valueId':valueId, 
                 'derivedValueId':derivedValueId,
                 'triggerRawValue': triggerRawValue, 
                 'triggerSampleTime': triggerSampleTime, 
                 'triggerReportTime': triggerReportTime
                 }
            
            triggerCache[valueName]=d            
        else:
            # Get the values that were last processed
            lastTriggerRawValue = tv.get("triggerRawValue")
            lastTriggerSampleTime = tv.get("triggerSampleTime")
            
            if triggerSampleTime == lastTriggerSampleTime and triggerRawValue == lastTriggerRawValue:
                derivedLog.trace("   ...the trigger has not changed, nothing to do for this lab value ")
            else:
                derivedLog.trace("   ...the trigger value has changed, adding this derived value to the calculation cache...")
                
                # First update the trigger cache
                d = {'valueName': valueName, 
                 'valueId':valueId, 
                 'derivedValueId':derivedValueId,
                 'triggerRawValue': triggerRawValue, 
                 'triggerSampleTime': triggerSampleTime, 
                 'triggerReportTime': triggerReportTime
                 }

                derivedLog.trace("...updating %s in the trigger cache" % (str(d)))
                triggerCache[valueName]=d
                
                derivedValueCallback=record['Callback']
                sampleTimeTolerance=record['SampleTimeTolerance']
                newSampleWaitTime=record['NewSampleWaitTime']
                resultItemId=record['ResultItemId']
                resultServerName=record['ResultServerName']
                unitName=record['UnitName']

                # Fetch the related data
                SQL = "select V.ValueId, V.ValueName  "\
                    " from LtValue V, LtRelatedData RD "\
                    " where RD.DerivedValueId = %s "\
                    " and RD.RelatedValueId = V.ValueId" % (derivedValueId) 

                relatedData=[]
                pds = system.db.runQuery(SQL, database)
                for record in pds:
                    relatedValueName=record["ValueName"]
                    relatedValueId=record["ValueId"]
                    relatedData.append({'relatedValueName': relatedValueName, 'relatedValueId': relatedValueId})
                
                d = {'valueName': valueName, 
                     'valueId':valueId, 
                     'unitName':unitName,
                     'triggerRawValue': triggerRawValue, 
                     'triggerSampleTime': triggerSampleTime, 
                     'triggerReportTime': triggerReportTime,
                     'sampleTimeTolerance': sampleTimeTolerance,
                     'newSampleWaitTime': newSampleWaitTime,
                     'relatedData': relatedData,
                     'derivedValueCallback': derivedValueCallback,
                     'resultItemId': resultItemId,
                     'resultServerName': resultServerName}
                
                derivedLog.trace("...adding %s to the calculation cache" % (str(d)))
                
                derivedCalculationCache[valueName]=d


# The logic that drives the derived calculations is a little different here than in the old system.  In the old system each 
# calculation procedure had the responsibility to collect consistent lab data.  In the new framework, the engine will collect
# all of the necessary information and then call the calculation method.
def checkDerivedCalculations(database, tagProvider, writeTags, writeTagValues):
    derivedLog.info("Checking the derived calculations...")
    
    cal = Calendar.getInstance()
    
    for d in derivedCalculationCache.values():
        valueName=d.get("valueName", "")
        derivedLog.trace("... checking %s" % (valueName))
        valueId=d.get("valueId", -1)
        unitName=d.get("unitName","")
        callback=d.get("derivedValueCallback", "")
        rawValue=d.get("triggerRawValue", 0.0)
        sampleTime=d.get("triggerSampleTime", None)
        reportTime=d.get("triggerReportTime", None)
        sampleTimeTolerance=d.get("sampleTimeTolerance", 0.0)
        newSampleWaitTime=d.get("newSampleWaitTime", 0.0)
        resultServerName=d.get("resultServerName", "")
        resultItemId=d.get("resultItemId", "")
        
        # Determine the time window that the related data must fall within
        cal.setTime(sampleTime)
        cal.add(Calendar.MINUTE, -1 * sampleTimeTolerance)
        sampleTimeWindowStart = cal.getTime()
        
        cal.setTime(sampleTime)
        cal.add(Calendar.MINUTE, sampleTimeTolerance)
        sampleTimeWindowEnd = cal.getTime()
        
        relatedDataIsConsistent=True
        
        # Put together a data dictionary for the callback - start with the trigger value
        dataDictionary={}
        dataDictionary[valueName]={'valueName': valueName, 
                                   'valueId': valueId, 
                                   'rawValue': rawValue,
                                   'trigger': True}
                            
        relatedDataList=d.get("relatedData", [])
        for relatedData in relatedDataList:
            relatedValueName=relatedData.get("relatedValueName","")
            relatedValueId=relatedData.get("relatedValueId",-1)
            
            SQL = "select RawValue, SampleTime from LtHistory H, LtValue V "\
                " where V.ValueId = %s and V.LastHistoryId = H.HistoryId" % (str(relatedValueId))
            pds=system.db.runQuery(SQL, database)
            if len(pds) == 1:
                record=pds[0]
                rv=record["RawValue"]
                st=record["SampleTime"]
                derivedLog.trace("      found %f at %s for related data named: %s" % (rv, str(st), relatedValueName))
                
                if st >= sampleTimeWindowStart and st <= sampleTimeWindowEnd:
                    derivedLog.trace("      --- The related data's sample time is within the sample time window! ---")
                    
                    dataDictionary[relatedValueName]={'valueName': relatedValueName, 
                                            'valueId':relatedValueId, 
                                            'rawValue': rv,
                                            'trigger': False}
                    
                else:
                    derivedLog.trace("      --- The related data's sample time is NOT within the sample time window! ---")
                    relatedDataIsConsistent = False
            else:
                derivedLog.error("Unable to find any value for the related data named %s for trigger value %s" % (relatedValueName, valueName))
        
        if relatedDataIsConsistent:
            # If they specify shared or project scope, then we don't need to do this
            if not(string.find(callback, "project") == 0 or string.find(callback, "shared") == 0):
                # The method contains a full python path, including the method name
                separator=string.rfind(callback, ".")
                packagemodule=callback[0:separator]
                separator=string.rfind(packagemodule, ".")
                package = packagemodule[0:separator]
                module  = packagemodule[separator+1:]
                derivedLog.trace("Using External Python, the package is: <%s>.<%s>" % (package,module))
                exec("import %s" % (package))
                exec("from %s import %s" % (package,module))
        
            try:
                derivedLog.trace("Calling %s and passing %s" % (callback, str(dataDictionary)))
                newVal = eval(callback)(dataDictionary)
                derivedLog.trace("The value returned from the calculation method is: %s" % (str(newVal)))
                
                # Use the sample time of the triggerValue and store the value in the database and in the UDT tags
                storeValue(valueId, valueName, newVal, sampleTime, database)
                
                # This updates the Lab Data UDT tags
                writeTags, writeTagValues = updateTags(tagProvider, unitName, valueName, newVal, sampleTime, True, writeTags, writeTagValues)
                
                # Derived lab data also has a target OPC tag that it needs to update - do this immediately
                system.opc.writeValue(resultServerName, resultItemId, newVal)
                
                # Remove this derived variable from the open calculation cache
                del derivedCalculationCache[valueName]
                
            except:
                errorType,value,trace = sys.exc_info()
                errorTxt = traceback.format_exception(errorType, value, trace, 500)
                derivedLog.error("Caught an exception calling calculation method named %s... \n%s" % (callback, errorTxt) )
                return writeTags, writeTagValues
        else:
            derivedLog.trace("The lab data is not consistent, check if we should give up...")
            from java.util import Date
            now = Date()
            
            # Determine the time window that we will keep trying (this just has an end time)
            cal.setTime(reportTime)
            cal.add(Calendar.MINUTE, newSampleWaitTime)
            newSampleWaitEnd = cal.getTime()
            
            if now > newSampleWaitEnd:
                derivedLog.trace("The  related sample has still not arrived and probably never will, time to give up!")
                del derivedCalculationCache[valueName]

    derivedLog.trace(" ...done processing the derived values for this cycle... ")

    return writeTags, writeTagValues

#-------------
def checkForNewDCSLabValues(database, limits, writeTags, writeTagValues):
    log.trace("Checking for new DCS Lab values ... ")
    
    SQL = "select distinct ServerName "\
        "FROM TkWriteLocation WL, LtDCSValue DV "\
        "WHERE DV.WriteLocationId = WL.WriteLocationId "
    pds = system.db.runQuery(SQL, database)
    for record in pds:
        serverName = record["ServerName"]
        readDCSLabValues(serverName, database)

    return writeTags, writeTagValues

def readDCSLabValues(serverName, database):
    log.trace("Reading DCS lab values from %s" % (serverName))
    
    SQL = "select ValueId, ItemId "\
        "FROM TkWriteLocation WL, LtDCSValue DV "\
        "WHERE DV.WriteLocationId = WL.WriteLocationId "\
        " AND WL.ServerName = '%s'" % (serverName)
    pds = system.db.runQuery(SQL, database)
    
    valueIds=[]
    itemIds=[]
    for record in pds:
        valueId = record["ValueId"]
        itemId = record["ItemId"]
        
        itemIds.append(itemId)
        valueIds.append(valueId)

    log.trace("Reading: %s" % (str(itemIds)))
    qvs = system.opc.readValues(serverName, itemIds)
    log.trace("Returned: %s" % str(qvs))
    
    
def checkForNewPHDLabValues(database, tagProvider, limits, writeTags, writeTagValues):
    log.trace("Checking for new PHD Lab values ... ")
    
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
        serverIsAvailable=system.opchda.isServerAvailable(hdaInterface)
        if not(serverIsAvailable):
            log.error("HDA interface %s is not available!" % (hdaInterface))
        else:
            log.trace("...reading lab data values from HDA server: %s..." % (hdaInterface))

            # Now select the itemIds that use that interface
            SQL = "select Post, UnitName, ValueId, ValueName, ItemId "\
                " from LtPHDValueView where InterfaceName = '%s'" % (hdaInterface)
            tagInfoPds = system.db.runQuery(SQL, database) 
            itemIds=[]
            for record in tagInfoPds:
                itemIds.append(record["ItemId"])

            maxValues=0
            boundingValues=0
            retVals=system.opchda.readRaw(hdaInterface, itemIds, startDate, endDate, maxValues, boundingValues)
            log.trace("...back from HDA read, read %i values!" % (len(retVals)))
#        log.trace("retVals: %s" % (str(retVals)))
        
            if len(tagInfoPds) != len(retVals):
                log.error("The number of elements in the tag info dataset does not match the number of values returned!")
                return writeTags, writeTagValues
    
            for i in range(len(tagInfoPds)):
                tagInfo=tagInfoPds[i]
                valueList=retVals[i]

                post=tagInfo["Post"]
                unitName=tagInfo["UnitName"]
                valueId=tagInfo["ValueId"]
                valueName=tagInfo["ValueName"]
                itemId=tagInfo["ItemId"]

                writeTags, writeTagValues = checkForANewPHDLabValue(post, unitName, valueId, valueName, itemId, \
                    database, tagProvider, limits, tagInfo, valueList, writeTags, writeTagValues)
        
    log.trace("Writing %s to %s" % (str(writeTagValues), str(writeTags)))

    log.trace("Done reading PHD lab values")
    return writeTags, writeTagValues

def checkForANewPHDLabValue(post, unitName, valueId, valueName, itemId, database, tagProvider, limits, tagInfo, valueList, writeTags, writeTagValues):
    log.trace("Checking for a new lab value for: %s - %s..." % (str(valueName), str(itemId)))
    
    if str(valueList.serviceResult) != 'Good':
        log.warn("   -- The returned value for %s was %s --" % (itemId, valueList.serviceResult))
        return writeTags, writeTagValues
    
    if valueList.size()==0:
        log.trace("   -- no data found for %s --" % (itemId))
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
        lastValue=lastValueCache.get(valueName)
        log.trace("...there is a value in the cache")
        if lastValue.get('rawValue') != rawValue or lastValue.get('sampleTime') != sampleTime:
            log.trace("...found a new value because it does not match what is in the cache (%s - %s)..." % (str(lastValue.get('rawValue')), str(lastValue.get('sampleTime'))))
            writeTags, writeTagValues = handleNewLabValue(post, unitName, valueId, valueName, rawValue, sampleTime, \
                    database, tagProvider, limits, writeTags, writeTagValues)
            # TODO Check if the lab value is newer than the cache
        else:
            log.trace("...this value is already in the cache so it will be ignored...")
    else:
        log.trace("...found a new value because %s does not exist in the cache..." % (valueName))
        writeTags, writeTagValues = handleNewLabValue(post, unitName, valueId, valueName, rawValue, sampleTime, \
                 database, tagProvider, limits, writeTags, writeTagValues)

    return writeTags, writeTagValues


# Handle a new value.  The first thing to do is to check the limits.  If there are validity limits and the value is outside the 
# limits then operator intervention is required before storing the value.  If there are no limits or the value is within the validity limits
# then store the value automatically
def handleNewLabValue(post, unitName, valueId, valueName, rawValue, sampleTime, database, tagProvider, limits, writeTags, writeTagValues):
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
        writeTags, writeTagValues = updateTags(tagProvider, unitName, valueName, rawValue, sampleTime, True, writeTags, writeTagValues)
        updateCache(valueId, valueName, rawValue, sampleTime)
    else:
        from ils.labData.validityLimitWarning import notify
        notify(post, valueName, valueId, rawValue, sampleTime, tagProvider, database, upperLimit, lowerLimit)
        writeTags, writeTagValues = updateTags(tagProvider, unitName, valueName, rawValue, sampleTime, False, writeTags, writeTagValues)
        updateCache(valueId, valueName, rawValue, sampleTime)
        
    return writeTags, writeTagValues


# Store a new lab value.  Insert the value into LtHistory and update LtValue with the id of the latest history value.
# This is called by one of two callers - directly by the scanner if the value is good or if the value is outside the limits and 
# the operator presses accept 
def storeValue(valueId, valueName, rawValue, sampleTime, database):
    log.trace("Storing %s - %s - %s - %s ..." % (valueName, str(valueId), str(rawValue), str(sampleTime)))
    try:
        # Step 1 - Insert the value into the lab history table.
        SQL = "insert into LtHistory (valueId, RawValue, SampleTime, ReportTime) values (?, ?, ?, getdate())"
        historyId = system.db.runPrepUpdate(SQL, [valueId, rawValue, sampleTime], database, getKey=1)
        
        # Step 2 - Update LtValue with the id of the latest value
        SQL = "update LtValue set LastHistoryId = %i where valueId = %i" % (historyId, valueId)
        system.db.runUpdateQuery(SQL, database)
    except:
        log.warn("Warning: Insert into LtHistory failed for %s, %s at %s, probably due to a unique key violation" % (valueName, str(rawValue), str(sampleTime)))

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
def updateTags(tagProvider, unitName, valueName, rawValue, sampleTime, valid, tags, tagValues):
    print "Updating tags..."
    tagName="[%s]LabData/%s/%s" % (tagProvider, unitName, valueName)
    
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
    log.info("Initializing the last Value Cache...")
    
    SQL = "select * from LtLastValueView"
    pds = system.db.runQuery(SQL, database)
    for record in pds:
        valueName=record['ValueName']
        valueId=record['ValueId']
        rawValue=record['RawValue']
        sampleTime=record['SampleTime']
        reportTime=record['ReportTime']
        lastValueCache[valueName]={'valueId':valueId, 'rawValue': rawValue, 'sampleTime': sampleTime, 'reportTime': reportTime}
    log.trace("Loaded %i measurements into the last value cache..." % (len(pds)))
#    print lastValueCache




