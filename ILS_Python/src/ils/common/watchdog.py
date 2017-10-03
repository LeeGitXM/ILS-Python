'''
Created on Apr 11, 2017

@author: phass
'''

import system
logger=system.util.getLogger("com.ils.watchdog")

def scanOpcWatchdogs(arg):
    projectName = system.util.getProjectName()
    if projectName == "[global]":
        print "Skipping the OPC Watchdog scanner for the global project"
        return
    
    logger.info("Scanning OPC watchdogs...")
    
    for udtParentType in ["OPC Read Watchdog"]:
        
        udts = system.tag.browseTags(
            parentPath="[XOM]Site/Watchdogs", 
            tagType="UDT_INST", 
            udtParentType="Watchdogs/" + udtParentType,
            recursive=True)
        
        logger.tracef("...Discovered %d watchdog UDTs...", len(udts))
        
        for udt in udts:
            udtPath = udt.path
            logger.tracef("Found a %s at %s", udtParentType, udtPath)
            
            if udtParentType == "OPC Read Watchdog":
                opcReadWatchdog(udtPath)
            else:
                logger.errorf("Unexpected watchdog type: %s", udtParentType)

def opcReadWatchdog(udtPath):
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

    stalled = False
        
    logger.tracef("  Path: %s\n  Current Value: %s\n  Change Strategy: %s\n  Read and Compare Strategy: %s\n  Last Value %s\n  Server Name: %s\n  Item Id: %s\n  Stall Count: %s\n", \
         udtPath, str(val), str(changeStrategy), str(readAndCompareStrategy), str(lastValue), str(serverName), str(itemId), str(stallCount))

    if changeStrategy:
        logger.tracef("Verifying the change Watchdog...")
        if val == lastValue:
            logger.errorf("FAILED the change test because the current value: %s and the last value %s, are the same", str(val), str(lastValue))
            stalled = True
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
                stalled = True
                logger.errorf("Failed the readAndCompare test because %s and %s are not the same", str(val), str(currentVal.value))
        else:
            logger.errorf("Failed readAndCompare test because the quality is not good!")

    if stalled:
        system.tag.write(udtPath+"/stallCount", stallCount + 1)
    elif not(stalled) and stallCount > 0:
        system.tag.write(udtPath+"/stallCount", 0)

def resetInterface(event):
    logger.infof("In %s.resetInterface()", __name__)
    opcInterface = getOpcInterfaceFromEvent(event)
    if opcInterface == None:
        return
    print "OPC Interface: ", opcInterface

def notifyOC(event):
    logger.infof("In %s.notifyOC()", __name__)
    opcInterface = getOpcInterfaceFromEvent(event)
    if opcInterface == None:
        return
    print "OPC Interface: ", opcInterface

def getOpcInterfaceFromEvent(event):
    print "Event: ", event
    source = event.get("source", None)
    if source == None:
        return None

    return "foo"
        