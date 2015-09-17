'''
Created on Mar 27, 2015

@author: Pete
'''

import sys, system, string, traceback
from ils.labData.common import postMessage
from java.util import Calendar
log = system.util.getLogger("com.ils.labData.reader")
dcsLog = system.util.getLogger("com.ils.labData.reader.dcs")
phdLog = system.util.getLogger("com.ils.labData.reader.phd")
derivedLog = system.util.getLogger("com.ils.labData.derivedValues")
customValidationLog = system.util.getLogger("com.ils.labData.customValidation")
selectorLog = system.util.getLogger("com.ils.labData.selector")
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
    writeTags, writeTagValues = checkForNewDCSLabValues(database, tagProvider, limits, writeTags, writeTagValues)
    checkForDerivedValueTriggers(database)
    writeTags, writeTagValues = checkDerivedCalculations(database, tagProvider, writeTags, writeTagValues)
    
    log.debug("Writing %i new lab values to local lab data tags" % (len(writeTags)))

    log.trace("Writing %s :: %s" % (str(writeTags), str(writeTagValues)))
    tagWriter(writeTags, writeTagValues,mode="asynchAll")
    log.info("...finished lab data scanning!")

def tagWriter(tags, vals, mode="synch"):
    
    if mode == "asynchAll":
        system.tag.writeAll(tags, vals)
    elif mode == "asynch":
        i = 0;
        for tag in tags:
            val = vals[i]
            system.tag.write(tag, val)
            i = i + 1
    elif mode == "synchAll":
        system.tag.writeAllSynchronous(tags, vals)
    elif mode == "synch":
        i = 0
        for tag in tags:
            val = vals[i]
            system.tag.writeSynchronous(tag, val)
#            print "     writing %s to %s " % (str(val), tag)
            i=i+1
            
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
            derivedLog.trace("      ...%s was not in the trigger cache, adding it" % (valueName))
            
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
                 'triggerValueName': triggerValueName,
                 'triggerValueId': triggerValueId,
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
                     'triggerValueName': triggerValueName,
                     'triggerValueId': triggerValueId,
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
    labDataWriteEnabled=system.tag.read("[" + tagProvider + "]" + "Configuration/LabData/labDataWriteEnabled").value
    globalWriteEnabled=system.tag.read("[" + tagProvider + "]/Configuration/Common/writeEnabled").value
    writeEnabled = labDataWriteEnabled and globalWriteEnabled
    
    for d in derivedCalculationCache.values():
        valueName=d.get("valueName", "")
        triggerValueName=d.get("triggerValueName","")
        derivedLog.trace("   ...checking %s" % (valueName))
        valueId=d.get("valueId", -1)
        triggerValueId=d.get("triggerValueId", -1)
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
        dataDictionary[triggerValueName]={'valueName': triggerValueName, 
                                   'valueId': triggerValueId, 
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
                relatedDataIsConsistent = False
        
        if relatedDataIsConsistent:
            from ils.labData.callbackDispatcher import derivedValueCallback
            try:
                derivedLog.trace("      Calling %s and passing %s" % (callback, str(dataDictionary)))
                returnDictionary = derivedValueCallback(callback, dataDictionary)
                derivedLog.trace("         The value returned from the calculation method is: %s" % (str(returnDictionary)))
                
                status=returnDictionary.get("status", "Error")
                if string.upper(status) == "SUCCESS":
                    newVal=returnDictionary.get("value", None)
                    # Use the sample time of the triggerValue and store the value in the database and in the UDT tags
                    storeValue(valueId, valueName, newVal, sampleTime, derivedLog, database)
                
                    # This updates the Lab Data UDT tags - derived values do not get validated, so set valid = true; this makes the console argument irrelevant
                    valid = True
                    writeTags, writeTagValues = updateTags(tagProvider, unitName, valueName, newVal, sampleTime, valid, True, writeTags, writeTagValues, log)
                
                    # Derived lab data also has a target OPC tag that it needs to update - do this immediately
                    if writeEnabled:
                        system.opc.writeValue(resultServerName, resultItemId, newVal)
                        log.trace("         Writing derived value %f for %s to %s" % (newVal, valueName, resultItemId))
                    else:
                        log.info("         *** Skipping *** Write of derived value %f for %s to %s" % (newVal, valueName, resultItemId))
                else:
                    derivedLog.warning("         The derived value callback was unsuccessful")

                # Remove this derived variable from the open calculation cache
                del derivedCalculationCache[valueName]
                
            except:
                errorType,value,trace = sys.exc_info()
                errorTxt = traceback.format_exception(errorType, value, trace, 500)
                derivedLog.error("Caught an exception calling calculation method named %s... \n%s" % (callback, errorTxt) )
                return writeTags, writeTagValues
        else:
            derivedLog.trace("         The lab data is not consistent, check if we should give up...")
            from java.util import Date
            now = Date()
            
            # Determine the time window that we will keep trying (this just has an end time)
            cal.setTime(reportTime)
            cal.add(Calendar.MINUTE, newSampleWaitTime)
            newSampleWaitEnd = cal.getTime()
            
            if now > newSampleWaitEnd:
                derivedLog.trace("         The  related sample has still not arrived and probably never will, time to give up!")
                del derivedCalculationCache[valueName]

    derivedLog.trace(" ...done processing the derived values for this cycle... ")

    return writeTags, writeTagValues

#----------------------------------------------------------------------
def checkIfValueIsNew(valueName, rawValue, sampleTime, log):
    log.trace("Checking if lab value is new: %s - %s - %s..." % (str(valueName), str(rawValue), str(sampleTime)))
        
    if lastValueCache.has_key(valueName):
        lastValue=lastValueCache.get(valueName)
        log.trace("...there is a value in the cache")
        if lastValue.get('rawValue') != rawValue or lastValue.get('sampleTime') != sampleTime:
            log.trace("...found a new value because it does not match what is in the cache (%s - %s)..." % 
                      (str(lastValue.get('rawValue')), str(lastValue.get('sampleTime'))))
            new = True
        else:
            new = False
            log.trace("...this value is already in the cache so it will be ignored...")
    else:
        log.trace("...found a new value because %s does not exist in the cache..." % (valueName))
        new = True
    
    return new


#-------------
def checkForNewDCSLabValues(database, tagProvider, limits, writeTags, writeTagValues):
    dcsLog.trace("Checking for new DCS Lab values ... ")    
    
    SQL = "select V.ValueName, V.ValueId, V.ValidationProcedure, DV.ItemId, WL.ServerName, U.UnitName, P.Post "\
        "FROM LtValue V, TkUnit U, LtDCSValue DV, TkPost P, TkWriteLocation WL "\
        "WHERE V.ValueId = DV.ValueId "\
        " and V.UnitId = U.UnitId "\
        " and U.PostId = P.PostId " \
        " and DV.WriteLocationId = WL.WriteLocationId"
        
    pds = system.db.runQuery(SQL, database)

    for record in pds:
        unitName = record["UnitName"]
        valueName = record["ValueName"]
        valueId = record["ValueId"]
        serverName = record["ServerName"]
        itemId = record["ItemId"]
        post = record["Post"]
        validationProcedure = record["ValidationProcedure"]
        tagName = "LabData/%s/DCS-Lab-Values/%s" % (unitName, valueName)
        dcsLog.trace("Reading: %s " % (tagName))    
        qv = system.tag.read(tagName)

        dcsLog.trace("...read %s: %s - %s - %s - %s" % (valueName, itemId, str(qv.value), str(qv.timestamp), str(qv.quality)))
        
        if str(qv.quality) == 'Good':
            new = checkIfValueIsNew(valueName, qv.value, qv.timestamp, dcsLog)
            if new:
                writeTags, writeTagValues = handleNewLabValue(post, unitName, valueId, valueName, qv.value, qv.timestamp, \
                     database, tagProvider, limits, validationProcedure, writeTags, writeTagValues, dcsLog)
        else:
            # I don't want to post this to the queue because this is called every minute, and if the same tag is bad for a day 
            # we'll fill the queue with errors, yet log.error isn't seen by anyone...
            dcsLog.error("Skipping %s because its quality is %s" % (valueName, qv.quality))

    return writeTags, writeTagValues

    
def checkForNewPHDLabValues(database, tagProvider, limits, writeTags, writeTagValues):
    
    #----------------------------------------------------------------
    def checkForANewPHDLabValue(valueName, itemId, valueList, endDate):
        phdLog.trace("Checking for a new lab value for: %s - %s..." % (str(valueName), str(itemId)))
        
        if str(valueList.serviceResult) != 'Good':
            phdLog.error("   -- The returned value for %s was %s --" % (itemId, valueList.serviceResult))
            return False, -1, -1, valueList.serviceResult
        
        if valueList.size()==0:
            phdLog.trace("   -- no data found for %s --" % (itemId))
            return False, -1, -1, "NoDataFound"
        
        # There is something strange about SOME of the lab data at EM - for some of the lab data, the results include a 
        # point in the future, so it will be the last point in the list, and it has a value of None.  I'm not sure how a historian
        # can have a point in the future - sounds more like fiction than history - plus that time is greater than the
        # end time I specified.  Filter it out nonetheless.
    #    lastQV=valueList[valueList.size()-1]
        validatedList = []
        for qv in valueList:
            if qv.timestamp < endDate:
                validatedList.append(qv)
            else:
                phdLog.warning("Found a lab sample in the future for %s-%s" % (str(valueName), str(itemId)))

        if len(validatedList) == 0:
            return False, None, None, "NoDataFound"

        qv=validatedList[len(validatedList) - 1]
        rawValue=qv.value
        sampleTime=qv.timestamp
        quality=qv.quality
        
        phdLog.trace("...checking value %s at %s (%s)..." % (str(rawValue), str(sampleTime), quality))
        new = checkIfValueIsNew(valueName, rawValue, sampleTime, phdLog)
        return new, rawValue, sampleTime, ""
    #----------------------------------------------------------------
    
    phdLog.trace("Checking for new PHD Lab values ... ")
    
    endDate = util.getDate()
    from java.util import Calendar
    cal = Calendar.getInstance()
 
    cal.setTime(endDate)
    cal.add(Calendar.HOUR, -24)
    startDate = cal.getTime()
    
    # Fetch the set of lab values that we need to get from PHD
    SQL = "Select distinct InterfaceName from LtPHDValueView"
    interfacePDS = system.db.runQuery(SQL, database)
    for interfaceRecord in interfacePDS:
        hdaInterface = interfaceRecord["InterfaceName"]
        serverIsAvailable=system.opchda.isServerAvailable(hdaInterface)
        if not(serverIsAvailable):
            phdLog.error("HDA interface %s is not available!" % (hdaInterface))
        else:
            phdLog.trace("...reading lab data values from HDA server: %s..." % (hdaInterface))

            # Now select the itemIds that use that interface
            SQL = "select Post, UnitName, ValueId, ValueName, ItemId, ValidationProcedure "\
                " from LtPHDValueView where InterfaceName = '%s'" % (hdaInterface)
            tagInfoPds = system.db.runQuery(SQL, database) 
            itemIds=[]
            for record in tagInfoPds:
                itemIds.append(record["ItemId"])

            maxValues=0
            boundingValues=0
            retVals=system.opchda.readRaw(hdaInterface, itemIds, startDate, endDate, maxValues, boundingValues)
            phdLog.trace("...back from HDA read, read %i values!" % (len(retVals)))
#        log.trace("retVals: %s" % (str(retVals)))
        
            if len(tagInfoPds) != len(retVals):
                phdLog.error("The number of elements in the tag info dataset does not match the number of values returned!")
                return writeTags, writeTagValues
    
            for i in range(len(tagInfoPds)):
                tagInfo=tagInfoPds[i]
                valueList=retVals[i]

                post=tagInfo["Post"]
                unitName=tagInfo["UnitName"]
                valueId=tagInfo["ValueId"]
                valueName=tagInfo["ValueName"]
                itemId=tagInfo["ItemId"]
                validationProcedure=tagInfo["ValidationProcedure"]

                new, rawValue, sampleTime, status = checkForANewPHDLabValue(valueName, itemId, valueList, endDate)
                if new:
                    writeTags, writeTagValues = handleNewLabValue(post, unitName, valueId, valueName, rawValue, sampleTime, \
                        database, tagProvider, limits, validationProcedure, writeTags, writeTagValues, phdLog)
                elif status != "":
                    writeTags, writeTagValues = handleBadLabValue(unitName, valueName, tagProvider, status, writeTags, writeTagValues)
        
    phdLog.trace("Writing %s to %s" % (str(writeTagValues), str(writeTags)))

    phdLog.trace("Done reading PHD lab values")
    return writeTags, writeTagValues
    
    
# Handle a new value.  The first thing to do is to check the limits.  If there are validity limits and the value is outside the 
# limits then operator intervention is required before storing the value.  If there are no limits or the value is within the validity limits
# then store the value automatically
def handleNewLabValue(post, unitName, valueId, valueName, rawValue, sampleTime, database, tagProvider, limits, 
                      validationProcedure, writeTags, writeTagValues, log):
    
    limit=limits.get(valueId,None)
    log.trace("...handling a new lab value for %s, checking limits (%s)..." % (valueName, str(limit)))
    
    # Always write the raw value and the raw sample time immediately
    writeTags, writeTagValues = updateRawTags(tagProvider, unitName, valueName, rawValue, sampleTime, writeTags, writeTagValues, log)

    if validationProcedure != None and validationProcedure != "":
        
        from ils.labData.callbackDispatcher import customValidate
        isValid = customValidate(valueName, rawValue, validationProcedure)
        # If it fails custom validation then don't bother with any further checks!
        if not(isValid):
            log.trace("%s failed custom validation procedure <%s> " % (valueName, validationProcedure))

            from ils.labData.limitWarning import notifyCustomValidationViolation
            foundConsole=notifyCustomValidationViolation(post, unitName, valueName, valueId, rawValue, sampleTime, tagProvider, database)
        
            writeTags, writeTagValues = updateTags(tagProvider, unitName, valueName, rawValue, sampleTime, False, foundConsole, writeTags, writeTagValues, log)
            updateCache(valueId, valueName, rawValue, sampleTime)
            return writeTags, writeTagValues
        
    validValidity = True
    validRelease = True
    if limit != None:
        log.trace("Evaluating limits for this value: %s" % (str(limit)))
        from ils.labData.limits import checkValidityLimit
        validValidity,upperLimit,lowerLimit=checkValidityLimit(post, valueId, valueName, rawValue, sampleTime, database, tagProvider, limit)
            
        from ils.labData.limits import checkSQCLimit
        validSQC=checkSQCLimit(post, valueId, valueName, rawValue, sampleTime, database, tagProvider, limit)
            
        from ils.labData.limits import checkReleaseLimit
        validRelease,upperLimit,lowerLimit=checkReleaseLimit(valueId, valueName, rawValue, sampleTime, database, tagProvider, limit)
        
    # If the value is valid then store it to the database and write the value and sample time to the tag (UDT)
    if not(validValidity):
        log.trace("%s *failed* validity checks" % (valueName) )
        
        from ils.labData.limitWarning import notifyValidityLimitViolation
        foundConsole=notifyValidityLimitViolation(post, unitName, valueName, valueId, rawValue, sampleTime, tagProvider, database, upperLimit, lowerLimit)
        # Mark the tags as failed for now, If the notification found a console, then it will be a minute or two before the operator 
        # will determine whether or not to accept the value. (If we don't find a console then the same tags may be in this list with 
        # different values - not sure if that causes a problem)
        writeTags, writeTagValues = updateTags(tagProvider, unitName, valueName, rawValue, sampleTime, False, foundConsole, writeTags, writeTagValues, log)    
    elif not(validRelease):
        log.trace("%s *failed* release limit checks" % (valueName) )
        
        from ils.labData.limitWarning import notifyReleaseLimitViolation
        foundConsole=notifyReleaseLimitViolation(post, unitName, valueName, valueId, rawValue, sampleTime, tagProvider, database, upperLimit, lowerLimit)
        # Mark the tags as failed for now, If the notification found a console, then it will be a minute or two before the operator 
        # will determine whether or not to accept the value. (If we don't find a console then the same tags may be in this list with 
        # different values - not sure if that causes a problem)
        writeTags, writeTagValues = updateTags(tagProvider, unitName, valueName, rawValue, sampleTime, False, foundConsole, writeTags, writeTagValues, log)    
      
    else:
        log.trace("%s passed all limit checks" % (valueName))
        storeValue(valueId, valueName, rawValue, sampleTime, log, database)
        writeTags, writeTagValues = updateTags(tagProvider, unitName, valueName, rawValue, sampleTime, True, True, writeTags, writeTagValues, log)
            
    # regardless of whether we passed or failed validation, add the value to the cache so we don't process it again
    updateCache(valueId, valueName, rawValue, sampleTime)
    
    return writeTags, writeTagValues

# Handle a bad value.  Write the status to the status tag of the UDT
def handleBadLabValue(unitName, valueName, tagProvider, status, writeTags, writeTagValues):
    tagName="[%s]LabData/%s/%s" % (tagProvider, unitName, valueName)
    
    writeTags.append(str(tagName + "/status"))
    writeTagValues.append(status)
        
    return writeTags, writeTagValues


# Store a new lab value.  Insert the value into LtHistory and update LtValue with the id of the latest history value.
# This is called by one of two callers - directly by the scanner if the value is good or if the value is outside the limits and 
# the operator presses accept 
def storeValue(valueId, valueName, rawValue, sampleTime, log, database):
    log.trace("Storing %s - %s - %s - %s ..." % (valueName, str(valueId), str(rawValue), str(sampleTime)))
    try:
        # Step 1 - Insert the value into the lab history table.
        SQL = "insert into LtHistory (valueId, RawValue, SampleTime, ReportTime) values (?, ?, ?, getdate())"
        historyId = system.db.runPrepUpdate(SQL, [valueId, rawValue, sampleTime], database, getKey=1)
        
        # Step 2 - Update LtValue with the id of the latest history value
        SQL = "update LtValue set LastHistoryId = %i where valueId = %i" % (historyId, valueId)
        system.db.runUpdateQuery(SQL, database)
    except:
        log.warn("Warning: Insert into LtHistory failed for %s, %s at %s, probably due to a unique key violation" % (valueName, str(rawValue), str(sampleTime)))

# This is called by a selector tag change script.  There is a listener on the SampleTime and on the value.  They both call this handler.
# When a measurement is received from the lab system the sampleTime tag and the value tag are updated almost atomically.  That action
# will fire off two calls to this procedure, this procedure doesn't know or care who called it.  It will read both tags to get the 
# current value.  Two identical insert statements will be attempted but the database will reject the second because of the unique index.
def storeSelector(tagRoot, database):
    selectorLog.trace("Storing selector of tag %s" % (tagRoot))

    valueName=tagRoot[tagRoot.find('LabData/') + 8:]
    valueName=valueName[valueName.find('/') + 1:]

    selectorLog.trace("   ...the selector value name is <%s>" % (valueName))

    # Read the value and the sample time
    vals = system.tag.readAll([tagRoot + '/value', tagRoot + '/sampleTime'])
    value=vals[0].value
    sampleTime=vals[1].value
    selectorLog.trace("   ...handling %s at %s" % (str(value), str(sampleTime)))
    
    # Fetch the value id using the name
    SQL = "select ValueId from LtValue where ValueName = '%s'" % (valueName)
    valueId=system.db.runScalarQuery(SQL)
    if valueId == None:
        selectorLog.error("Error storing lab value for selector <%s> due to unable to find name in LtValue" % (valueName))
        return
     
    storeValue(valueId, valueName, value, sampleTime, selectorLog, database)

    
def updateCache(valueId, valueName, rawValue, sampleTime):
    lastValueCache[valueName]={'valueId': valueId, 'rawValue': rawValue, 'sampleTime': sampleTime}


# Update the Lab Data UDT tags
# FoundConsole is only relevant if the tag failed validation
def updateRawTags(tagProvider, unitName, valueName, rawValue, sampleTime, tags, tagValues, log):
    tagName="[%s]LabData/%s/%s" % (tagProvider, unitName, valueName)
    log.trace("Updating *raw* lab data tags %s..." % (tagName))
    
    tags.append(tagName + "/rawValue")
    tagValues.append(rawValue)
    tags.append(tagName + "/rawSampleTime")
    tagValues.append(sampleTime)

    return tags, tagValues
    
# Update the Lab Data UDT tags
# FoundConsole is only relevant if the tag failed validation
def updateTags(tagProvider, unitName, valueName, rawValue, sampleTime, valid, foundConsole, tags, tagValues, log):
    tagName="[%s]LabData/%s/%s" % (tagProvider, unitName, valueName)
    log.trace("Updating lab data tags %s..." % (tagName))
       
    if valid:
        tags.append(tagName + "/sampleTime")
        tagValues.append(sampleTime)
        tags.append(tagName + "/value")
        tagValues.append(rawValue)
        tags.append(tagName + "/badValue")
        tagValues.append(False)
        tags.append(tagName + "/status")
        tagValues.append("Good")
        
    else:
        if foundConsole:
            log.trace("Value is bad and there is a console - Setting the bad value flag to TRUE")
            tags.append(tagName + "/badValue")
            tagValues.append(True)
            tags.append(tagName + "/status")
            tagValues.append("bad - waiting for operator review")
        else:
            # Don't write to any tags here - the notify function will immediately call the accept logic if there is not a console
            # and that logic writes to the tags
            pass
        
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




