'''
Created on Dec 20, 2017

@author: phass
'''

import system, time
from ils.queue.message import insert
from ils.io.util import readTag, writeTag, getProviderFromTagPath
from ils.queue.constants import QUEUE_ERROR, QUEUE_WARNING, QUEUE_INFO
from ils.config.common import getTagProvider

MAX_TRIES = 3
from ils.log import getLogger
log = getLogger(__name__)

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
    currentValue = readTag("[.]source")
    dataTransferCore(tagPath, currentValue, initialChange)
            

def dataTransferCore(tagPath, currentValue, initialChange):
    if initialChange:
        writeTag("[.]status", "Skipping write because value is an initial change value")
        return

    provider = getProviderFromTagPath(tagPath)
    latency = readTag("[%s]Configuration/Common/opcTagLatencySeconds" % (provider)).value
    messageQueue = readTag("[.]messageQueue").value
    db = readTag("[.]database").value

    permissive = readTag("[.]permissive").value
    if permissive:
        tries = 0
        itemId = readTag("[.]destination.OPCItemPath").value
        while tries < MAX_TRIES:
            try:
                system.tag.writeBlocking(["[.]destination"], [currentValue.value])
            except:
                tries = tries + 1
                time.sleep(latency)
            else:
                ''' The write was successful! '''
                txt = "Successfully wrote %s to %s at %s" % (str(currentValue.value), itemId, str(system.date.now()))
                log.infof(txt)
                writeTag("[.]status", txt)
                if messageQueue != "" and db != "":
                    insert(messageQueue, QUEUE_INFO, txt, db)
                break

        if tries == MAX_TRIES:
            txt = "Write of %s to %s (%s) failed after %d tries" % (str(currentValue.value), itemId, tagPath, MAX_TRIES)
            log.errorf(txt)
            writeTag("[.]status", txt)
            if messageQueue != "" and db != "":
                insert(messageQueue, QUEUE_ERROR, txt, db)
    else:
        writeTag("[.]status", "Skipping write because the permissive is false")

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
    currentValue = readTag("[.]source")
    dataTransferWithCountCore(tagPath, currentValue, initialChange)    
    

def dataTransferWithCountCore(tagPath, currentValue, initialChange):
    if initialChange:
        writeTag("[.]status", "Skipping write because value is an initial change value")
        return

    provider = getProviderFromTagPath(tagPath)
    latency = readTag("[%s]Configuration/Common/opcTagLatencySeconds" % (provider)).value
    messageQueue = readTag("[.]messageQueue").value
    db = readTag("[.]database").value

    permissive = readTag("[.]permissive").value
    count = readTag("[.]countDestination").value
    if permissive:
        tries = 0
        itemId = readTag("[.]destination.OPCItemPath").value
        while tries < MAX_TRIES:
            try:
                system.tag.writeBlocking(
                        ["[.]destination", "[.]countDestination"], 
                        [currentValue.value, count + 1])
            except:
                tries = tries + 1
                time.sleep(latency)
            else:
                ''' The write was successful! '''
                txt = "Successfully wrote %s to %s at %s" % (str(currentValue.value), itemId, str(system.date.now()))
                log.infof(txt)
                writeTag("[.]status", txt)
                if messageQueue != "" and db != "":
                    insert(messageQueue, QUEUE_INFO, txt, db)
                break        

        if tries == MAX_TRIES:
            txt = "Write of %s to %s (%s) failed after %d tries" % (str(currentValue.value), itemId, tagPath, MAX_TRIES)
            log.errorf(txt)
            writeTag("[.]status", txt)
            if messageQueue != "" and db != "":
                insert(messageQueue, QUEUE_ERROR, txt, db)

    else:
        writeTag("[.]status", "Skipping write because the permissive is false")


'''
This is called from the source tag of the "Data Transfer With Time" UDT.
'''
def dataTransferWithTime(tagPath, previousValue, currentValue, initialChange, missedEvents):
    dataTransferWithTimeCore(tagPath, currentValue, initialChange)


'''
This is called from the SampleTime tag of the "Data Transfer With Time" UDT.
'''
def dataTransferWithTimeSampleTime(tagPath, previousValue, currentValue, initialChange, missedEvents):
    currentValue = readTag("[.]source")
    dataTransferWithTimeCore(tagPath, currentValue, initialChange) 
   

def dataTransferWithTimeCore(tagPath, currentValue, initialChange):
    if initialChange:
        writeTag("[.]status", "Skipping write because value is an initial change value")
        return

    provider = getProviderFromTagPath(tagPath)
    latency = readTag("[%s]Configuration/Common/opcTagLatencySeconds" % (provider)).value
    messageQueue = readTag("[.]messageQueue").value
    db = readTag("[.]database").value

    from ils.common.util import unixTime
    ut = unixTime(currentValue.timestamp)
    permissive = readTag("[.]Permissive").value
    if permissive:
        itemId = readTag("[.]destination.OPCItemPath").value
        tries = 0
        while tries < MAX_TRIES:
            try:
                system.tag.writeBlocking(
                        ["[.]destination", "[.]timeDestination"], 
                        [currentValue.value, ut])
            except:
                tries = tries + 1
                time.sleep(latency)
            else:
                ''' The write was successful! '''
                txt = "Successfully wrote %s to %s at %s" % (str(currentValue.value), itemId, str(system.date.now()))
                log.infof(txt)
                writeTag("[.]status", txt)
                if messageQueue != "" and db != "":
                    insert(messageQueue, QUEUE_INFO, txt, db)
                break

        if tries == MAX_TRIES:
            txt = "Write of %s to %s (%s) failed after %d tries" % (str(currentValue.value), itemId, tagPath, MAX_TRIES)
            log.errorf(txt)
            writeTag("[.]status", txt)
            if messageQueue != "" and db != "":
                insert(messageQueue, QUEUE_ERROR, txt, db)


'''
This is called from the triggerTag of the "HDA Transfer Driven" UDT.
'''
def dataTransferToHDA(tagPath, previousValue, currentValue, initialChange, missedEvents):
    if initialChange:
        writeTag("[.]error", "Skipping write because value is an initial change value")
        return
    
    hdaInterface = readTag("[.]hdaInterface").value
    destinationHDAItemID = readTag("[.]destinationHDAItemID").value
    manualPermissive = readTag("[.]manualPermissive").value
    expressionPermissive = readTag("[.]expressionPermissive").value
    
    #Check permissives
    if not manualPermissive or not expressionPermissive:
        writeTag("[.]error", "Permissives false")
    else:
        #Check server
        serverIsAvailable=system.opchda.isServerAvailable(hdaInterface)
        if serverIsAvailable == False:
            writeTag("[.]error", "Server not avaliable")
        else:
            #Read value
            sourceQv = readTag("[.]valueToWrite")
            if sourceQv.quality.isGood():
                sourceVal = sourceQv.value
                now = system.date.now()
                tagQuality = system.opchda.insertReplace(hdaInterface,destinationHDAItemID,sourceVal,now,192)
                writeTag("[.]error", "Tag write with quality " + str(tagQuality))
                writeTag("[.]lastUpdate", now)
            else:
                writeTag("[.]error", "Source tag bad quality")


'''
This is called from all three of the "source" tags (expressionSource, memorySource, opcSource) of the "HDA Transfer Simple" UDT.
'''
def writeToHDA(tagPath, previousValue, currentValue, initialChange, missedEvents):
    if initialChange:
        writeTag("[.]status", "Skipping write because value is an initial change value")
        return

    provider = getProviderFromTagPath(tagPath)
    latency = readTag("[%s]Configuration/Common/opcTagLatencySeconds" % (provider)).value
    messageQueue = readTag("[.]messageQueue").value
    db = readTag("[.]database").value

    hdaServer = readTag("[.]hdaServer").value
    itemId = readTag("[.]hdaItemId").value
    
    serverIsAvailable=system.opchda.isServerAvailable(hdaServer)
    if serverIsAvailable == False:
        txt = "Write of %s to %s (%s) skipped because server not available" % (str(currentValue.value), itemId, tagPath)
        log.errorf(txt)
        writeTag("[.]status", txt)
        if messageQueue != "" and db != "":
            insert(messageQueue, QUEUE_ERROR, txt, db)
        return

    if not(currentValue.quality.isGood()):
        txt = "Write of %s to %s (%s) skipped because the source value is bad." % (str(currentValue.value), itemId, tagPath)
        log.errorf(txt)
        writeTag("[.]status", txt)
        if messageQueue != "" and db != "":
            insert(messageQueue, QUEUE_ERROR, txt, db)
        return
    
    val = currentValue.value
    timestamp = currentValue.timestamp
    tries = 0
    while tries < MAX_TRIES:
        try:
            tagQuality = system.opchda.insertReplace(hdaServer, itemId, val, timestamp, 192)
            writeTag("[.]status", "Tag write with quality " + str(tagQuality))
        except:
            tries = tries + 1
            time.sleep(latency)
        else:
            ''' The write was successful! '''
            txt = "Successfully wrote %s to %s (%s)" % (str(currentValue.value), itemId, tagPath)
            log.infof(txt)
            writeTag("[.]status", txt)
            if messageQueue != "" and db != "":
                insert(messageQueue, QUEUE_INFO, txt, db)
            break

    if tries == MAX_TRIES:
        txt = "Write of %s to %s (%s) failed after %d tries" % (str(currentValue.value), itemId, tagPath, MAX_TRIES)
        log.errorf(txt)
        writeTag("[.]status", txt)
        if messageQueue != "" and db != "":
            insert(messageQueue, QUEUE_ERROR, txt, db)

'''
This is called from the triggerTag of the HDA UDT.
Unlike everything else in this module, this method reads from the HDA server!
'''
def hda(tagPath, previousValue, currentValue, initialChange, missedEvents):
    hdaInterface = readTag("[.]hdaInterface").value
    itemID = readTag("[.]itemID").value
    maxPoints = readTag("[.]maxPoints").value
    maxAgeHours = readTag("[.]maxAgeHours").value
    lastTimestamp = readTag("[.]timestamp").value
    
    if maxPoints == None or maxAgeHours == None or initialChange:
        writeTag("[.]error", "Skip processing due to initial change or unexpected Null value")
    else:    
        #Calculate start and end date
        startDate = system.date.now()
        writeTag("[.]lastUpdate", startDate)
        endDate = system.date.addHours(startDate, -1*maxAgeHours)
        
        #Check server
        serverIsAvailable=system.opchda.isServerAvailable(hdaInterface)
        if serverIsAvailable == False:
            writeTag("[.]error", "Server not avaliable")
        else:
            writeTag("[.]error", "OK")
            #Read results
            retVals = system.opchda.readRaw(hdaInterface, [itemID], startDate, endDate, maxPoints, 0)
            #Check if we get a value back
            if len(retVals) != 1:
                writeTag("[.]error", "A value was not returned")
            else:
                #Break apart the vales list
                valueList = retVals[0]
                if str(valueList.serviceResult) != 'Good':
                    writeTag("[.]error", "Returned value not good")
                if valueList.size()==0:
                    writeTag("[.]error", "Returned size 0")
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
                        writeTag("[.]value", qvCurrent.value)
                        writeTag("[.]timestamp", qvCurrent.timestamp)
                        writeTag("[.]quality", qvCurrent.quality)
                        writeTag("[.]history", historyDs)
                        writeTag("[.]error", "OK")
                    else:
                        writeTag("[.]error", "No new data")

