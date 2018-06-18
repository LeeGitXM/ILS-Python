'''
Created on Jun 14, 2018

@author: phass
'''

'''
Created on Jul 21, 2015

@author: Pete
'''
import system, string
from ils.migration.common import lookupOPCServerAndScanClass
  
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
            gsiInterface = ds.getValueAt(row, "gsi-interface")
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
                    createOpcTag(parentPath, outputName, itemId, serverName, scanClass, "String")
                    status = "Created"
                elif className == "OPC-FLOAT-OUTPUT":
                    createOpcTag(parentPath, outputName, itemId, serverName, scanClass, "Float8")
                    status = "Created"
                elif className == "OPC-INT-OUTPUT":
                    createOpcTag(parentPath, outputName, itemId, serverName, scanClass, "Int8")
                    status = "Created"
                elif className == "OPC-FLOAT-BAD-FLAG":
                    createOpcTag(parentPath, outputName, itemId, serverName, scanClass, "Float8")
                    status = "Created"
                elif className == "OPC-INT-BAD-FLAG":
                    createOpcTag(parentPath, outputName, itemId, serverName, scanClass, "Int8")
                    status = "Created"
                elif className == "OPC-TEXT-BAD-FLAG":
                    createOpcTag(parentPath, outputName, itemId, serverName, scanClass, "String")
                    status = "Created"
                elif className == "BATCH-SEQUENCE-PAR":
                    createOpcTag(parentPath, outputName, itemId, serverName, scanClass, "Float8")
                    status = "Created"            
                else:
                    print "Undefined class: ", className
                    status = "Error"

        if status != "":
            ds=system.dataset.setValue(ds, row, "status", status)
    table.data=ds

def filterName(tagName):
    tagName = string.replace(tagName, ".", "_")
    tagName = string.replace(tagName, "-", "_")
    tagName = string.replace(tagName, " ", "")
    return tagName

def createOpcTag(parentPath, tagName, itemId, serverName, scanClass, dataType):
    print "Creating an OPC tag named: %s, Path: %s, Scan Class: %s" % (tagName, parentPath, scanClass)
    
    system.tag.addTag(parentPath=parentPath, name=tagName, tagType="OPC", dataType=dataType,
            attributes={"OPCServer":serverName, "OPCItemPath":itemId, "ScanClass":scanClass})
