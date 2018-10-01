'''
Created on Jul 21, 2015

@author: Pete
'''
import system, string
from ils.migration.common import lookupOPCServerAndScanClass

def translateTags(rootContainer):
    table = rootContainer.getComponent("Power Table")
    ds = table.data
    pds = system.dataset.toPyDataSet(ds)
    rootFolder = rootContainer.getComponent("Root Folder").text
    
    translations = []
    row = 0
    for record in pds:
        tagName = record["name"]
        alternateNames = record["names"]
        folder = record["folder"]
        tagPath = "%s/%s/%s" % (rootFolder, folder, tagName)
        tokens = alternateNames.split(" ")
        print "Row %i: %s" % (row, tokens)
        
        for token in tokens:
            translations.append(["insert into TagMap (GSIName, TagPath, DataType) values ('%s', '%s','DOUBLE');" % (token, tagPath)])
        row = row + 1
    
    print translations
    translationTable = rootContainer.getComponent("Translation Table")
    ds = system.dataset.toDataSet(['Translation'], translations)
    translationTable.data = ds

def saveTranslationFile(rootContainer):
    filename = system.file.saveFile("outputData.sql", "sql", "An SQL file")
    if filename == None:
        return
    
    translationTable = rootContainer.getComponent("Translation Table")
    ds = translationTable.data
    pds = system.dataset.toPyDataSet(ds)
    
    append = False
    for record in pds:
        system.file.writeFile(filename, record["Translation"] + "\n", append)
        append = True

def load(rootContainer):
    filename=rootContainer.getComponent("File Field").text
    if not(system.file.fileExists(filename)):
        system.gui.messageBox("The file does not exist!")
        return
    
    contents = system.file.readFileAsString(filename, "US-ASCII")
    records = contents.split('\n')
    
    ds=parseRecords(records,"")
    table=rootContainer.getComponent("Power Table")
    table.data=ds
        
    print "Done Loading!"

def parseRecords(records,recordType):        
    print "Parsing %s records..." % (recordType)

    i = 0
    numTokens=100
    data = []    
    for line in records:
        line=line[:len(line)-1] #Strip off the last character which is some sort of CRLF
        tokens = line.split(',')

        if i == 0:
            line = "status,skip," + line.replace(" ","")
            line=line.rstrip(',')
            header = line.split(',')
            numTokens=len(header)
        else:
            if recordType == "" or string.upper(tokens[0]) == recordType:
                line = " ,False," + line
                tokens = line.split(',')
                print "Tokens: ", tokens
                if len(tokens) != numTokens:
                    for j in range(len(tokens), numTokens):
                        tokens.append("")
                print "Line %i now has %i tokens" % (i, len(tokens))
                data.append(tokens)
                
        i = i + 1

    print "Header: ", header
    print "Data: ", data
        
    ds = system.dataset.toDataSet(header, data)
    print "   ...parsed %i %s records!" % (len(data), recordType)
    return ds

def clearStatus(rootContainer):
    table=rootContainer.getComponent("Power Table")
    ds=table.data
    for row in range(ds.rowCount):
        ds=system.dataset.setValue(ds, row, "status", "")
    table.data=ds
    
def skipAll(rootContainer):
    table=rootContainer.getComponent("Power Table")
    ds=table.data
    for row in range(ds.rowCount):
        ds=system.dataset.setValue(ds, row, "skip", True)
    table.data=ds

def createAll(rootContainer):
    table=rootContainer.getComponent("Power Table")
    ds=table.data
    for row in range(ds.rowCount):
        ds=system.dataset.setValue(ds, row, "skip", False)
    table.data=ds
    
def createTags(rootContainer):
    table=rootContainer.getComponent("Power Table")
    ds=table.data
    site = rootContainer.getComponent("Site").text
    provider = rootContainer.getComponent("Tag Provider").text
    rootFolder = rootContainer.getComponent("Root Folder").text
    folderFilter = rootContainer.getComponent("Filters").getComponent("Folder").text
    classFilter = rootContainer.getComponent("Filters").getComponent("Class").text
    itemIdPrefix = system.tag.read("[" + provider + "]Configuration/DiagnosticToolkit/itemIdPrefix").value

    for row in range(ds.rowCount):
        status = ""
        folder = ds.getValueAt(row, "Folder")
        className =  ds.getValueAt(row, "class")
        skip = ds.getValueAt(row, "skip")
        if (string.upper(skip) == "TRUE"):
            status = "Skipped"
        elif (folderFilter == "" or folder == folderFilter) and (classFilter == "" or className == classFilter):
            
            className =  ds.getValueAt(row, "class")
            outputName = ds.getValueAt(row, "name")
            outputName = filterName(outputName)
            outputNames = ds.getValueAt(row, "names")
            
            if className in ["FLOAT-PARAMETER", "FLOAT-VARIABLE", "LOGICAL-VARIABLE"]:
                path = rootFolder + "/" + folder
                parentPath = '[' + provider + ']' + path    
                tagPath = parentPath + "/" + outputName
                tagExists = system.tag.exists(tagPath)
            
                if tagExists:
                    print tagPath, " already exists!"
                    status = "Exists"
                else:
                    print "Creating a %s named <%s>" % (className, outputName)
                    if className == "FLOAT-PARAMETER":
                        system.tag.addTag(parentPath=parentPath, name=outputName, tagType="MEMORY", dataType="Float8",
                                          attributes={"ScanClass": "Expression-Fast"})
                        status = "Created"
                    elif className == "FLOAT-VARIABLE":
                        expression =  ds.getValueAt(row, 6)
                        system.tag.addTag(parentPath=parentPath, name=outputName, tagType="EXPRESSION", dataType="Float8",
                                          attributes={"Expression":expression, "ScanClass": "Expression-Fast"})
                        status = "Created"
                    elif className == "LOGICAL-VARIABLE":
                        expression =  ds.getValueAt(row, 6)
                        system.tag.addTag(parentPath=parentPath, name=outputName, tagType="EXPRESSION", dataType="Boolean",
                                          attributes={"Expression":expression, "ScanClass": "Expression-Fast"})
                        status = "Created"
                    else:
                        status = "Error"
            else:
                gsiInterface = ds.getValueAt(row, "gsi-interface")
                itemId = ds.getValueAt(row, "itemId")
    #            conditionalItemId = ds.getValueAt(row, "Conditional ItemId")
                
                if itemId <> "":
                    itemId = itemIdPrefix + itemId
                    serverName, scanClass, permissiveScanClass, writeLocationId = lookupOPCServerAndScanClass(site, gsiInterface)
                
                path = rootFolder + "/" + folder
                print folder, outputName, itemId, serverName
                
                parentPath = '[' + provider + ']' + path    
                tagPath = parentPath + "/" + outputName
                tagExists = system.tag.exists(tagPath)
            
                if tagExists:
                    print tagPath, " already exists!"
                    status = "Exists"
                else:
                    print "---------------------------"
                    print "Folder: ", folder
                    print "Class: ", className
                    print "Name: ", outputName
                    print "Names: ", outputNames
                    print "GSI Interface: ", gsiInterface
                    print "Item Id: ", itemId
                
                    if className == "OPC-TEXT-OUTPUT":
                        createOutput(parentPath, outputName, itemId, serverName, scanClass, outputNames, "String")
                        status = "Created"
                    elif className == "FLOAT-PARAMETER":
                        initialValue = ds.getValueAt(row, "initial-value")
                        createParameter(parentPath, outputName, scanClass, "Float8", initialValue)
                        status = "Created"
                    elif className == "OPC-FLOAT-OUTPUT":
                        createOutput(parentPath, outputName, itemId, serverName, scanClass, outputNames, "Float")
                        status = "Created"
                    elif className == "OPC-INT-OUTPUT":
                        createOutput(parentPath, outputName, itemId, serverName, scanClass, outputNames, "Integer")
                        status = "Created"
                    elif className == "OPC-FLOAT-BAD-FLAG":
                        createBadFlag(parentPath, outputName, itemId, serverName, scanClass, outputNames, "Float")
                        status = "Created"
                    elif className == "OPC-INT-BAD-FLAG":
                        createBadFlag(parentPath, outputName, itemId, serverName, scanClass, outputNames, "Integer")
                        status = "Created"
                    elif className == "OPC-TEXT-BAD-FLAG":
                        createBadFlag(parentPath, outputName, itemId, serverName, scanClass, outputNames, "String")
                        status = "Created"
                    elif className == "OPC-TEXT-CONDITIONAL-FLOAT-OUTPUT":
                        # This column doesn't sound right for the permissive item id, but I think the columns just got a little 
                        # screwed up during export so the header doesn't match the column
                        permissiveItemId = ds.getValueAt(row, "mode-item-Id")
                        createConditionalOutut(parentPath, outputName, itemId, permissiveItemId, serverName, 
                                                scanClass, outputNames, "Float", "String")
                        status = "Created"
                    elif className == "OPC-TEXT-CONDITIONAL-TEXT-OUTPUT":
                        # This column doesn't sound right for the permissive item id, but I think the columns just got a little 
                        # screwed up during export so the header doesn't match the column
                        permissiveItemId = ds.getValueAt(row, "mode-item-Id")
                        createConditionalOutut(parentPath, outputName, itemId, permissiveItemId, serverName, 
                                                scanClass, outputNames, "String", "String")
                        status = "Created"
                    elif className in ["OPC-PKS-CONTROLLER", "OPC-PKS-DIGITAL-CONTROLLER", "OPC-PKS-EHG-CONTROLLER", "OPC-PKS-EHG-DIGITAL-CONTROLLER"]:
                        modeItemId = ds.getValueAt(row, "mode-item-id")
                        permissiveItemId = ds.getValueAt(row, "mode-permissive-item-id")
                        spItemId = ds.getValueAt(row, "write-target-item-id")
                        # For som ereason that I can't figure out, I couldn't use the column name for this one column...
                        windupItemId = ds.getValueAt(row, 12)
                        print "Output Disposability: ", windupItemId
    #                    windupItemId = ds.getValueAt(row, "output-disposability-item-id")
                        createPKSController(parentPath, outputName, itemId, modeItemId, permissiveItemId, spItemId, windupItemId, 
                                            serverName, scanClass, permissiveScanClass, outputNames)
                        status = "Created"                
                    elif className == "OPC-PKS-ACE-CONTROLLER":
                        modeItemId = ds.getValueAt(row, "mode-item-id")
                        permissiveItemId = ds.getValueAt(row, "mode-permissive-item-id")
                        processingCmdItemId = ds.getValueAt(row, "processing-cmd-item-id")
                        spItemId = ds.getValueAt(row, "write-target-item-id")
                        # For som ereason that I can't figure out, I couldn't use the column name for this one column...
                        windupItemId = ds.getValueAt(row, 12)
                        print "Output Disposability: ", windupItemId
    #                    windupItemId = ds.getValueAt(row, "output-disposability-item-id")
                        createPKSACEController(parentPath, outputName, itemId, modeItemId, permissiveItemId, spItemId, windupItemId, 
                                            serverName, scanClass, permissiveScanClass, outputNames, processingCmdItemId)
                        status = "Created"
                        
                    elif className == "OPC-PKS-ACE-RAMP-CONTROLLER":
                        print "Parsing a OPC-PKS-ACE-RAMP-CONTROLLER record..."
                        modeItemId = ds.getValueAt(row, "mode-item-id")
                        permissiveItemId = ds.getValueAt(row, "mode-permissive-item-id")
                        rampProcessingCmdItemId = ds.getValueAt(row, "ramp-processing-cmd-item-id")
                        rampStateItemId = ds.getValueAt(row, "ramp-state-item-id")
                        rampAttributeItemId = ds.getValueAt(row, "ramp-attr-item-id")
                        rampSetpointItemId = ds.getValueAt(row, "ramp-setpoint-item-id")
                        rampItemId = ds.getValueAt(row, "ramp-item-id")
                        # For some reason that I can't figure out, I couldn't use the column name for this one column...
                        windupItemId = ds.getValueAt(row, 12)
                        print "Output Disposability: ", windupItemId
    #                    windupItemId = ds.getValueAt(row, "output-disposability-item-id")
                        createPKSACERampController(parentPath, outputName, itemId, modeItemId, permissiveItemId, rampItemId, windupItemId, 
                                            serverName, scanClass, permissiveScanClass, outputNames, rampProcessingCmdItemId, rampStateItemId,
                                            rampAttributeItemId, rampSetpointItemId)
                        status = "Created"
                    
                    elif className in ["OPC-TDC-CONTROLLER-PM"]:
                        itemId = ds.getValueAt(row, 7)
                        spItemId = ds.getValueAt(row, 8)
                        opItemId = ds.getValueAt(row, 9)
                        modeItemId = ds.getValueAt(row, 10)
                        windupItemId = ds.getValueAt(row, 11)    # Is this permissive or windup

                        createTDCController(parentPath, outputName, itemId, spItemId, opItemId, modeItemId, windupItemId, 
                                            serverName, scanClass, permissiveScanClass, outputNames)
                        status = "Created"  
                    
                    elif className in ["OPC-TDC-RAMP-VAR"]:
                        itemId = ds.getValueAt(row, 7)
                        spItemId = ds.getValueAt(row, 8)
                        opItemId = ds.getValueAt(row, 9)
                        modeItemId = ds.getValueAt(row, 10)
                        outputDisposabilityItemId = ds.getValueAt(row, 11)
                        sptvItemId = ds.getValueAt(row, 12)
                        sptvSetpointItemId = ds.getValueAt(row, 13) # This is always the same as the spItem Id
                        rampStateItemId = ds.getValueAt(row, 14)
                        rampTimeItemId = ds.getValueAt(row, 15)
                        rampTimeValue  = ds.getValueAt(row, 16)
                        
                        lowClampItemId = ""
                        highClampItemId = ""
                        windupItemId = ""

                        createTDCRampController(parentPath, outputName, itemId, spItemId, opItemId, modeItemId, outputDisposabilityItemId,
                                            sptvItemId, rampStateItemId, rampTimeItemId, rampTimeValue, 
                                            lowClampItemId, highClampItemId, windupItemId,
                                            serverName, scanClass, permissiveScanClass, outputNames)
                        
                    elif className in ["OPC-CONTROLLER-TDC-RAMP-OUTPUT"]:
                        sptvItemId = ds.getValueAt(row, 7)
                        spItemId = ds.getValueAt(row, 8)
                        rampStateItemId = ds.getValueAt(row, 9)
                        rampTimeItemId = ds.getValueAt(row, 10)
                        rampTimeValue  = ds.getValueAt(row, 11)
                        modeItemId = ds.getValueAt(row, 12)
                        lowClampItemId = ds.getValueAt(row, 13)
                        highClampItemId = ds.getValueAt(row, 14)
                        windupItemId = ds.getValueAt(row, 15)
                        
                        outputDisposabilityItemId = ""
                        opItemId = ""

                        createTDCRampController(parentPath, outputName, itemId, spItemId, opItemId, modeItemId, outputDisposabilityItemId,
                                            sptvItemId, rampStateItemId, rampTimeItemId, rampTimeValue, 
                                            lowClampItemId, highClampItemId, windupItemId,
                                            serverName, scanClass, permissiveScanClass, outputNames)

                        status = "Created"  
                        
                    else:
                        print "Undefined class: ", className
                        status = "Error"

        if status != "":
            ds=system.dataset.setValue(ds, row, "status", status)
    table.data=ds

def filterName(tagName):
    tagName = string.replace(tagName, ".", "-")
    tagName = string.replace(tagName, "_", "-")
    tagName = string.replace(tagName, " ", "")
    return tagName

def createParameter(parentPath, tagName, scanClass, dataType, initialValue):
    print "Creating a memory tag named: %s, Path: %s, Scan Class: %s" % (tagName, parentPath, scanClass)
    system.tag.addTag(parentPath=parentPath, name=tagName, tagType="MEMORY", dataType=dataType)
    tagPath = parentPath + "/" + tagName
    print "Writing %s to %s" % (str(initialValue), tagPath) 
    system.tag.write(tagPath, float(initialValue))

def createOutput(parentPath, outputName, itemId, serverName, scanClass, names, dataType):
    UDTType='Basic IO/OPC Output'

    print "Creating a %s, Name: %s, Path: %s, Item Id: %s, Scan Class: %s, Server: %s" % (UDTType, outputName, parentPath, itemId, scanClass, serverName)
    system.tag.addTag(parentPath=parentPath, name=outputName, tagType="UDT_INST", 
            attributes={"UDTParentType":UDTType}, 
            parameters={"itemId":itemId, "serverName":serverName, "scanClassName":scanClass, "alternateNames": names})
    
    if string.upper(dataType) == "STRING":
        system.tag.editTag(tagPath=parentPath + "/" + outputName,
                           overrides={"value":{"DataType":"String"}, "writeValue": {"DataType":"String"}})
    elif string.upper(dataType) == "INTEGER":
        system.tag.editTag(tagPath=parentPath + "/" + outputName,
                           overrides={"value":{"DataType":"Int8"}, "writeValue": {"DataType":"Int8"}})

def createBadFlag(parentPath, outputName, itemId, serverName, scanClass, names, dataType):
    UDTType='Basic IO/OPC Tag Bad Flag'

    print "Creating a %s, Name: %s, Path: %s, Item Id: %s, Scan Class: %s, Server: %s" % (UDTType, outputName, parentPath, itemId, scanClass, serverName)
    system.tag.addTag(parentPath=parentPath, name=outputName, tagType="UDT_INST", 
            attributes={"UDTParentType":UDTType}, 
            parameters={"itemId":itemId, "serverName":serverName, "scanClassName":scanClass, "alternateNames": names})
    
    if string.upper(dataType) == "STRING":
        system.tag.editTag(tagPath=parentPath + "/" + outputName,
                           overrides={"value":{"DataType":"String"}, "writeValue": {"DataType":"String"}})
    elif string.upper(dataType) == "INTEGER":
        system.tag.editTag(tagPath=parentPath + "/" + outputName,
                           overrides={"value":{"DataType":"Int8"}, "writeValue": {"DataType":"Int8"}})

def createConditionalOutut(parentPath, outputName, itemId, permissiveItemId, serverName, scanClass, names, dataType, permissiveDataType):
    UDTType='Basic IO/OPC Conditional Output'

    print "Creating a %s, Name: %s, Path: %s, Item Id: %s, Scan Class: %s, Server: %s" % (UDTType, outputName, parentPath, itemId, scanClass, serverName)
    system.tag.addTag(parentPath=parentPath, name=outputName, tagType="UDT_INST", 
            attributes={"UDTParentType":UDTType}, 
            parameters={"itemId":itemId, "serverName":serverName, "scanClassName":scanClass, "alternateNames": names,
                        "permissiveItemId": permissiveItemId})
    
    # The default type for the value is Float
    if string.upper(dataType) == "STRING":
        system.tag.editTag(tagPath=parentPath + "/" + outputName,
                           overrides={"value":{"DataType":"String"}, "writeValue": {"DataType":"String"}})

    # The default type for the permissive is string
    if string.upper(dataType) == "FLOAT":
        system.tag.editTag(tagPath=parentPath + "/" + outputName,
                           overrides={"permissive":{"DataType":"Float8"}, 
                                      "permissiveValue": {"DataType":"Float8"},
                                      "permissiveAsFound": {"DataType":"Float8"}})


def createPKSController(parentPath, outputName, itemId, modeItemId, permissiveItemId, spItemId, windupItemId, 
                        serverName, scanClass, permissiveScanClass, names):
    UDTType='Controllers/PKS Controller'

    print "Creating a %s, Name: %s, Path: %s, SP Item Id: %s, Scan Class: %s, Server: %s" % (UDTType, outputName, parentPath, spItemId, scanClass, serverName)
    # Because this generic controller definition is being used by the Diagnostic Toolkit it does not use the PV and OP attributes.  
    # There are OPC tags and just to make sure we don't wreak havoc with the OPC server, these should be disabled
    system.tag.addTag(parentPath=parentPath, name=outputName, tagType="UDT_INST", 
                        attributes={"UDTParentType":UDTType}, 
                        parameters={"itemId":itemId, "serverName":serverName, "scanClassName":scanClass, "scanClassNameForPermissives":permissiveScanClass, "spItemId":spItemId,
                                "modeItemId":modeItemId, "permissiveItemId":permissiveItemId,
                                "windupItemId":windupItemId,
                                "alternateNames": names},
                        overrides={"op": {"Enabled":"false"}})

#
def createTDCController(parentPath, outputName, itemId, spItemId, opItemId, modeItemId, windupItemId, 
                        serverName, scanClass, permissiveScanClass, names):
    UDTType='Controllers/TDC Controller'

    print "Creating a %s, Name: %s, Path: %s, SP Item Id: %s, Scan Class: %s, Server: %s" % (UDTType, outputName, parentPath, spItemId, scanClass, serverName)
    system.tag.addTag(parentPath=parentPath, name=outputName, tagType="UDT_INST", 
                        attributes={"UDTParentType":UDTType}, 
                        parameters={"itemId":itemId, "serverName":serverName, "scanClassName":scanClass, "scanClassNameForPermissives":permissiveScanClass, "spItemId":spItemId,
                                "opItemId":opItemId, "modeItemId":modeItemId, "windupItemId":windupItemId, "alternateNames": names})


def createPKSACEController(parentPath, outputName, itemId, modeItemId, permissiveItemId, spItemId, windupItemId, 
                        serverName, scanClass, permissiveScanClass, names, processingCmdItemId):
    UDTType='Controllers/PKS ACE Controller'

    print "Creating a %s, Name: %s, Path: %s, SP Item Id: %s, Scan Class: %s, Server: %s" % (UDTType, outputName, parentPath, spItemId, scanClass, serverName)
    # Because this generic controller definition is being used by the Diagnostic Toolkit it does not use the PV and OP attributes.  
    # There are OPC tags and just to make sure we don't wreak havoc with the OPC server, these should be disabled
    system.tag.addTag(parentPath=parentPath, name=outputName, tagType="UDT_INST", 
                        attributes={"UDTParentType":UDTType}, 
                        parameters={"itemId":itemId, "serverName":serverName, "scanClassName":scanClass, "scanClassNameForPermissives": permissiveScanClass,
                                "spItemId":spItemId, "modeItemId":modeItemId, "permissiveItemId":permissiveItemId,
                                "windupItemId":windupItemId, "processingCommandItemId": processingCmdItemId,
                                "alternateNames": names},
                        overrides={"op": {"Enabled":"false"}})


def createPKSACERampController(parentPath, outputName, itemId, modeItemId, permissiveItemId, spItemId, windupItemId, serverName,
            scanClass, permissiveScanClass, names, processingCmdItemId, rampStateItemId, rampAttributeItemId, rampSetpointItemId):
    UDTType='Ramp Controllers/PKS ACE Ramp Controller'

    print "Creating a %s, Name: %s, Path: %s, SP Item Id: %s, Scan Class: %s, Server: %s" % (UDTType, outputName, parentPath, spItemId, scanClass, serverName)
    # Because this generic controller definition is being used by the Diagnostic Toolkit it does not use the PV and OP attributes.  
    # There are OPC tags and just to make sure we don't wreak havoc with the OPC server, these should be disabled
    system.tag.addTag(parentPath=parentPath, name=outputName, tagType="UDT_INST", 
                        attributes={"UDTParentType":UDTType}, 
                        parameters={"itemId":itemId, "serverName":serverName, "scanClassName":scanClass, "scanClassNameForPermissives": permissiveScanClass,
                                "spItemId":spItemId, "modeItemId":modeItemId, "permissiveItemId":permissiveItemId,
                                "windupItemId":windupItemId, "processingCommandItemId": processingCmdItemId, "rampStateItemId": rampStateItemId,
                                "rampAttributeItemId": rampAttributeItemId, "targetValueItemId": rampSetpointItemId, "alternateNames": names},
                        overrides={"op": {"Enabled":"false"}})

def createTDCRampController(parentPath, outputName, itemId, spItemId, opItemId, modeItemId, outputDisposabilityItemId, setpointTargetValueItemId, rampStateItemId, rampTimeItemId, 
                            rampTimeValue, lowClampItemId, highClampItemId, windupItemId, serverName, scanClass, permissiveScanClass, names):
    
    UDTType='Ramp Controllers/TDC Ramp Controller'

    print "Creating a %s, Name: %s, Path: %s, SP Item Id: %s, Scan Class: %s, Server: %s" % (UDTType, outputName, parentPath, spItemId, scanClass, serverName)
    # Because this generic controller definition is being used by the Diagnostic Toolkit it does not use the PV and OP attributes.  
    # There are OPC tags and just to make sure we don't wreak havoc with the OPC server, these should be disabled
    system.tag.addTag(parentPath=parentPath, name=outputName, tagType="UDT_INST", 
                        attributes={"UDTParentType":UDTType}, 
                        parameters={"itemId":itemId, "serverName":serverName, "scanClassName":scanClass, "scanClassNameForPermissives": permissiveScanClass, "opItemId":opItemId, 
                                "spItemId":spItemId, "modeItemId":modeItemId, "outputDisposabilityItemId": outputDisposabilityItemId, "rampStateItemId": rampStateItemId,
                                "rampTimeItemId": rampTimeItemId, "setpointTargetValueItemId": setpointTargetValueItemId, 
                                "lowClampItemId": lowClampItemId, "highClampItemId": highClampItemId, "windupItemId": windupItemId, "alternateNames": names} )
    
    tagPath =  parentPath + "/" + outputName + "/sp/rampTimeValue"
    print "Writing %s to %s" % (str(rampTimeValue), tagPath) 
    system.tag.write(tagPath, float(rampTimeValue))