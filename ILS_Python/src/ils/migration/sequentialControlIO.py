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
            outputNames = ds.getValueAt(row, "names")
            gsiInterface = ds.getValueAt(row, "gsi-interface")
            initialValue = ds.getValueAt(row, "initial-value")
            itemId = ds.getValueAt(row, "itemId")
#            conditionalItemId = ds.getValueAt(row, "Conditional ItemId")
            
            print "---------------------------"
            print "Folder: ", folder
            print "Class: ", className
            print "Name: ", outputName
            print "Names: ", outputNames
            print "GSI Interface: ", gsiInterface
            print "Item Id: ", itemId
            
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
                if className == "OPC-TEXT-OUTPUT":
                    createOutput(parentPath, outputName, itemId, serverName, scanClass, outputNames, "String")
                    status = "Created"
                elif className == "FLOAT-PARAMETER":
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
                elif className in ["OPC-PKS-CONTROLLER", "OPC-PKS-DIGITAL-CONTROLLER"]:
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
                else:
                    print "Undefined class: ", className
                    status = "Error"

        if status != "":
            ds=system.dataset.setValue(ds, row, "status", status)
    table.data=ds

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

