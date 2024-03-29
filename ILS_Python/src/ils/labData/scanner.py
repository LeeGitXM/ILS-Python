'''
Created on Mar 27, 2015

@author: Pete

The purpose of this module is to scan / poll of of the lab data points for new values.

This runs every 30 seconds from a gateway timer script.
The scanner utilizes a cache of processed values that are maintained from run to run, this
saves the work of a fair amount of database queries and slicing and dicing every 30 seconds even when nothing changed.
The cache used to just be a module level global.  This worked great except that it got initialized every time Python was 
reloaded, which happens every time ANY file is changed in the PYLIB structure.  The logic still worked fine except that this 
would trigger it to reprocess the most recent value.  Generally this happens behind the scenes and doesn't matter, but if the 
most recent value was bad and violated some lab limits then it will generate an OC alert every time your Python is saved.
So, to work around this I changed using a module level global to using IA's global scheme.  At the beginning of each scan I 
get the globals and at the end I stash them.    
'''

import sys, system, string, traceback
from ils.common.config import getTagProvider, getIsolationTagProvider, getDatabase, getIsolationDatabase
from ils.labData.common import postMessage
from java.util import Calendar
from ils.common.database import toDateString
from ils.common.cast import toDateTime

from ils.log import getLogger
log =getLogger(__name__)
dcsLog =getLogger(__name__ + ".dcs")
phdLog =getLogger(__name__ + ".phd")
derivedLog =getLogger(__name__ + ".derivedValues")
customValidationLog =getLogger(__name__ + ".customValidation")
selectorLog =getLogger(__name__ + ".selector")
import ils.common.util as util

LAST_VALUE_CACHE = "lastValueCache"
TRIGGER_CACHE = "triggerCache"
DERIVED_CALCULATION_CACHE = "derivedCalculationCache"

'''
This is called from a gateway timer script
'''
def scanner():
    iaGlobals = system.util.getGlobals()
    lastValueCache = iaGlobals.get(LAST_VALUE_CACHE, {})
    triggerCache= iaGlobals.get(TRIGGER_CACHE, {})
    derivedCalculationCache = iaGlobals.get(DERIVED_CALCULATION_CACHE, {})
    
    database = getDatabase()
    isolationDatabase = getIsolationDatabase()
    tagProvider = getTagProvider()
    tagProviderIsolation = getIsolationTagProvider()
    
    if system.tag.read("[%s]Configuration/LabData/pollingEnabled" % (tagProvider)).value == True:
        lastValueCache, triggerCache, derivedCalculationCache = main(database, tagProvider, lastValueCache, triggerCache, derivedCalculationCache)
    else:
        log.tracef("Lab data polling is disabled") 

    if system.tag.read("[%s]Configuration/LabData/pollingEnabledIsolation" % (tagProvider)).value == True:
        lastValueCache, triggerCache, derivedCalculationCache = main(isolationDatabase, tagProviderIsolation, lastValueCache, triggerCache, derivedCalculationCache)
        
    ''' Tickle the watchdogs '''
    tagPath = "[%s]Site/Watchdogs/Lab Data Watchdog/currentValue" % (tagProvider)
    if system.tag.exists(tagPath):
        currentValue = system.tag.read(tagPath).value
        
        if currentValue > 100:
            currentValue = 0
        else:
            currentValue = currentValue + 1
            
        system.tag.write(tagPath, currentValue)

    system.util.getGlobals()[LAST_VALUE_CACHE]= lastValueCache
    system.util.getGlobals()[TRIGGER_CACHE] = triggerCache
    system.util.getGlobals()[DERIVED_CALCULATION_CACHE] = derivedCalculationCache

def main(database, tagProvider, lastValueCache, triggerCache, derivedCalculationCache):
    log.tracef("Scanning for lab data (%s, %s)...", database, tagProvider)

    log.trace("Last Value Cache: %s" % (str(lastValueCache)))
    if len(lastValueCache) == 0:
        lastValueCache = initializeCache(database, lastValueCache)
    
    from ils.labData.limits import fetchLimits
    limits=fetchLimits(tagProvider, database)
    
    if system.tag.exists("[%s]Configuration/Common/simulateHDA" % (tagProvider)):
        simulateHDA = system.tag.read("[%s]Configuration/Common/simulateHDA" % (tagProvider)).value
    else:
        simulateHDA = False

    writeMode = "synch"
    newValue = False
    writeTags=[]
    writeTagValues=[]
    lastValueCache, writeTags, writeTagValues = checkForNewPHDLabValues(lastValueCache, database, tagProvider, limits, writeTags, writeTagValues, simulateHDA)
    log.debug("Writing %i new PHD lab values to local lab data tags" % (len(writeTags)))
    tagWriter(writeTags, writeTagValues, mode=writeMode)
    if len(writeTags) > 0:
        newValue = True
    
    writeTags=[]
    writeTagValues=[] 
    lastValueCache, writeTags, writeTagValues = checkForNewDCSLabValues(lastValueCache, database, tagProvider, limits, writeTags, writeTagValues)
    log.debug("Writing %i new DCS lab values to local lab data tags" % (len(writeTags)))
    tagWriter(writeTags, writeTagValues, mode=writeMode)
    if len(writeTags) > 0:
        newValue = True
    
    writeTags=[]
    writeTagValues=[] 
    triggerCache, derivedCalculationCache = checkForDerivedValueTriggers(database, triggerCache, derivedCalculationCache)
    derivedCalculationCache, writeTags, writeTagValues = checkDerivedCalculations(derivedCalculationCache, database, tagProvider, writeTags, writeTagValues, simulateHDA)
    log.debug("Writing %i new derived lab values to local lab data tags" % (len(writeTags)))
    tagWriter(writeTags, writeTagValues, mode=writeMode)
    if len(writeTags) > 0:
        newValue = True
        
    if newValue:
        notifyClients()

    log.tracef("...finished lab data scanning!")
    return lastValueCache, triggerCache, derivedCalculationCache


def notifyClients():
    log.tracef("Notifying clients of new lab data!")
    project = system.util.getProjectName()
    system.util.sendMessage(project, messageHandler="newLabData", payload={}, scope="C")


def tagWriter(tags, vals, mode="synch"):
    
    if mode == "asynchAll":
        try:
            system.tag.writeAll(tags, vals)
        except:
            log.errorf("Error: Lab Data Scanner, (%s.tagWriter): writing %s to %s, mode: %s", __name__, str(vals), str(tags), mode)
    elif mode == "asynch":
        i = 0;
        for tag in tags:
            val = vals[i]
            try:
                system.tag.write(tag, val)
            except:
                log.errorf("Error: Lab Data Scanner, (%s.tagWriter): writing %s to %s, mode: %s", __name__, str(val), str(tag), mode)
            i = i + 1
    elif mode == "synchAll":
        try:
            system.tag.writeAllSynchronous(tags, vals)
        except:
            log.errorf("Error: Lab Data Scanner, (%s.tagWriter): writing %s to %s, mode: %s", __name__, str(vals), str(tags), mode)
    elif mode == "synch":
        i = 0
        for tag in tags:
            val = vals[i]
            try:
                system.tag.writeSynchronous(tag, val)
            except:
                log.errorf("Error: Lab Data Scanner, (%s.tagWriter): writing %s to %s, mode: %s", __name__, str(val), str(tag), mode)
            i=i+1
            
#-------------
# 
def checkForDerivedValueTriggers(database, triggerCache, derivedCalculationCache):
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
        callback=record["Callback"]
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
                resultServerName=record['InterfaceName']
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
    
    return triggerCache, derivedCalculationCache


# The logic that drives the derived calculations is a little different here than in the old system.  In the old system each 
# calculation procedure had the responsibility to collect consistent lab data.  In the new framework, the engine will collect
# all of the necessary information and then call the calculation method.
def checkDerivedCalculations(derivedCalculationCache, database, tagProvider, writeTags, writeTagValues, simulateHDA):
    derivedLog.tracef("Checking the derived calculations...")
    
    def writeToPHD(resultServerName, resultItemId, newVal, sampleTime, simulateHDA):
        try:
            if simulateHDA:
                log.tracef("simulating HDA: skipping write of %s - %s ", resultItemId, str(newVal))
            else:
                system.opchda.insert(resultServerName, resultItemId, newVal, sampleTime, 192)
                log.infof("         Writing derived value to PHD via HDA: %f for %s to %s at %s", newVal, valueName, resultItemId, str(sampleTime))
        except:
            log.errorf("**** Error writing derived value to PHD via HDA: %f for %s to %s at %s ****", newVal, valueName, resultItemId, str(sampleTime))
    
    cal = Calendar.getInstance()
    labDataWriteEnabled=system.tag.read("[" + tagProvider + "]" + "Configuration/LabData/labDataWriteEnabled").value
    globalWriteEnabled=system.tag.read("[" + tagProvider + "]/Configuration/Common/writeEnabled").value
    productionProviderName = getTagProvider()   # Get the Production tag provider
    writeEnabled = tagProvider != productionProviderName or (labDataWriteEnabled and globalWriteEnabled)
    
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
                                   'sampleTime': sampleTime,
                                   'reportTime': reportTime,
                                   'trigger': True}
                            
        relatedDataList=d.get("relatedData", [])
        order = 0
        for relatedData in relatedDataList:
            relatedValueName=relatedData.get("relatedValueName","")
            relatedValueId=relatedData.get("relatedValueId",-1)
            
            SQL = "select RawValue, SampleTime, ReportTime from LtHistory H, LtValue V "\
                " where V.ValueId = %s and V.LastHistoryId = H.HistoryId" % (str(relatedValueId))
            pds=system.db.runQuery(SQL, database)
            if len(pds) == 1:
                record=pds[0]
                rv=record["RawValue"]
                st=record["SampleTime"]
                rt=record["ReportTime"]
                derivedLog.trace("      found %f at %s for related data named: %s" % (rv, str(st), relatedValueName))
                
                if st >= sampleTimeWindowStart and st <= sampleTimeWindowEnd:
                    derivedLog.trace("      --- The related data's sample time is within the sample time window! ---")
                    
                    dataDictionary[relatedValueName]={'valueName': relatedValueName, 
                                            'valueId':relatedValueId, 
                                            'rawValue': rv,
                                            'sampleTime': st,
                                            'reportTime': rt,
                                            "order": order,
                                            'trigger': False}
                    
                    order = order + 1
                else:
                    derivedLog.tracef("      --- The related data's sample time is NOT within the sample time window(%s -> %s)! ---", str(sampleTimeWindowStart), str(sampleTimeWindowEnd))
                    relatedDataIsConsistent = False
            else:
                derivedLog.error("Unable to find any value for the related data named %s for trigger value %s" % (relatedValueName, valueName))
                relatedDataIsConsistent = False
        
        if relatedDataIsConsistent:
            from ils.labData.callbackDispatcher import derivedValueCallback
            
            derivedLog.trace("      Calling %s and passing %s" % (callback, str(dataDictionary)))
            
            try:
                returnDictionary = derivedValueCallback(callback, dataDictionary)
                derivedLog.trace("         The value returned from the calculation method is: %s" % (str(returnDictionary)))
                status=returnDictionary.get("status", "Error")
            except:
                errorType,value,trace = sys.exc_info()
                errorTxt = traceback.format_exception(errorType, value, trace, 500)
                derivedLog.error("Caught an exception calling calculation method named %s... \n%s" % (callback, errorTxt) )
                status = "Error"

            if string.upper(status) == "SUCCESS":
                newVal=returnDictionary.get("value", None)
                # Use the sample time of the triggerValue and store the value in the database and in the UDT tags
                storeValue(valueId, valueName, newVal, str(sampleTime), unitName, derivedLog, tagProvider, database)
            
                # This updates the Lab Data UDT tags - derived values do not get validated, so set valid = true; this makes the console argument irrelevant
                valid = True
                writeTags, writeTagValues = updateTags(tagProvider, unitName, valueName, newVal, sampleTime, valid, True, writeTags, writeTagValues, log)
            
                # Derived lab data also has a target OPC tag that it needs to update - do this immediately
                if writeEnabled:
                    writeToPHD(resultServerName, resultItemId, newVal, sampleTime, simulateHDA)
                else:
                    log.info("         *** Skipping *** Write of derived value %f for %s to %s" % (newVal, valueName, resultItemId))
            else:
                derivedLog.warn("         The derived value callback was unsuccessful")

            # Remove this derived variable from the open calculation cache
            del derivedCalculationCache[valueName]
    
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

    derivedLog.tracef(" ...done processing the derived values for this cycle!")

    return derivedCalculationCache, writeTags, writeTagValues


#-------------
def checkForNewDCSLabValues(lastValueCache, database, tagProvider, limits, writeTags, writeTagValues):
    
    #----------------------------------------------------------------------
    def checkIfValueIsNew(valueName, rawValue, sampleTime, minimumSampleIntervalSeconds, log):
        log.trace("...checking if it is new: %s - %s - %s..." % (str(valueName), str(rawValue), str(sampleTime)))
            
        if lastValueCache.has_key(valueName):
            lastValue=lastValueCache.get(valueName)
            log.tracef("...there is a value in the cache: <%s>", str(lastValue))
            
            if lastValue.get('rawValue') == None or lastValue.get('sampleTime') == None:
                log.trace("...found a new value because the last value is None...")
                new = True
            else:
                if lastValue.get('rawValue') != rawValue:
                    log.tracef("The VALUE is different: %s & %s", str(lastValue.get('rawValue')), str(rawValue))
                
                if system.date.secondsBetween(lastValue.get('sampleTime'), sampleTime) != 0:
                    log.tracef("The sample time is different %s & %s", str(lastValue.get('sampleTime')), str(sampleTime))
                
                if lastValue.get('rawValue') != rawValue or system.date.secondsBetween(lastValue.get('sampleTime'), sampleTime) != 0:
                    # Calculate the time between this sample and the last sample
                    lastSampleTime = lastValue.get("sampleTime")
                    secondsBetween = system.date.secondsBetween(lastSampleTime, sampleTime)
                    if secondsBetween > minimumSampleIntervalSeconds:
                        log.trace("...found a new value because it does not match what is in the cache and has met the minimum time between samples (%s - %s)..." % 
                              (str(lastValue.get('rawValue')), str(lastValue.get('sampleTime'))))
                        new = True
                    else:
                        log.trace("...found a new value (%s - %s) that has NOT met the minimum time between samples, the last sample was recived %s seconds ago ..." % 
                              (str(lastValue.get('rawValue')), str(lastValue.get('sampleTime')), str(secondsBetween)))
                        new = False
                else:
                    new = False
                    log.trace("...this value is already in the cache so it will be ignored...")
        else:
            log.trace("...found a new value because %s does not exist in the cache..." % (valueName))
            new = True
        
        return new
        
    dcsLog.tracef("Checking for new DCS Lab values ... ")    
    
    SQL = "select V.ValueName, V.ValueId, V.ValidationProcedure, DV.ItemId, OPC.InterfaceName, U.UnitName, P.Post, DV.MinimumSampleIntervalSeconds, "\
        "DV.SampleTimeConstantMinutes "\
        "FROM LtValue V, TkUnit U, LtDCSValue DV, TkPost P, LtOpcInterface OPC "\
        "WHERE V.ValueId = DV.ValueId "\
        " and V.UnitId = U.UnitId "\
        " and U.PostId = P.PostId " \
        " and DV.InterfaceId = OPC.InterfaceId"
        
    pds = system.db.runQuery(SQL, database)

    for record in pds:
        unitName = record["UnitName"]
        valueName = record["ValueName"]
        valueId = record["ValueId"]
        interfaceName = record["InterfaceName"]
        itemId = record["ItemId"]
        post = record["Post"]
        validationProcedure = record["ValidationProcedure"]
        minimumSampleIntervalSeconds  = record["MinimumSampleIntervalSeconds"]
        sampleTimeConstantMinutes = record["SampleTimeConstantMinutes"]
        
        tagName = "LabData/%s/DCS-Lab-Values/%s" % (unitName, valueName)
        dcsLog.trace("Reading: %s " % (tagName))    
        qv = system.tag.read(tagName)

        dcsLog.trace("...read %s: %s - %s - %s - %s" % (valueName, itemId, str(qv.value), str(qv.timestamp), str(qv.quality)))
        
        if str(qv.quality) == 'Good':
            sampleTime = system.date.addMinutes(qv.timestamp, int(-1 * abs(sampleTimeConstantMinutes)))
            new = checkIfValueIsNew(valueName, qv.value, sampleTime, minimumSampleIntervalSeconds, dcsLog)
            if new:
                lastValueCache, writeTags, writeTagValues = handleNewLabValue(lastValueCache, post, unitName, valueId, valueName, qv.value, sampleTime, \
                     database, tagProvider, limits, validationProcedure, writeTags, writeTagValues, dcsLog)
        else:
            # I don't want to post this to the queue because this is called every minute, and if the same tag is bad for a day 
            # we'll fill the queue with errors, yet log.error isn't seen by anyone...
            dcsLog.warn("...skipping %s because its quality is %s" % (valueName, qv.quality))

    dcsLog.tracef("...done checking for new DCS Lab values!")
    
    return lastValueCache, writeTags, writeTagValues

    
def checkForNewPHDLabValues(lastValueCache, database, tagProvider, limits, writeTags, writeTagValues, simulateHDA):
    
    #----------------------------------------------------------------------
    def checkIfValueIsNew(valueName, rawValue, sampleTime, log):
        log.trace("...checking if it is new: %s - %s - %s..." % (str(valueName), str(rawValue), str(sampleTime)))
            
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

    #----------------------------------------------------------------
    def checkForANewPHDLabValue(valueName, itemId, valueList, endDate, simulateHDA):
        
        phdLog.trace("Checking for a new lab value for: %s - %s..." % (str(valueName), str(itemId)))
        
        if simulateHDA:
            phdLog.trace("--- Using PHD Simulator ---")
            if len(valueList) == 0:
                phdLog.trace("   -- no data found for %s --" % (itemId))
                return False, -1, -1, "NoDataFound"
            
            phdLog.tracef("Found simulated data for %s", itemId)
            validatedList = []
            for qv in valueList:
                phdLog.tracef("Checking qv: %s", str(qv))
                if toDateTime(qv["timestamp"], dateDelimiter="-") < endDate:
                    validatedList.append(qv)
                else:
                    phdLog.warn("Found a lab sample in the future for %s-%s" % (str(valueName), str(itemId)))
    
            if len(validatedList) == 0:
                return False, None, None, "NoDataFound"
    
            qv=validatedList[len(validatedList) - 1]
            rawValue=qv["value"]
            sampleTime=qv["timestamp"]
            quality=qv["quality"]
            
            phdLog.trace("...checking value %s at %s (%s)..." % (str(rawValue), str(sampleTime), quality))
            new = checkIfValueIsNew(valueName, rawValue, sampleTime, phdLog)
            
        else:
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
            phdLog.tracef("Found data for %s", itemId)
            validatedList = []
            for qv in valueList:
                phdLog.tracef("Checking qv: %s", str(qv))
                if qv.timestamp < endDate:
                    validatedList.append(qv)
                else:
                    phdLog.warn("Found a lab sample in the future for %s-%s" % (str(valueName), str(itemId)))
    
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
    
    phdLog.tracef("Checking for new PHD Lab values ... ")
    
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
        
        if simulateHDA:
            serverIsAvailable = True
        else:
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

#            print "HDA Lab data items: ", itemIds
            maxValues=0
            boundingValues=0
            if simulateHDA:
                retVals = simulateReadRaw(itemIds, startDate, endDate)
            else:
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

                new, rawValue, sampleTime, status = checkForANewPHDLabValue(valueName, itemId, valueList, endDate, simulateHDA)
                if new:
                    lastValueCache, writeTags, writeTagValues = handleNewLabValue(lastValueCache, post, unitName, valueId, valueName, rawValue, sampleTime, \
                        database, tagProvider, limits, validationProcedure, writeTags, writeTagValues, phdLog)
                elif status != "":
                    writeTags, writeTagValues = handleBadLabValue(unitName, valueName, tagProvider, status, writeTags, writeTagValues)
        
    phdLog.trace("Writing %s to %s" % (str(writeTagValues), str(writeTags)))

    phdLog.tracef("Done reading PHD lab values")
    return lastValueCache, writeTags, writeTagValues
    
    
'''
Handle a new value generically, regardless of its source..  The first thing to do is to check the limits.  If there are validity limits and the value is outside the 
# limits then operator intervention is required before storing the value.  If there are no limits or the value is within the validity limits
# then store the value automatically
'''
def handleNewLabValue(lastValueCache, post, unitName, valueId, valueName, rawValue, sampleTime, database, tagProvider, limits, 
                      validationProcedure, writeTags, writeTagValues, log):
    
    
    limit=limits.get(valueId,None)
    log.trace("...handling a new lab value for %s, checking limits (%s)..." % (valueName, str(limit)))
    
    # Always write the raw value and the raw sample time immediately
    writeTags, writeTagValues = updateRawTags(tagProvider, unitName, valueName, rawValue, sampleTime, writeTags, writeTagValues, log)

    if validationProcedure != None and validationProcedure != "":
        
        from ils.labData.callbackDispatcher import customValidate
        isValid, notifyConsole, statusMessage = customValidate(validationProcedure, valueId, valueName, rawValue, sampleTime, unitName, tagProvider, database)

        # If it fails custom validation then don't bother with any further checks!
        if not(isValid):
            log.trace("%s failed custom validation procedure <%s> " % (valueName, validationProcedure))

            if notifyConsole:
                from ils.labData.limitWarning import notifyCustomValidationViolation
                foundConsole=notifyCustomValidationViolation(post, unitName, valueName, valueId, rawValue, sampleTime, tagProvider, database)
                # If the value is bad and we re supposed to notify the console but there isn't one, then store the value even if it is bad.
                storeValue(valueId, valueName, rawValue, sampleTime, unitName, log, tagProvider, database)
            else:
                foundConsole = False

            # Remember that updateTags does not always promote the value...
            writeTags, writeTagValues = updateTags(tagProvider, unitName, valueName, rawValue, sampleTime, isValid, foundConsole, writeTags, writeTagValues, log, notifyConsole, statusMessage)
            lastValueCache = updateCache(lastValueCache, valueId, valueName, rawValue, sampleTime)
            return lastValueCache, writeTags, writeTagValues
        
    validValidity = True
    validSQCValidity = True
    validRelease = True
    if limit != None:
        log.trace("Evaluating limits for this value: %s" % (str(limit)))
        
        ''' Validity limits are a little funny; there can be a pure validity limit and there can be a validity limit that is part of an SQC limit.  '''
        from ils.labData.limits import checkValidityLimit
        validValidity, upperValidityLimit, lowerValidityLimit=checkValidityLimit(post, valueId, valueName, rawValue, sampleTime, database, tagProvider, limit)
            
        from ils.labData.limits import checkSQCLimit
        validSQCValidity, upperValidityLimit, lowerValidityLimit =checkSQCLimit(post, valueId, valueName, rawValue, sampleTime, database, tagProvider, limit)
            
        from ils.labData.limits import checkReleaseLimit
        validRelease, upperReleaseLimit, lowerReleaseLimit=checkReleaseLimit(valueId, valueName, rawValue, sampleTime, database, tagProvider, limit)
    
    log.tracef("validValidity: %s", str(validValidity))
    log.tracef("validSQCValidity: %s", str(validSQCValidity))
    log.tracef("validRelease: %s", str(validRelease))
    
    # If the value is valid then store it to the database and write the value and sample time to the tag (UDT)
    if not(validRelease):
        log.tracef("%s *failed* release limit checks", valueName)
        
        from ils.labData.limitWarning import notifyReleaseLimitViolation
        foundConsole=notifyReleaseLimitViolation(post, unitName, valueName, valueId, rawValue, sampleTime, tagProvider, database, upperReleaseLimit, lowerReleaseLimit)
        # Mark the tags as failed for now, If the notification found a console, then it will be a minute or two before the operator 
        # will determine whether or not to accept the value. (If we don't find a console then the same tags may be in this list with 
        # different values - not sure if that causes a problem)
        writeTags, writeTagValues = updateTags(tagProvider, unitName, valueName, rawValue, sampleTime, False, foundConsole, writeTags, writeTagValues, log)
    
    elif not(validValidity) or not(validSQCValidity):
        log.tracef("%s *failed* validity checks", valueName)
        
        from ils.labData.limitWarning import notifyValidityLimitViolation
        foundConsole=notifyValidityLimitViolation(post, unitName, valueName, valueId, rawValue, sampleTime, tagProvider, database, upperValidityLimit, lowerValidityLimit)
        # Mark the tags as failed for now, If the notification found a console, then it will be a minute or two before the operator 
        # will determine whether or not to accept the value. (If we don't find a console then the same tags may be in this list with 
        # different values - not sure if that causes a problem)
        writeTags, writeTagValues = updateTags(tagProvider, unitName, valueName, rawValue, sampleTime, False, foundConsole, writeTags, writeTagValues, log)    
      
    else:
        log.tracef("%s passed all limit checks", valueName)
        storeValue(valueId, valueName, rawValue, sampleTime, unitName, log, tagProvider, database)
        writeTags, writeTagValues = updateTags(tagProvider, unitName, valueName, rawValue, sampleTime, True, True, writeTags, writeTagValues, log)
            
    # regardless of whether we passed or failed validation, add the value to the cache so we don't process it again
    lastValueCache = updateCache(lastValueCache, valueId, valueName, rawValue, sampleTime)
    
    return lastValueCache, writeTags, writeTagValues

# Handle a bad value.  Write the status to the status tag of the UDT
def handleBadLabValue(unitName, valueName, tagProvider, status, writeTags, writeTagValues):
    tagName="[%s]LabData/%s/%s" % (tagProvider, unitName, valueName)
    
    writeTags.append(str(tagName + "/status"))
    writeTagValues.append(status)
        
    return writeTags, writeTagValues


# Store a new lab value.  Insert the value into LtHistory and update LtValue with the id of the latest history value.
# This is called by one of two callers - directly by the scanner if the value is good or if the value is outside the limits and 
# the operator presses accept 
def storeValue(valueId, valueName, rawValue, sampleTime, unitName, log, tagProvider, database):
    log.trace("Storing %s - %s - %s - %s ..." % (valueName, str(valueId), str(rawValue), str(sampleTime)))

    from ils.common.grade import getGradeForUnit
    grade=getGradeForUnit(unitName, tagProvider)
    insertHistoryValue(valueName, valueId, rawValue, sampleTime, grade, log, database)


# This should be the only place anywhere that inserts into the LtHistory table.
def insertHistoryValue(valueName, valueId, rawValue, sampleTime, grade, log, database=""):
    log.tracef("Inserting %s (%d) %s at %s for grade %s", valueName, valueId, str(rawValue), str(sampleTime), str(grade))
    success = True  # If the row already exists then consider it a success
    insertedRows = 0

    sampleTimeType = type(sampleTime).__name__
    if sampleTimeType == "Date":
        log.tracef("sampleTime is a date, converting to a string...")
        sampleTime=system.db.dateFormat(sampleTime, "yyyy-MM-dd HH:mm:ss")
    elif sampleTimeType == "Timestamp":
        log.tracef("sampleTime is a **Timestamp**, converting to a string...")
        sampleTime=system.db.dateFormat(sampleTime, "yyyy-MM-dd HH:mm:ss")
    
    if sampleTime.find(".") > 0:
        sampleTime = sampleTime[:sampleTime.find(".")]

    SQL = "select count(*) from LtHistory where valueId = %i and RawValue = %s and SampleTime = '%s'" % (valueId, str(rawValue), sampleTime)
    rows = system.db.runScalarQuery(SQL, database)
    if rows == 0:
        try:
            # Step 1 - Insert the value into the lab history table.
            SQL = "insert into LtHistory (valueId, RawValue, Grade, SampleTime, ReportTime) values (%i, %s, '%s', '%s', getdate())" % (valueId, str(rawValue), grade, sampleTime)
            historyId = system.db.runUpdateQuery(SQL, database, getKey=1)
            log.tracef("...inserted value with history id: %d", historyId)
            
            # Step 2 - Update LtValue with the id of the latest history value
            SQL = "update LtValue set LastHistoryId = %d where valueId = %d" % (historyId, valueId)
            system.db.runUpdateQuery(SQL, database)
            success = True
            insertedRows = 1
        except:
            log.errorf("Failed to insert into a lab value for %s-%i, %s at %s, grade: %s", valueName, valueId, str(rawValue), str(sampleTime), str(grade))
            success = False
    else:
        ''' This isn't an error, due to timing we may get the same values twice, the check is just to prevent duplicates. '''
        log.tracef("Skipping insert of %s (%d) %s at %s for grade %s", valueName, valueId, str(rawValue), str(sampleTime), str(grade))
        
    return success, insertedRows

# This is called by a selector tag change script.  There is a listener on the SampleTime and on the value.  They both call this handler.
# When a measurement is received from the lab system the sampleTime tag and the value tag are updated almost atomically.  That action
# will fire off two calls to this procedure, this procedure doesn't know or care who called it.  It will read both tags to get the 
# current value.  Two identical insert statements will be attempted but the database will reject the second because of the unique index.
def storeSelector(tagRoot, database):
    selectorLog.trace("Storing selector of tag %s" % (tagRoot))

    tagProvider=tagRoot[1:tagRoot.find(']')]
    valueName=tagRoot[tagRoot.find('LabData/') + 8:]
    unitName=valueName[:valueName.find('/')]
    valueName=valueName[valueName.find('/') + 1:]
    selectorLog.trace("   ...the selector value name is <%s> (unit=%s)" % (valueName,unitName))

    # Read the value and the sample time
    vals = system.tag.readAll([tagRoot + '/value', tagRoot + '/sampleTime'])
    value=vals[0].value
    sampleTime=vals[1].value
    
    if value == None:
        selectorLog.warn("Detected a value of None for <%s>" % (valueName))
        return
    
    if sampleTime == None:
        selectorLog.warn("Detected a sample time of None for <%s>" % (valueName))
        return
    
    selectorLog.trace("   ...handling %s at %s" % (str(value), str(sampleTime)))
    
    # Fetch the value id using the name
    SQL = "select ValueId from LtValue where ValueName = '%s'" % (valueName)
    valueId=system.db.runScalarQuery(SQL, database)
    if valueId == None:
        selectorLog.error("Error storing lab value for selector <%s> due to unable to find name in LtValue" % (valueName))
        return
     
    storeValue(valueId, valueName, value, sampleTime, unitName, selectorLog, tagProvider, database)

    
def updateCache(lastValueCache, valueId, valueName, rawValue, sampleTime):
    lastValueCache[valueName]={'valueId': valueId, 'rawValue': rawValue, 'sampleTime': sampleTime}
    return lastValueCache


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
def updateTags(tagProvider, unitName, valueName, rawValue, sampleTime, valid, foundConsole, tags, tagValues, log, notifyConsole=True, statusMessage="bad - waiting for operator review"):
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
        if notifyConsole:
            if foundConsole:
                # The value is bad, there is a console and the operator has been notified
                log.trace("Value is bad and there is a console - Setting the bad value flag to TRUE")
                tags.append(tagName + "/badValue")
                tagValues.append(True)
                tags.append(tagName + "/status")
                tagValues.append(statusMessage)
            else:
                # The value is bad and we are supposed to notify the console for to approve/reject the value, but there isn't a console connected, 
                # so accept the value even though it is bad.
                log.trace("Value is bad, we are supposed to notify the console, but there isn't one so promote the bad value")
                tags.append(tagName + "/badValue")
                tagValues.append(True)
                tags.append(tagName + "/status")
                tagValues.append(statusMessage)
                tags.append(tagName + "/sampleTime")
                tagValues.append(sampleTime)
                tags.append(tagName + "/value")
                tagValues.append(rawValue)

        else:
            # The value is bad but we do not wish to notify the console so do not promote the bad value
            log.trace("Value is bad and we do not need to notify the console - Setting the bad value flag to TRUE")
            tags.append(tagName + "/badValue")
            tagValues.append(True)
            tags.append(tagName + "/status")
            tagValues.append(statusMessage)
        
    return tags, tagValues


# This is called on startup to load the most recent measurement into the cache
def initializeCache(database, lastValueCache):
    log.tracef("Initializing the last Value Cache...")
    
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
    return lastValueCache

def simulateReadRaw(itemIds, startDate, endDate):
    retVals = []
    phdLog.trace("--- Simulating Read Raw ---")
    for itemId in itemIds:
        valList = []
        SQL = "select * from history where itemId = '%s' and dateTime > '%s' and dateTime < '%s' " % (itemId, toDateString(startDate), toDateString(endDate))
        phdLog.trace(SQL)
        pds = system.db.runQuery(SQL, "PHD_SIMULATOR")
        for record in pds:
            dateTime = system.db.dateFormat(record["dateTime"], "yyyy-MM-dd HH:mm:ss.000")
            valList.append({"value": record["val"], "quality":"Good", "timestamp": dateTime})
        retVals.append(valList)
    
    return retVals