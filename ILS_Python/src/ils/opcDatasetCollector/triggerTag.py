'''
Created on Nov 29, 2015

@author: Pete
'''

def setValues(udtTagPath):
    import system
    print "Inside external ils.opcDatasetCollector.triggerTag.setValues"
    # Get the dataset of tagpaths
    print udtTagPath
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
    # Don't need to check if tag exists because would not get nto code if it did not exist
    print "Trigger Tagpath: %s" % (triggerTagPath)
    triggerTagQv = system.tag.read(triggerTagPath)
    # Check if quality good, otherwise leave
    if triggerTagQv.quality.isGood():
        epochTriggerTimestampMinutes = (triggerTagQv.timestamp.getTime() / 1000 / 60) 
    else:
        print "Trigger Tag quality is bad returning %s:" % (triggerTagPath)
        return
    # Initialize timestamps aligned to True, 
    timestampsAligned = True
    for row in pyDsTagPaths:
        print row
        tagPath = row["TagPath"]
        print "TagPath: %s" % (tagPath)
        valueRow = row["Row"]  # This is the row poistion in the value dataset where value goes
        print "Row Position in Dataset: %i" % (valueRow)
        valueCol = row["Col"]  # This is the row poistion in the value dataset where value goes
        print "Column Position in Dataset: %i" % (valueCol)
        useOPC = row["UseOPC"]  # Use OPC Value
        print "Use OPC: %s" % (useOPC)
        defaultValue = row["DefaultValue"]  # Default Value can ve "LastValue"
        print "Default Value: %s" % (defaultValue)
        tagExists = True  # Set to default value only applies for tags if OPC this is left as true
        if not(useOPC):  # Collect from a tag
            # Check if tag exists
            tagExists = system.tag.exists(tagPath)
            if tagExists:
                # Read tag value            
                qv = system.tag.read(tagPath)
            else:
                # Print a statement regarding not finding a tag
                print "OPC Dataset Collector - could not find a tag:"
                print "Unknown tagpath: %s" % (tagPath)
                print "Dataset Tags row/column location: row %i, column %i" % (int(valueRow), int(valueCol))
                print "OPC Dataset Collector Tagpath: %s" % (udtTagPath)
                # #
                alignTimestamps = False  # Don't assign data if tag does not exist, this is trick to not assign data
        else:  # OPC tag read
            # Assume opc value
            # ##!!! Put a check in here that opc and itemId != "" and that opc server exitsts
            opcServer = row['OPCServer']
            itemId = row['ItemID']
            print "OPC Server: %s" % (opcServer)
            print "OPC Item ID: %s" % (itemId)
            # Read tag value            
            qv = system.opc.readValue(opcServer, itemId)
        # Extract the value and assign to holding dataset
        if tagExists and qv.quality.isGood():
            value = qv.value
            quality = qv.quality
            timestamp = qv.timestamp
            print "Value: %s" % (value)
            print "Quality: %s" % (quality)
            print "Timestamp: %s" % (timestamp)
            # print qv.timestamp.getClass().getName() a little trick to return class name if a java class
            epochTimestampMinutes = (qv.timestamp.getTime() / 1000 / 60)
            diffMinutes = abs(epochTriggerTimestampMinutes - epochTimestampMinutes)
            # Check if timestamps aligned - if just one not aligned then we won't assign data back to tag
            if alignTimestamps:
                if diffMinutes > alignWindowMinutes:
                    timestampsAligned = False
            # Assign to Dataset Value
            dsTagValues = system.dataset.setValue(dsTagValues, valueRow, valueCol, str(value))
        else:
            if tagExists:
                if not(qv.quality.isGood()):  # Print a statement regarding not finding a tag
                    print "OPC Dataset Collector - quality of tag 'Bad'"
                    print "Dataset Tags row/column location: row %i, column %i" % (int(valueRow), int(valueCol))
                    print "OPC Dataset Collector Tagpath: %s" % (udtTagPath)
            alignTimestamps = False  # Don't assign data if tag does not exist, this is trick to not assign data
    # Assign to Dataset Values if timestamps aligned
    # Get the current time so we can update last update time and trigger time
    from java.util import Date
    now = Date()  # Creates a new date, for right now  
    if alignTimestamps:
        if timestampsAligned:
            system.tag.write(udtTagPath + "/Dataset Values", dsTagValues)
            system.tag.write(udtTagPath + "/Last Update Time", now)
    else:
        system.tag.write(udtTagPath + "/Dataset Values", dsTagValues)
        system.tag.write(udtTagPath + "/Last Update Time", now)
    system.tag.write(udtTagPath + "/Last Trigger Time", now)

