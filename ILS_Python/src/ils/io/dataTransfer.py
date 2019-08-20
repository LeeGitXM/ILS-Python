'''
Created on Dec 20, 2017

@author: phass
'''

import system, time
from ils.queue.message import insert
from ils.io.util import getDatabaseFromTagPath
from ils.queue.constants import QUEUE_ERROR, QUEUE_WARNING, QUEUE_INFO 

MAX_TRIES = 3
log = system.util.getLogger("com.ils.io")

'''
This is called from the source tag of the "Data Transfer" UDT.
'''
def dataTransfer(tagPath, previousValue, currentValue, initialChange, missedEvents):
    dataTransferCore(tagPath, currentValue, initialChange)


'''
This is called from the sampleTime tag of the "Data Transfer" UDT.
Whenever the sample time changes we write the value.  The destination does not have a slot for the sample time, so
the first thing we need to do is to read the value that we want to transfer.  The current value here is the sample time.
'''
def dataTransferSampleTime(tagPath, previousValue, currentValue, initialChange, missedEvents):
    currentValue = system.tag.read("[.]source")
    dataTransferCore(tagPath, currentValue, initialChange)
            

def dataTransferCore(tagPath, currentValue, initialChange):
    if initialChange:
        system.tag.write("[.]status", "Skipping write because value is an initial change value")
        return
    
    latency = system.tag.read("[XOM]Configuration/Common/opcTagLatencySeconds").value
    messageQueue = system.tag.read("[.]messageQueue").value
    if messageQueue != "":
        db = getDatabaseFromTagPath(tagPath)
        
    permissive = system.tag.read("[.]permissive").value
    if permissive:
        tries = 0
        itemId = system.tag.read("[.]destination.OPCItemPath").value
        while tries < MAX_TRIES:
            try:
                system.tag.writeSynchronous("[.]destination", currentValue.value)
            except:
                tries = tries + 1
                time.sleep(latency)
            else:
                ''' The write was successful! '''
                txt = "Successfully wrote %s to %s at %s" % (str(currentValue.value), itemId, str(system.date.now()))
                log.infof(txt)
                system.tag.write("[.]status", txt)
                if messageQueue != "":
                    insert(messageQueue, QUEUE_INFO, txt, db)
                break

        if tries == MAX_TRIES:
            txt = "Write of %s to %s (%s) failed after %d tries" % (str(currentValue.value), itemId, tagPath, MAX_TRIES)
            log.errorf(txt)
            system.tag.write("[.]status", txt)
            if messageQueue != "":
                insert(messageQueue, QUEUE_ERROR, txt, db)
    else:
        system.tag.write("[.]status", "Skipping write because the permissive is false")

'''
This is called from the source tag of the "Data Transfer With Count" UDT.
'''
def dataTransferWithCount(tagPath, previousValue, currentValue, initialChange, missedEvents):    
    dataTransferWithCountCore(tagPath, currentValue, initialChange)


'''
This is called from the sampleTime tag of the "Data Transfer With Count" UDT.
Whenever the sample time changes we write the value.  The destination does not have a slot for the sample time, so
the first thing we need to do is to read the value that we want to transfer.  The current value here is the sample time.
'''
def dataTransferWithCountSampleTime(tagPath, previousValue, currentValue, initialChange, missedEvents):
    currentValue = system.tag.read("[.]source")
    dataTransferWithCountCore(tagPath, currentValue, initialChange)    
    

def dataTransferWithCountCore(tagPath, currentValue, initialChange):
    if initialChange:
        system.tag.write("[.]status", "Skipping write because value is an initial change value")
        return
    
    latency = system.tag.read("[XOM]Configuration/Common/opcTagLatencySeconds").value
    messageQueue = system.tag.read("[.]messageQueue").value
    if messageQueue != "":
        db = getDatabaseFromTagPath(tagPath)

    permissive = system.tag.read("[.]permissive").value
    count = system.tag.read("[.]countDestination").value
    if permissive:
        tries = 0
        itemId = system.tag.read("[.]destination.OPCItemPath").value
        while tries < MAX_TRIES:
            try:
                system.tag.writeSynchronous("[.]destination", currentValue.value)
                system.tag.writeSynchronous("[.]countDestination", count + 1)
            except:
                tries = tries + 1
                time.sleep(latency)
            else:
                ''' The write was successful! '''
                txt = "Successfully wrote %s to %s at %s" % (str(currentValue.value), itemId, str(system.date.now()))
                log.infof(txt)
                system.tag.write("[.]status", txt)
                if messageQueue != "":
                    insert(messageQueue, QUEUE_INFO, txt, db)
                break        

        if tries == MAX_TRIES:
            txt = "Write of %s to %s (%s) failed after %d tries" % (str(currentValue.value), itemId, tagPath, MAX_TRIES)
            log.errorf(txt)
            system.tag.write("[.]status", txt)
            if messageQueue != "":
                insert(messageQueue, QUEUE_ERROR, txt, db)

    else:
        system.tag.write("[.]status", "Skipping write because the permissive is false")


'''
This is called from the source tag of the "Data Transfer With Time" UDT.
'''
def dataTransferWithTime(tagPath, previousValue, currentValue, initialChange, missedEvents):
    dataTransferWithTimeCore(tagPath, currentValue, initialChange)


'''
This is called from the SampleTime tag of the "Data Transfer With Time" UDT.
'''
def dataTransferWithTimeSampleTime(tagPath, previousValue, currentValue, initialChange, missedEvents):
    currentValue = system.tag.read("[.]source")
    dataTransferWithTimeCore(tagPath, currentValue, initialChange) 
   

def dataTransferWithTimeCore(tagPath, currentValue, initialChange):
    if initialChange:
        system.tag.write("[.]status", "Skipping write because value is an initial change value")
        return
    
    latency = system.tag.read("[XOM]Configuration/Common/opcTagLatencySeconds").value
    messageQueue = system.tag.read("[.]messageQueue").value
    if messageQueue != "":
        db = getDatabaseFromTagPath(tagPath)

    from ils.common.util import unixTime
    ut = unixTime(currentValue.timestamp)
    permissive = system.tag.read("[.]Permissive").value
    if permissive:
        itemId = system.tag.read("[.]destination.OPCItemPath").value
        tries = 0
        while tries < MAX_TRIES:
            try:
                system.tag.writeSynchronous("[.]destination", currentValue.value)
                system.tag.writeSynchronous("[.]timeDestination", ut)
            except:
                tries = tries + 1
                time.sleep(latency)
            else:
                ''' The write was successful! '''
                txt = "Successfully wrote %s to %s at %s" % (str(currentValue.value), itemId, str(system.date.now()))
                log.infof(txt)
                system.tag.write("[.]status", txt)
                if messageQueue != "":
                    insert(messageQueue, QUEUE_INFO, txt, db)
                break

        if tries == MAX_TRIES:
            txt = "Write of %s to %s (%s) failed after %d tries" % (str(currentValue.value), itemId, tagPath, MAX_TRIES)
            log.errorf(txt)
            system.tag.write("[.]status", txt)
            if messageQueue != "":
                insert(messageQueue, QUEUE_ERROR, txt, db)


'''
This is called from the triggerTag of the "HDA Transfer Driven" UDT.
'''
def dataTransferToHDA(tagPath, previousValue, currentValue, initialChange, missedEvents):
    if initialChange:
        system.tag.write("[.]error", "Skipping write because value is an initial change value")
        return
    
    hdaInterface = system.tag.read("[.]hdaInterface").value
    destinationHDAItemID = system.tag.read("[.]destinationHDAItemID").value
    manualPermissive = system.tag.read("[.]manualPermissive").value
    expressionPermissive = system.tag.read("[.]expressionPermissive").value
    
    #Check permissives
    if not manualPermissive or not expressionPermissive:
        system.tag.write("[.]error", "Permissives false")
    else:
        #Check server
        serverIsAvailable=system.opchda.isServerAvailable(hdaInterface)
        if serverIsAvailable == False:
            system.tag.write("[.]error", "Server not avaliable")
        else:
            #Read value
            sourceQv = system.tag.read("[.]valueToWrite")
            if sourceQv.quality.isGood():
                sourceVal = sourceQv.value
                now = system.date.now()
                tagQuality = system.opchda.insertReplace(hdaInterface,destinationHDAItemID,sourceVal,now,192)
                system.tag.write("[.]error", "Tag write with quality " + str(tagQuality))
                system.tag.write("[.]lastUpdate", now)
            else:
                system.tag.write("[.]error", "Source tag bad quality")


'''
This is called from all three of the "source" tags (expressionSource, memorySource, opcSource) of the "HDA Transfer Simple" UDT.
'''
def writeToHDA(tagPath, previousValue, currentValue, initialChange, missedEvents):
    if initialChange:
        system.tag.write("[.]status", "Skipping write because value is an initial change value")
        return
    
    latency = system.tag.read("[XOM]Configuration/Common/opcTagLatencySeconds").value
    messageQueue = system.tag.read("[.]messageQueue").value
    if messageQueue != "":
        db = getDatabaseFromTagPath(tagPath)

    hdaServer = system.tag.read("[.]hdaServer").value
    itemId = system.tag.read("[.]hdaItemId").value
    
    serverIsAvailable=system.opchda.isServerAvailable(hdaServer)
    if serverIsAvailable == False:
        txt = "Write of %s to %s (%s) skipped because server not available" % (str(currentValue.value), itemId, tagPath)
        log.errorf(txt)
        system.tag.write("[.]status", txt)
        if messageQueue != "":
            insert(messageQueue, QUEUE_ERROR, txt, db)
        return

    if not(currentValue.quality.isGood()):
        txt = "Write of %s to %s (%s) skipped because the source value is bad." % (str(currentValue.value), itemId, tagPath)
        log.errorf(txt)
        system.tag.write("[.]status", txt)
        if messageQueue != "":
            insert(messageQueue, QUEUE_ERROR, txt, db)
        return
    
    val = currentValue.value
    timestamp = currentValue.timestamp
    tries = 0
    while tries < MAX_TRIES:
        try:
            tagQuality = system.opchda.insertReplace(hdaServer, itemId, val, timestamp, 192)
            system.tag.write("[.]status", "Tag write with quality " + str(tagQuality))
        except:
            tries = tries + 1
            time.sleep(latency)
        else:
            ''' The write was successful! '''
            txt = "Successfully wrote %s to %s (%s)" % (str(currentValue.value), itemId, tagPath)
            log.infof(txt)
            system.tag.write("[.]status", txt)
            if messageQueue != "":
                insert(messageQueue, QUEUE_INFO, txt, db)
            break

    if tries == MAX_TRIES:
        txt = "Write of %s to %s (%s) failed after %d tries" % (str(currentValue.value), itemId, tagPath, MAX_TRIES)
        log.errorf(txt)
        system.tag.write("[.]status", txt)
        if messageQueue != "":
            insert(messageQueue, QUEUE_ERROR, txt, db)

'''
This is called from the triggerTag of the HDA UDT.
Unlike everything else in this module, this method reads from the HDA server!
'''
def hda(tagPath, previousValue, currentValue, initialChange, missedEvents):
    hdaInterface = system.tag.read("[.]hdaInterface").value
    itemID = system.tag.read("[.]itemID").value
    maxPoints = system.tag.read("[.]maxPoints").value
    maxAgeHours = system.tag.read("[.]maxAgeHours").value
    lastTimestamp = system.tag.read("[.]timestamp").value
    
    if maxPoints == None or maxAgeHours == None or initialChange:
        system.tag.write("[.]error", "Skip processing due to initial change or unexpected Null value")
    else:    
        #Calculate start and end date
        startDate = system.date.now()
        system.tag.write("[.]lastUpdate", startDate)
        endDate = system.date.addHours(startDate, -1*maxAgeHours)
        
        #Check server
        serverIsAvailable=system.opchda.isServerAvailable(hdaInterface)
        if serverIsAvailable == False:
            system.tag.write("[.]error", "Server not avaliable")
        else:
            system.tag.write("[.]error", "OK")
            #Read results
            retVals = system.opchda.readRaw(hdaInterface, [itemID], startDate, endDate, maxPoints, 0)
            #Check if we get a value back
            if len(retVals) != 1:
                system.tag.write("[.]error", "A value was not returned")
            else:
                #Break apart the vales list
                valueList = retVals[0]
                if str(valueList.serviceResult) != 'Good':
                    system.tag.write("[.]error", "Returned value not good")
                if valueList.size()==0:
                    system.tag.write("[.]error", "Returned size 0")
                else:
                    #OK let's assume the first qualified value in list is most recent?
                    #New data let take it apart
                    #qvCurrent = valueList.serviceResult[0]
                    #if qvCurrent.timestamp > lastTimestamp:
                    historyHeaders = ["value", "timestamp", "quality"]
                    historyLs = []
                    foundNewData = False
                    for qv in valueList:
                        historyLs.append([qv.value, qv.timestamp, qv.quality])
                        if qv.timestamp > lastTimestamp:
                            lasttimestamp = qv.timestamp
                            foundNewData = True
                            qvCurrent = qv
                    if foundNewData == True:
                        historyDs = system.dataset.toDataSet(historyHeaders, historyLs)
                        system.tag.write("[.]value", qvCurrent.value)
                        system.tag.write("[.]timestamp", qvCurrent.timestamp)
                        system.tag.write("[.]quality", qvCurrent.quality)
                        system.tag.write("[.]history", historyDs)
                        system.tag.write("[.]error", "OK")
                    else:
                        system.tag.write("[.]error", "No new data")

