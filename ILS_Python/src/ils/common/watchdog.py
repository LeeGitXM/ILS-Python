'''
Created on Apr 11, 2017

@author: phass
'''

import system
from ils.log import getLogger
log =getLogger(__name__)

'''
This is called from a gateway timer script. It doesn't make sense to call this for isolation.
(The UDTS do not exist in isolation as they get converted to folders. )
'''
def scanLabDataWatchdogs(tagProvider):
    projectName = system.util.getProjectName()
    if projectName == "[global]":
        print "Skipping the Lab Data Watchdog scanner for the global project"
        return
    
    log.info("Scanning Lab Data watchdogs...")
    
    udtParentType = "Lab Data Watchdog"
    parentPath = "[%s]Site/Watchdogs" % (tagProvider)
        
    udts = system.tag.browseTags(
        parentPath=parentPath, 
        tagType="UDT_INST", 
        udtParentType="Watchdogs/" + udtParentType,
        recursive=True)
    
    log.tracef("...discovered %d Lab Data watchdog UDTs...", len(udts))
    
    for udt in udts:
        udtPath = udt.path
        log.tracef("Found a %s at %s", udtParentType, udtPath)
        labDataWatchdog(tagProvider, udtPath)


def labDataWatchdog(tagProvider, udtPath):
    udtPath = "[%s]%s" % (tagProvider, udtPath)
    log.tracef("Evaluating a Lab Data Watchdog with <%s>", udtPath)
    
    vals = system.tag.readAll([
                udtPath+"/currentValue", 
                udtPath+"/lastValue",
                udtPath+"/maxStalls",
                udtPath+"/stallCount"
                ])
    
    currentValue=vals[0].value
    lastValue=vals[1].value
    maxStalls=vals[2].value
    stallCount=vals[3].value
    
    if stallCount == None:
        stallCount = 0

    changeTestFailed = False
 
    log.tracef("Current Value: %d, Last Value: %d, maxStalls: %d, Stall Count: %d", currentValue, lastValue, maxStalls, stallCount )

    if currentValue == lastValue:
        log.errorf("FAILED the change test because the current value: %s and the last value %s, are the same", str(currentValue), str(lastValue))
        changeTestFailed = True
    else:
        log.tracef("Passed the value changed test")
        
    system.tag.write(udtPath+"/lastValue", currentValue)

    if changeTestFailed:
        system.tag.write(udtPath+"/stallCount", stallCount + 1)
    else:
        system.tag.write(udtPath+"/stallCount", 0)

'''
This is called from a gateway timer script. It doesn't make sense to call this for isolation.
(The UDTS do not exist in isolation as they get converted to folders. )
'''
def scanOpcReadWatchdogs(tagProvider):
    projectName = system.util.getProjectName()
    if projectName == "[global]":
        print "Skipping the OPC Watchdog scanner for the global project"
        return
    
    log.info("Scanning OPC Read watchdogs...")
    
    udtParentType = "OPC Read Watchdog"
    parentPath = "[%s]Site/Watchdogs" % (tagProvider)
        
    udts = system.tag.browseTags(
        parentPath=parentPath, 
        tagType="UDT_INST", 
        udtParentType="Watchdogs/" + udtParentType,
        recursive=True)
    
    log.tracef("...Discovered %d read watchdog UDTs...", len(udts))
    
    for udt in udts:
        udtPath = udt.path
        log.tracef("Found a %s at %s", udtParentType, udtPath)
        opcReadWatchdog(tagProvider, udtPath)


def opcReadWatchdog(tagProvider, udtPath):
    udtPath = "[%s]%s" % (tagProvider, udtPath)
    log.tracef("Evaluating an opcReadWatchdog with <%s>", udtPath)
    
    vals = system.tag.readAll([udtPath+"/tag", 
                               udtPath+"/changeStrategy", 
                               udtPath+"/readAndCompareStrategy",
                               udtPath+"/lastValue",
                               udtPath+"/serverName",
                               udtPath+"/itemId",
                               udtPath+"/stallCount"
                               ])
    
    val=vals[0].value
    changeStrategy=vals[1].value
    readAndCompareStrategy=vals[2].value
    lastValue=vals[3].value
    serverName=vals[4].value
    itemId=vals[5].value
    stallCount=vals[6].value
    
    if stallCount == None:
        stallCount = 0

    changeTestFailed = False
    readAndCompareTestFailed = False
        
    log.tracef("Path: %s, Current Value: %s, Change Strategy: %s, Read and Compare Strategy: %s, Last Value %s, Server Name: %s, Item Id: %s, Stall Count: %s", \
         udtPath, str(val), str(changeStrategy), str(readAndCompareStrategy), str(lastValue), str(serverName), str(itemId), str(stallCount))

    if changeStrategy:
        log.tracef("Verifying the change Watchdog...")
        if val == lastValue:
            log.errorf("FAILED the change test because the current value: %s and the last value %s, are the same", str(val), str(lastValue))
            changeTestFailed = True
        else:
            log.tracef("Passed the value changed test")
            
        system.tag.write(udtPath+"/lastValue", val)

# Not sure what this test is meant to do!!!!        
    if readAndCompareStrategy:
        log.tracef("Verifying the read and compare watchdog...")
        currentVal = system.opc.readValue(serverName, itemId)
        
        if currentVal.quality.isGood():
            if val == currentVal.value:
                log.tracef("Passed the readAndCompare test")
            else:
                readAndCompareTestFailed = True
                log.errorf("Failed the readAndCompare test because %s and %s are not the same", str(val), str(currentVal.value))
        else:
            log.errorf("Failed readAndCompare test because the quality is not good!")

    if changeTestFailed or readAndCompareTestFailed:
        system.tag.write(udtPath+"/stallCount", stallCount + 1)
    elif not(changeTestFailed or readAndCompareTestFailed) and stallCount > 0:
        system.tag.write(udtPath+"/stallCount", 0)

'''
This is called from a gateway timer script.  It doesn't make sense to call this for isolation.
(The UDTS do not exist in isolation as they get converted to folders. )
'''
def scanOpcWriteWatchdogs(tagProvider):
    projectName = system.util.getProjectName()
    if projectName == "[global]":
        print "Skipping the OPC Watchdog scanner for the global project"
        return
    
    log.info("Scanning OPC write watchdogs...")
    
    udtParentType = "OPC Write Watchdog"
    
    udts = system.tag.browseTags(
        parentPath="[%s]Site/Watchdogs" % (tagProvider), 
        tagType="UDT_INST", 
        udtParentType="Watchdogs/" + udtParentType,
        recursive=True)
    
    log.tracef("...Discovered %d write watchdog UDTs...", len(udts))
    
    for udt in udts:
        udtPath = udt.path
        log.tracef("Found a %s at %s", udtParentType, udtPath)
        opcWriteWatchdog(tagProvider, udtPath)

'''
The write watchdog is mostly implemented on the DCS side.  The idea is that the DCS is incrementing a tag by 1 every so often.
Occasionally, Ignition needs to reset the tag as a signal that Ignition is alive.  If the tag value ever gets to some threshold, 
then the DCS concludes that Ignition is dead. 
'''
def opcWriteWatchdog(tagProvider, udtPath):
    udtPath = "[%s]%s" % (tagProvider, udtPath)
    log.tracef("Evaluating an opcWriteWatchdog with <%s>", udtPath)
    
    vals = system.tag.readAll([udtPath+"/tag", 
                               udtPath+"/WriteEnabled", 
                               udtPath+"/writeValue",
                               udtPath+"/serverName",
                               udtPath+"/itemId",
                               udtPath+"/stallCount",
                               udtPath+"/internallyDriven",
                               udtPath+"/maxWriteValue"
                               ])
    
    val=vals[0].value
    writeEnabled=vals[1].value
    writeValue=vals[2].value
    serverName=vals[3].value
    itemId=vals[4].value
    stallCount=vals[5].value
    internallyDriven=vals[6].value
    maxWriteVal=vals[7].value
    
    globalWriteEnabled = system.tag.read("[%s]Configuration/Common/writeEnabled" % (tagProvider)).value

    stalled = False
    
    if internallyDriven:
        print "Internally driven watchdog..."
        writeValue += 1
        print "writeValue = ", writeValue
        if writeValue > maxWriteVal:
            writeValue = 1
        tagpath = udtPath + "/writeValue"
        system.tag.write(tagpath, writeValue)
        
    log.tracef("  Path: %s\n  Current Value: %s\n  Write Enabled %s\n  Write Value %s\n  Server Name: %s\n  Item Id: %s\n  Stall Count: %s\n", \
         udtPath, str(val), str(writeEnabled), str(writeValue), str(serverName), str(itemId), str(stallCount))

    if writeEnabled and globalWriteEnabled:
        log.tracef("Attempting watchdog write...")
        
        try:
            tagpath = udtPath + "/tag"
            log.tracef("Writing %s to %s", str(writeValue), tagpath)
            system.tag.writeSynchronous(tagpath, writeValue)
            log.tracef("Passed the watchdog write test")
        except:
            log.errorf("FAILED the write watchdog test because the synchronous write to (%s) failed", tagpath)
            stalled = True
            
    if stalled:
        system.tag.write(udtPath+"/stallCount", stallCount + 1)
    elif not(stalled) and stallCount > 0:
        system.tag.write(udtPath+"/stallCount", 0)


'''
This is called from a gateway timer script. It doesn't make sense to call this for isolation.
(The UDTS do not exist in isolation as they get converted to folders. )
'''
def scanHdaReadWatchdogs(tagProvider):
    projectName = system.util.getProjectName()
    if projectName == "[global]":
        print "Skipping the HDA Watchdog scanner for the global project"
        return
    
    log.info("Scanning HDA Read watchdogs...")
    
    udtParentType = "HDA Watchdog"
    parentPath = "[%s]Site/Watchdogs" % (tagProvider)
        
    udts = system.tag.browseTags(
        parentPath=parentPath, 
        tagType="UDT_INST", 
        udtParentType="Watchdogs/" + udtParentType,
        recursive=True)
    
    log.tracef("...Discovered %d HDA Read watchdog UDTs...", len(udts))
    
    for udt in udts:
        udtPath = udt.path
        log.tracef("Found a %s at %s", udtParentType, udtPath)
        opcHdaReadWatchdog(tagProvider, udtPath)

def opcHdaReadWatchdog(tagProvider, udtPath):
    udtPath = "[%s]%s" % (tagProvider, udtPath)
    log.tracef("Evaluating an opcHdaReadWatchdog with <%s>", udtPath)
    
    vals = system.tag.readAll([udtPath+"/serverName",
                               udtPath+"/itemId",
                               udtPath+"/lastSampleValue",
                               udtPath+"/lastSampleTime",
                               udtPath+"/maxStalls",
                               udtPath+"/stallCount"
                               ])
    
    serverName=vals[0].value
    itemId=vals[1].value
    lastSampleValue=vals[2].value
    lastSampleTime=vals[3].value
    maxStalls=vals[4].value
    stallCount=vals[5].value
    
    if stallCount == None:
        stallCount = 0

    sampleTimeChanged = False
    vals = []
    tags = []
    manualEntryOverride = system.tag.read("[%s]Configuration/LabData/manualEntryOverride" % (tagProvider)).value
    if manualEntryOverride:
        system.tag.write("[%s]Configuration/LabData/manualEntryPermitted" % (tagProvider), True)
    
    log.tracef("Path: %s, Last Value: %s, Last Sample Time %s, Server Name: %s, Item Id: %s, Stall Count: %s", \
         udtPath, str(lastSampleValue), str(lastSampleTime), str(serverName), str(itemId), str(stallCount))

    ''' The first check is to just use the Ignition API to see if the server is available '''
    serverIsAvailable = system.opchda.isServerAvailable(serverName)
    system.tag.write(udtPath+"/connectionAvailable", serverIsAvailable)
    
    if not(serverIsAvailable):
        log.errorf("The HDA server (%s) is *NOT* available as determined by calling system.opchda.isServerAvailable()!", serverName)
    else:
        log.tracef("The HDA server (%s) is available as determined by calling system.opchda.isServerAvailable()!", serverName)
    
        ''' The second check is to call the HDA readRaw API and verify that the sample time has updated - the value is expected to always be 1. '''
        endDate = system.date.now()
        startDate = system.date.addMinutes(endDate, -30)
        boundingValues = False
        maxValues = 0

        log.tracef("Reading the sample value and time...")
        retVals = system.opchda.readRaw(serverName, [itemId], startDate, endDate, maxValues, boundingValues)
        log.tracef("...back from readRaw, %d values were returned! (%s)", len(retVals), str(retVals))
        sampleTimeChanged = False
        
        if len(retVals) != 1:
            log.errorf("A value was not returned for the HDA watchdog <%s - %s>", serverName, itemId)
        else:
            #Break apart the vales list
            valueList = retVals[0]
            if str(valueList.serviceResult) != 'Good':
                log.errorf("HDA watchdog <%s - %s> Returned value not good", serverName, itemId)
            if valueList.size() == 0:
                log.errorf("HDA watchdog <%s - %s> Returned size 0", serverName, itemId)
            else:
                ''' 
                I'm not sure if there is a spec about the order of data returned by this API, but the Vistalon HDA server orders
                the from oldest to newest. (This shouldn't return a lot of values, so iterate and then take the last value).
                '''
                for qv in valueList:
                    sampleValue = qv.value
                    sampleTime = qv.timestamp
                    quality = qv.quality

                log.tracef("Returned value: %s - %s - %s", str(sampleValue), str(sampleTime), str(quality))

                tags.append(udtPath+"/lastSampleValue")
                vals.append(sampleValue)
                
                tags.append(udtPath+"/lastSampleTime")
                vals.append(sampleTime)
        
                if sampleTime != lastSampleTime:
                    sampleTimeChanged = True
                else:
                    sampleTimeChanged = False

    if not(serverIsAvailable) or not(sampleTimeChanged):
        tags.append(udtPath+"/stallCount")
        vals.append(stallCount + 1)
        if stallCount > maxStalls:
            system.tag.write("[%s]Configuration/LabData/communicationHealthy" % (tagProvider), False)
            system.tag.write("[%s]Configuration/LabData/manualEntryPermitted" % (tagProvider), True)
    
    elif serverIsAvailable and sampleTimeChanged and stallCount > 0:
        ''' I'm not exactly sure what the scenario is that this handles  '''
        tags.append(udtPath+"/stallCount")
        vals.append(0)
        system.tag.write("[%s]Configuration/LabData/communicationHealthy" % (tagProvider), True)
        if not(manualEntryOverride):
            system.tag.write("[%s]Configuration/LabData/manualEntryPermitted" % (tagProvider), False)
    
    elif stallCount == 0:
        system.tag.write("[%s]Configuration/LabData/communicationHealthy" % (tagProvider), True)
        if not(manualEntryOverride):
            system.tag.write("[%s]Configuration/LabData/manualEntryPermitted" % (tagProvider), False)

    if len(tags) > 0:
        system.tag.writeAll(tags, vals)
     
'''
-------------------------------------------------------------------------------------------------
'''
def resetInterface(serverName):
    log.infof("In %s.resetInterface()", __name__)
    
    if serverName == None:
        return
    
    print "OPC Interface: ", serverName
    
    from com.inductiveautomation.ignition.gateway import SRContext
    from com.inductiveautomation.ignition.gateway.opc import OPCServerSettingsRecord
    from simpleorm.dataset import SQuery
    context = SRContext.get()
    
    try:
        query = SQuery(OPCServerSettingsRecord.META)
        query.eq(OPCServerSettingsRecord.Name, serverName)
        r = context.getPersistenceInterface().queryOne(query)
        context.getPersistenceInterface().notifyRecordUpdated(r)
    except:
        pass


def notifyOC(serverName, retryCounter, post):
    '''
    This is called from an alarm pipeline, which runs in global scope.
    '''
    log.infof("In %s.notifyOC()", __name__)

    print "OPC Interface: ", serverName
    
    project = "XOM"
    topMessage = "Communication error for OPC server %s" % (serverName)
    bottomMessage = "Communication is still bad after %s reset attempts" % (str(retryCounter))
    
    mainMessage = "<HTML>OPC Communication to %s is still bad after %s attempts to automatically reset the interface. "\
        "No further retry attempts will be attempted!  Notify the systems group and your AE." % (serverName, retryCounter)

    buttonLabel = "Ack"
    db = "XOM"
    
    # This is generally called from the gateway, but should work from th
    from ils.common.ocAlert import sendAlert
    sendAlert(project, post, topMessage, bottomMessage, mainMessage, buttonLabel,  db=db)

