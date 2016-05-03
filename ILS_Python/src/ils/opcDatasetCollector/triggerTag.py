'''
Created on Dec, 2015

@author: Jeff
'''

def setValues(udtTagPath):
    import system
    # Get a logger
    logger = system.util.getLogger("com.ils.opcDatasetCollector")
    logger.trace("Inside external ils.opcDatasetCollector.triggerTag.setValues")
    # Get the dataset of tagpaths
    logger.tracef("UDT Tagpath: %s", str(udtTagPath))
    dsTagPaths = system.tag.read(udtTagPath + "/Dataset Tags").value  # Recall a qualified value so need .value
    pyDsTagPaths = system.dataset.toPyDataSet(dsTagPaths)  # Easier to work with py dataset for tagpaths
    # Get the dataset of values.  Datasets are immutable so this is just a copy not actual dataset
    dsTagValues = system.tag.read(udtTagPath + "/Dataset Values").value  # Recall a qualified value so need .value
    # Next we iterate through dataset of tagpaths and assign to the dataset of tag values
    # Need a counter to track for first row
    alignTimestamps = system.tag.read(udtTagPath + "/Align Timestamps").value
    alignWindowMinutes = system.tag.read(udtTagPath + "/Align Window Minutes").value
    # Read the trigger tag first, need the timestamp for comparison
    triggerTagPath = system.tag.read(udtTagPath + "/Trigger Tagpath").value  # This is the Trigger Tag path
    # Don't need to check if tag exists because would not get into code if it did not exist -- << Not true
    if triggerTagPath==None:
        logger.warnf("opcDatasetCollector: Null trigger tagpath: for %s", str(udtTagPath))
        return
    
    logger.tracef("Trigger Tagpath: %s", triggerTagPath)
    triggerTagQv = system.tag.read(triggerTagPath)
    # Read maximum # of rows to read
    maxRowNumberToRead = system.tag.read(udtTagPath + "/Maximum Row Number to Read").value 
    # Check if quality good, otherwise leave
    if triggerTagQv.quality.isGood():
        epochTriggerTimestampMinutes = (triggerTagQv.timestamp.getTime() / 1000 / 60) 
    else:
        logger.tracef("Trigger Tag quality is bad returning: %s", triggerTagPath)
        return
    # Initialize timestamps aligned to True, 
    timestampsAligned = True
    #This is the count of consecutive scans that had at least one bad quality tag
    fallbackCntr = system.tag.read(udtTagPath + "/Fallback Scan Counter").value
    fallbackMaxScans = system.tag.read(udtTagPath + "/Fallback Max Number of Scans").value
    # Increment Last Good Value counter once per scan eg only a single increment for scan even if > 1 bad tag
    incrementedFallbackForScan = False
    # A flag to say its OK to update dataset
    updateDs = True
    for row in pyDsTagPaths:
        tagPath = row["TagPath"]
        logger.tracef("TagPath: %s", tagPath)
        valueRow = row["Row"]  # This is the row poistion in the value dataset where value goes
        logger.tracef("Row Position in Dataset: %s", str(valueRow))
        valueCol = row["Col"]  # This is the row poistion in the value dataset where value goes
        logger.tracef("Column Position in Dataset: %s", str(valueCol))
        useOPC = row["UseOPC"]  # Use OPC Value
        logger.tracef("Use OPC: %s", useOPC)
        dataType = row["DataType"]  # Use OPC Value
        logger.tracef("Data Type: %s", dataType)
        fallbackValue = row["FallbackValue"]  # Default Value can ve "LastValue"
        logger.tracef("Default Value: %s", fallbackValue)
        tagExists = True  # Set to default value only applies for tags if OPC this is left as true
        # Process # of rows dynamically
        if maxRowNumberToRead == -1 or (valueRow <= maxRowNumberToRead):
            if not(useOPC):  # Collect from a tag
                # Check if tag exists
                tagExists = system.tag.exists(tagPath)
                if tagExists:
                    # Read tag value            
                    qv = system.tag.read(tagPath)
                else:
                    # Print a statement regarding not finding a tag
                    logger.trace("OPC Dataset Collector - could not find a tag:")
                    logger.tracef("Unknown tagpath: %s", tagPath)
                    logger.tracef("Dataset Tags row/column location: row %i, column %i", int(valueRow), int(valueCol))
                    logger.tracef("OPC Dataset Collector Tagpath: %s", udtTagPath)
                    alignTimestamps = False  # Don't assign data if tag does not exist, this is trick to not assign data
            else:  # OPC tag read
                # Assume opc value
                # ##!!! Need to check what happens during system read if item-id and/or OPC Server not really there
                opcServer = row['OPCServer']
                itemId = row['ItemID']
                logger.tracef("OPC Server: %s", opcServer)
                logger.tracef("OPC Item ID: %s", itemId)
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
            else: #This value only applies to Ignition tags as for direct OPC don't know if tag exists
                value = "The Ignition Tag %s does not exist." % (tagPath)
            if tagExists and qv.quality.isGood():
                quality = qv.quality
                timestamp = qv.timestamp
                logger.tracef("Value: %s", value)
                logger.tracef("Quality: %s", quality)
                logger.tracef("Timestamp: %s", timestamp)
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
                    logger.trace("OPC Dataset Collector - quality of tag 'Bad'")
                    logger.tracef("Dataset Tags row/column location: row %i, column %i", int(valueRow), int(valueCol))
                    logger.tracef("OPC Dataset Collector Tagpath: %s", udtTagPath)
                    if fallbackValue == "Use Bad":
                        logger.trace("Fallback Value: Use Bad")
                        dsTagValues = system.dataset.setValue(dsTagValues, valueRow, valueCol, value)
                    elif fallbackValue == "Last Good":
                        # Here you don't do anything just use last value we read in the dataset
                        logger.trace("Fallback Value: Last Good")                
                else:
                    #Basically write a value saying tag does not exist
                    dsTagValues = system.dataset.setValue(dsTagValues, valueRow, valueCol, "Tag Does Not Exist")
                #Increment counter for # of scans with at least one bad quality read  
                if not(incrementedFallbackForScan):
                    fallbackCntr = fallbackCntr + 1  
                    incrementedFallbackForScan = True
    #Update fallback counter - if none of the tags were bad then we reset the counter to 0
    if not(incrementedFallbackForScan):
        system.tag.write(udtTagPath + "/Fallback Scan Counter", 0)
        fallbackCntr = 0
    else:
        system.tag.write(udtTagPath + "/Fallback Scan Counter", fallbackCntr)
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
                system.tag.write(udtTagPath + "/Dataset Values", dsTagValues)
                system.tag.write(udtTagPath + "/Last Update Time", now)
        else:
            system.tag.write(udtTagPath + "/Dataset Values", dsTagValues)
            system.tag.write(udtTagPath + "/Last Update Time", now)
    system.tag.write(udtTagPath + "/Last Trigger Time", now)

