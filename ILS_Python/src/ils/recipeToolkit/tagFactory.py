'''
Created on Sep 10, 2014

@author: Pete
'''
import system

def createConfigurationTags(ds):
    print "Creating configuration tags..."
    pds = system.dataset.toPyDataSet(ds)

    for row in pds:
        path = row["Path"]
        name = row["Name"]
        dataType = row["Data Type"]
        val = row["Value"]
        
        fullName = path + name
                
        # Check if the tag exists
        print "Checking: " + fullName
        if not(system.tag.exists(fullName)):
            print "  ...creating configuration tag " + fullName 
            system.tag.addTag(parentPath = path, name = name, tagType = "DB", dataType = dataType)
    
            if dataType == "Int8":
                val = int(val)
            elif dataType == "Float4":
                val = float(val)
            elif dataType == "Boolean":
                from ils.common.cast import toBool
                val = toBool(val)
            
#            print "  ...initializing ", fullName, " to ", val
            system.tag.writeToTag(fullName, val)


# Create a recipe data tag
def createUDT(UDTType, provider, path, dataType, tagName, serverName, scanClass, itemId, conditionalDataType):
    import string

    #----------------------------------------------------
    # TODO - The permissive may actually need a suffic of .MODEATTR /enum
    def morphItemIdPermissive(itemId):
        permissiveItemId = itemId[:itemId.rfind('.')] + '.MODEATTR'
        return permissiveItemId
    #-----------------------------------------------------
    UDTType = 'Basic IO/' + UDTType
    parentPath = '[' + provider + ']' + path    
    tagPath = parentPath + "/" + tagName
    tagExists = system.tag.exists(tagPath)
    
    if tagExists:
#        print tagName, " already exists!"
        pass
    else:
        print "Creating a %s\n  Name: %s\n  Path: %s\n  Item Id: %s\n  Data Type: %s\n  Scan Class: %s\n  Server: %s\n  Conditional Data Type: %s" % (UDTType, tagName, tagPath, itemId, dataType, scanClass, serverName, conditionalDataType) 
        if UDTType == 'Basic IO/OPC Output':
            system.tag.addTag(parentPath=parentPath, name=tagName, tagType="UDT_INST", 
                attributes={"UDTParentType":UDTType}, 
                parameters={"itemId":itemId, "serverName":serverName, "scanClassName":scanClass})
        else:
            permissiveItemId = morphItemIdPermissive(itemId)
            system.tag.addTag(parentPath=parentPath, name=tagName, tagType="UDT_INST", 
                attributes={"UDTParentType":UDTType}, 
                parameters={"itemId":itemId, "serverName":serverName, "scanClassName":scanClass, "permissiveItemId":permissiveItemId})

            # Override the data type of the permissive - the default is integer
            if string.lower(conditionalDataType) == "string":
                print "Overriding the permissive tag datatype..."
                system.tag.editTag(tagPath=tagPath,
                    overrides={"permissive":{"DataType":"String"}})

    # Now do any additional overrides that may be necessary - Remember the UDTs are floats, so if we are making int or string tags, I'll need to override the UDT
    if string.lower(dataType) == "string":
        print "Overriding the tag datatype..."
        system.tag.editTag(tagPath=tagPath,
            overrides={"tag":{"DataType":"String"}})


# Create a recipe detail UDT
def createRecipeDetailUDT(UDTType, provider, path, tagName):
    UDTType = 'Recipe Data/' + UDTType
    parentPath = '[' + provider + ']' + path                
    tagPath = parentPath + "/" + tagName
    tagExists = system.tag.exists(tagPath)
            
    if tagExists:
#        print tagName, " already exists!"
        pass
    else:
        print "Creating a %s\n  Name: %s\n  Path: %s\n" % (UDTType, tagName, tagPath) 
        system.tag.addTag(parentPath=parentPath, name=tagName, tagType="UDT_INST", 
            attributes={"UDTParentType":UDTType} )