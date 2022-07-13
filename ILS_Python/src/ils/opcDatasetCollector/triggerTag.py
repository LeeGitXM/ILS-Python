'''
Created on Dec, 2015

@author: Jeff
'''
from ils.io.util import readTag, writeTag

def setValues(udtTagPath):
    import system
    # Get a logger
    from ils.log import getLogger
    log = getLogger(__name__)
    log.trace("Inside external ils.opcDatasetCollector.triggerTag.setValues")
    # Get the dataset of tagpaths
    log.tracef("UDT Tagpath: %s", str(udtTagPath))
    dsTagPaths = readTag(udtTagPath + "/Dataset Tags").value  # Recall a qualified value so need .value
    pyDsTagPaths = system.dataset.toPyDataSet(dsTagPaths)  # Easier to work with py dataset for tagpaths
    # Get the dataset of values.  Datasets are immutable so this is just a copy not actual dataset
    dsTagValues = readTag(udtTagPath + "/Dataset Values").value  # Recall a qualified value so need .value
    # Next we iterate through dataset of tagpaths and assign to the dataset of tag values
    # Need a counter to track for first row
    alignTimestamps = readTag(udtTagPath + "/Align Timestamps").value
    alignWindowMinutes = readTag(udtTagPath + "/Align Window Minutes").value
    # Read the trigger tag first, need the timestamp for comparison
    triggerTagPath = readTag(udtTagPath + "/Trigger Tagpath").value  # This is the Trigger Tag path
    # Don't need to check if tag exists because would not get into code if it did not exist -- << Not true
    if triggerTagPath==None:
        log.warnf("opcDatasetCollector: Null trigger tagpath: for %s", str(udtTagPath))
        return
    
    log.tracef("Trigger Tagpath: %s", triggerTagPath)
    triggerTagQv = readTag(triggerTagPath)
    # Read maximum # of rows to read
    maxRowNumberToRead = readTag(udtTagPath + "/Maximum Row Number to Read").value 
    # Check if quality good, otherwise leave
    if triggerTagQv.quality.isGood():
        epochTriggerTimestampMinutes = (triggerTagQv.timestamp.getTime() / 1000 / 60) 
    else:
        log.tracef("Trigger Tag quality is bad returning: %s", triggerTagPath)
        return
    # Initialize timestamps aligned to True, 
    timestampsAligned = True
    #This is the count of consecutive scans that had at least one bad quality tag
    fallbackCntr = readTag(udtTagPath + "/Fallback Scan Counter").value
    fallbackMaxScans = readTag(udtTagPath + "/Fallback Max Number of Scans").value
    # Increment Last Good Value counter once per scan eg only a single increment for scan even if > 1 bad tag
    incrementedFallbackForScan = False
    # A flag to say its OK to update dataset
    updateDs = True
    for row in pyDsTagPaths:
        tagPath = row["TagPath"]
        log.tracef("TagPath: %s", tagPath)
        valueRow = row["Row"]  # This is the row poistion in the value dataset where value goes
        log.tracef("Row Position in Dataset: %s", str(valueRow))
        valueCol = row["Col"]  # This is the row poistion in the value dataset where value goes
        log.tracef("Column Position in Dataset: %s", str(valueCol))
        useOPC = row["UseOPC"]  # Use OPC Value
        log.tracef("Use OPC: %s", useOPC)
        dataType = row["DataType"]  # Use OPC Value
        log.tracef("Data Type: %s", dataType)
        fallbackValue = row["FallbackValue"]  # Default Value can ve "LastValue"
        log.tracef("Default Value: %s", fallbackValue)
        tagExists = True  # Set to default value only applies for tags if OPC this is left as true
        # Process # of rows dynamically
        if maxRowNumberToRead == -1 or (valueRow <= maxRowNumberToRead):
            if not(useOPC):  # Collect from a tag
                # Check if tag exists
                tagExists = system.tag.exists(tagPath)
                if tagExists:
                    # Read tag value            
                    qv = readTag(tagPath)
                else:
                    # Print a statement regarding not finding a tag
                    log.trace("OPC Dataset Collector - could not find a tag:")
                    log.trace("Unknown tagpath: %s" % (str(tagPath)))
                    log.trace("Dataset Tags row/column location: row %i, column %i" % (int(valueRow), int(valueCol)))
                    log.trace("OPC Dataset Collector Tagpath: %s" % (udtTagPath))
                    alignTimestamps = False  # Don't assign data if tag does not exist, this is trick to not assign data
            else:  # OPC tag read
                # Assume opc value
                # ##!!! Need to check what happens during system read if item-id and/or OPC Server not really there
                opcServer = row['OPCServer']
                itemId = row['ItemID']
                log.tracef("OPC Server: %s", opcServer)
                log.tracef("OPC Item ID: %s", itemId)
                # Read tag value            
                qv = system.opc.readValue(opcServer, itemId)
            # Extract the value and convert data, for OPC we don't know if tagExists so tagExists = true for OPC
            if tagExists:
                if dataType == "Float":
                    try:
                        value = float(qv.value)
                    except:
                        value = -99999999999999.99
                if dataType == "Integer":
                    try:
                        value = int(qv.value)
                    except:
                        value = -99999999999999
                else:
                    value = str(qv.value)
            elif not(useOPC): #This value only applies to Ignition tags as for direct OPC don't know if tag exists
                value = "The Ignition Tag %s does not exist." % (tagPath)
            if tagExists and qv.quality.isGood():
                quality = qv.quality
                timestamp = qv.timestamp
                log.tracef("Value: %s", value)
                log.tracef("Quality: %s", quality)
                log.tracef("Timestamp: %s", timestamp)
                # print qv.timestamp.getClass().getName() a little trick to return class name if a java class
                epochTimestampMinutes = (qv.timestamp.getTime() / 1000 / 60)
                diffMinutes = abs(epochTriggerTimestampMinutes - epochTimestampMinutes)
                # Check if timestamps aligned - if just one not aligned then we won't assign data back to tag
                if alignTimestamps:
                    if diffMinutes > alignWindowMinutes:
                        timestampsAligned = False
                # Assign to Dataset Value
                dsTagValues = system.dataset.setValue(dsTagValues, valueRow, valueCol, str(value))
            else: # Here we assume quality is bad.  For direct OPC either because OPC says bad or OPC item not existing
                if tagExists:
                    log.trace("OPC Dataset Collector - quality of tag 'Bad'")
                    log.tracef("Dataset Tags row/column location: row %i, column %i", int(valueRow), int(valueCol))
                    log.tracef("OPC Dataset Collector Tagpath: %s", udtTagPath)
                    if fallbackValue == "Use Bad":
                        log.trace("Fallback Value: Use Bad")
                        dsTagValues = system.dataset.setValue(dsTagValues, valueRow, valueCol, value)
                    elif fallbackValue == "Last Good":
                        # Here you don't do anything just use last value we read in the dataset
                        log.trace("Fallback Value: Last Good")                
                else:
                    #Basically write a value saying tag does not exist
                    dsTagValues = system.dataset.setValue(dsTagValues, valueRow, valueCol, "Tag Does Not Exist")
                #Increment counter for # of scans with at least one bad quality read  
                if not(incrementedFallbackForScan):
                    fallbackCntr = fallbackCntr + 1  
                    incrementedFallbackForScan = True
    #Update fallback counter - if none of the tags were bad then we reset the counter to 0
    if not(incrementedFallbackForScan):
        writeTag(udtTagPath + "/Fallback Scan Counter", 0)
        fallbackCntr = 0
    else:
        writeTag(udtTagPath + "/Fallback Scan Counter", fallbackCntr)
    #Next check max # of scans with a bad value
    if fallbackMaxScans > 0 and fallbackCntr > fallbackMaxScans:
        updateDs = False
    # Assign to Dataset Values if timestamps aligned
    # Get the current time so we can update last update time and trigger time
    from java.util import Date
    now = Date()  # Creates a new date, for right now
    if updateDs:  
        if alignTimestamps:
            if timestampsAligned:
                writeTag(udtTagPath + "/Dataset Values", dsTagValues)
                writeTag(udtTagPath + "/Last Update Time", now)
        else:
            writeTag(udtTagPath + "/Dataset Values", dsTagValues)
            writeTag(udtTagPath + "/Last Update Time", now)
    writeTag(udtTagPath + "/Last Trigger Time", now)

