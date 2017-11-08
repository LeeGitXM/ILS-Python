'''
Created on Apr 11, 2017

@author: phass
'''

import system
logger=system.util.getLogger("com.ils.watchdog")


'''
This is called from a gateway timer script
'''
def scanOpcReadWatchdogs(tagProvider):
    projectName = system.util.getProjectName()
    if projectName == "[global]":
        print "Skipping the OPC Watchdog scanner for the global project"
        return
    
    logger.info("Scanning OPC Read watchdogs...")
    
    udtParentType = "OPC Read Watchdog"
    parentPath = "[%s]Site/Watchdogs" % (tagProvider)
        
    udts = system.tag.browseTags(
        parentPath=parentPath, 
        tagType="UDT_INST", 
        udtParentType="Watchdogs/" + udtParentType,
        recursive=True)
    
    logger.tracef("...Discovered %d read watchdog UDTs...", len(udts))
    
    for udt in udts:
        udtPath = udt.path
        logger.tracef("Found a %s at %s", udtParentType, udtPath)
        opcReadWatchdog(tagProvider, udtPath)


def opcReadWatchdog(tagProvider, udtPath):
    udtPath = "[%s]%s" % (tagProvider, udtPath)
    logger.tracef("Evaluating an opcReadWatchdog with <%s>", udtPath)
    
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
        
    logger.tracef("Path: %s, Current Value: %s, Change Strategy: %s, Read and Compare Strategy: %s, Last Value %s, Server Name: %s, Item Id: %s, Stall Count: %s", \
         udtPath, str(val), str(changeStrategy), str(readAndCompareStrategy), str(lastValue), str(serverName), str(itemId), str(stallCount))

    if changeStrategy:
        logger.tracef("Verifying the change Watchdog...")
        if val == lastValue:
            logger.errorf("FAILED the change test because the current value: %s and the last value %s, are the same", str(val), str(lastValue))
            changeTestFailed = True
        else:
            logger.tracef("Passed the value changed test")
            
        system.tag.write(udtPath+"/lastValue", val)
        
    if readAndCompareStrategy:
        logger.tracef("Verifying the read and compare watchdog...")
        currentVal = system.opc.readValue(serverName, itemId)
        
        if currentVal.quality.isGood():
            if val == currentVal.value:
                logger.tracef("Passed the readAndCompare test")
            else:
                readAndCompareTestFailed = True
                logger.errorf("Failed the readAndCompare test because %s and %s are not the same", str(val), str(currentVal.value))
        else:
            logger.errorf("Failed readAndCompare test because the quality is not good!")

    if changeTestFailed or readAndCompareTestFailed:
        system.tag.write(udtPath+"/stallCount", stallCount + 1)
    elif not(changeTestFailed or readAndCompareTestFailed) and stallCount > 0:
        system.tag.write(udtPath+"/stallCount", 0)

'''
This is called from a gateway timer script
'''
def scanOpcWriteWatchdogs(tagProvider):
    projectName = system.util.getProjectName()
    if projectName == "[global]":
        print "Skipping the OPC Watchdog scanner for the global project"
        return
    
    logger.info("Scanning OPC write watchdogs...")
    
    udtParentType = "OPC Write Watchdog"
        
    udts = system.tag.browseTags(
        parentPath="[XOM]Site/Watchdogs", 
        tagType="UDT_INST", 
        udtParentType="Watchdogs/" + udtParentType,
        recursive=True)
    
    logger.tracef("...Discovered %d write watchdog UDTs...", len(udts))
    
    for udt in udts:
        udtPath = udt.path
        logger.tracef("Found a %s at %s", udtParentType, udtPath)
        opcWriteWatchdog(tagProvider, udtPath)

'''
The write watchdog is mostly implemented on the DCS side.  The idea is that the DCS is incrementing a tag by 1 every so often.
Occasionally, Ignition needs to reset the tag as a signal that Ignition is alive.  If the tag value ever gets to some threshold, 
then the DCS concludes that Ignition is dead. 
'''
def opcWriteWatchdog(tagProvider, udtPath):
    udtPath = "[%s]%s" % (tagProvider, udtPath)
    logger.tracef("Evaluating an opcWriteWatchdog with <%s>", udtPath)
    
    vals = system.tag.readAll([udtPath+"/tag", 
                               udtPath+"/WriteEnabled", 
                               udtPath+"/writeValue",
                               udtPath+"/serverName",
                               udtPath+"/itemId",
                               udtPath+"/stallCount"
                               ])
    
    val=vals[0].value
    writeEnabled=vals[1].value
    writeValue=vals[2].value
    serverName=vals[3].value
    itemId=vals[4].value
    stallCount=vals[5].value

    stalled = False
        
    logger.tracef("  Path: %s\n  Current Value: %s\n  Write Enabled %s\n  Write Value %s\n  Server Name: %s\n  Item Id: %s\n  Stall Count: %s\n", \
         udtPath, str(val), str(writeEnabled), str(writeValue), str(serverName), str(itemId), str(stallCount))

    if writeEnabled:
        logger.tracef("Attempting watchdog write...")
        
        try:
            tagpath = udtPath + "/tag"
            logger.tracef("Writing %s to %s", str(writeValue), tagpath)
            system.tag.writeSynchronous(tagpath, writeValue)
            logger.tracef("Passed the watchdog write test")
        except:
            logger.errorf("FAILED the write test because the read value: %s and the written value %s, are not the same", str(val), str(writeValue))
            stalled = True
            
    if stalled:
        system.tag.write(udtPath+"/stallCount", stallCount + 1)
    elif not(stalled) and stallCount > 0:
        system.tag.write(udtPath+"/stallCount", 0)



def resetInterface(serverName):
    logger.infof("In %s.resetInterface()", __name__)
    
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
    logger.infof("In %s.notifyOC()", __name__)

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

        