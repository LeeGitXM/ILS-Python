'''
Created on Sep 10, 2014

@author: Pete
'''
import system

import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.recipeToolkit")


# Create a recipe data tag
def createUDT(UDTType, provider, path, dataType, tagName, serverName, scanClass, itemId, conditionalDataType):
    import string

    #----------------------------------------------------
    # The permissive may actually need a suffix of .MODEATTR /enum
    def morphItemIdPermissive(itemId):
        # I have hard coded MODEATTR here even though it is a field in the recipe database, we may need to
        # get this out of the recipe rather than hard coding it.
        permissiveItemId = itemId[:itemId.rfind('.')] + '.MODEATTR /enum'
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
        log.info("Creating a %s, Name: %s, Path: %s, Item Id: %s, Data Type: %s, Scan Class: %s, Server: %s, Conditional Data Type: %s" % (UDTType, tagName, tagPath, itemId, dataType, scanClass, serverName, conditionalDataType))
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
                log.info("Overriding the permissive tag datatype...")
                system.tag.editTag(tagPath=tagPath, overrides={"permissive":{"DataType":"String"}})

    # Now do any additional overrides that may be necessary - Remember the UDTs are floats, so if we are making int or string tags, I'll need to override the UDT
    if string.lower(dataType) == "string":
        log.info("Overriding the tag datatype...")
        system.tag.editTag(tagPath=tagPath, overrides={"tag":{"DataType":"String"}})


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
        log.info("Creating a %s, Name: %s, Path: %s" % (UDTType, tagName, tagPath)) 
        system.tag.addTag(parentPath=parentPath, name=tagName, tagType="UDT_INST", 
            attributes={"UDTParentType":UDTType} )