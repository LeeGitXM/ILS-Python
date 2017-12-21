'''
Created on Dec 20, 2017

@author: phass
'''

import system

'''
This is called from the triggerTag of the HDA UDT.
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

'''
This is called from the Source of the "Data Transfer" UDT.
'''
def dataTransfer(tagPath, previousValue, currentValue, initialChange, missedEvents):
    qv = system.tag.read("[.]Permissive")
    if qv.value:
        system.tag.write("[.]Destination", currentValue.value)
        

'''
This is called from the Source of the "Data Transfer With Count" UDT.
'''
def dataTransferWithCount(tagPath, previousValue, currentValue, initialChange, missedEvents):
    qv = system.tag.read("[.]Permissive")
    if qv.value:
        system.tag.write("[.]Destination", currentValue.value)
        qv = system.tag.read("[.]CountDestination")
        system.tag.write("[.]CountDestination", qv.value + 1)
    

'''
This is called from the Source of the "Data Transfer With Count" UDT.
'''
def dataTransferWithTime(tagPath, previousValue, currentValue, initialChange, missedEvents):
    from ils.common.util import unixTime
    qv = system.tag.read("[.]Permissive")
    if qv.value:
        system.tag.write("[.]Destination", currentValue.value)
        ut = unixTime(currentValue.timestamp)
        system.tag.write("[.]TimeDestination", ut)
        

'''
This is called from the triggerTag of the "Data Transfer Tag to HDA" UDT.
'''
def dataTransferToHDA(tagPath, previousValue, currentValue, initialChange, missedEvents):
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
