'''
Created on Sep 10, 2014

@author: Pete
'''
import system, string
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
from system.ils.blt.diagram import getProductionTagProvider
log = LogUtil.getLogger("com.ils.recipeToolkit")


def createUDT(UDTType, provider, path, dataType, tagName, serverName, scanClass, itemId, modeAttribute, modeAttributeValue, conditionalDataType):
    '''
    Create a recipe data tag
    '''
    #----------------------------------------------------
    def morphItemIdPermissive(itemId, modeAttribute, modeAttributeValue):
        print "Determining the permissive item id where the attribute is <%s> and the mode value is <%s> and the base item id is: <%s>" % (modeAttribute, modeAttributeValue, itemId)
        permissiveItemId = itemId[:itemId.rfind('.')] + '.' + modeAttribute
        
        if type(modeAttributeValue) in [str, unicode] and string.upper(modeAttribute).find("ENUM") < 0:
            print "Adding /enum because we detected a string permissive value!"
            permissiveItemId = permissiveItemId + " /enum"
    
        print "Returning permissive item id: ", permissiveItemId
        return permissiveItemId
    #-----------------------------------------------------
    UDTType = 'Basic IO/' + UDTType
    parentPath = '[' + provider + ']' + path
    
    productionProvider = getProductionTagProvider()
    tagPath = parentPath + "/" + tagName
    tagExists = system.tag.exists(tagPath)
    
    if tagExists:
        log.tracef("%s already exists!", tagPath)
        pass
    elif provider != productionProvider:
        log.infof("Skipping the creation of %s, a %s, because we are in Isolation", tagName, UDTType)
    else:
        log.info("Creating a %s, Name: %s, Path: %s, Item Id: %s, Data Type: %s, Scan Class: %s, Server: %s, Conditional Data Type: %s" % (UDTType, tagName, tagPath, itemId, dataType, scanClass, serverName, conditionalDataType))
        if UDTType == 'Basic IO/OPC Output':
            system.tag.addTag(parentPath=parentPath, name=tagName, tagType="UDT_INST", 
                attributes={"UDTParentType":UDTType}, 
                parameters={"itemId":itemId, "serverName":serverName, "scanClassName":scanClass})
            
            # Now do any additional overrides that may be necessary - Remember the UDTs are floats, so if we are making int or string tags, I'll need to override the UDT
            if string.lower(dataType) == "string":
                log.info("Overriding the value datatype...")
                system.tag.editTag(tagPath=tagPath, overrides={"value":{"DataType":"String"}})
        else:
            permissiveItemId = morphItemIdPermissive(itemId, modeAttribute, modeAttributeValue)
            system.tag.addTag(parentPath=parentPath, name=tagName, tagType="UDT_INST", 
                attributes={"UDTParentType":UDTType}, 
                parameters={"itemId":itemId, "serverName":serverName, "scanClassName":scanClass, "permissiveItemId":permissiveItemId})

            # Override the data type of the permissive - the default is integer
            if string.lower(conditionalDataType) == "string":
                log.info("Overriding the permissive tag datatype...")
                system.tag.editTag(tagPath=tagPath, overrides={"permissive":{"DataType":"String"}})

            # Now do any additional overrides that may be necessary - Remember the UDTs are floats, so if we are making int or string tags, I'll need to override the UDT
            if string.lower(dataType) == "string":
                log.info("Overriding the value datatype...")
                system.tag.editTag(tagPath=tagPath, overrides={"value":{"DataType":"String"}})


# Create a recipe detail UDT
def createRecipeDetailUDT(UDTType, provider, path, tagName):
    UDTType = 'Recipe Data/' + UDTType
    parentPath = '[' + provider + ']' + path
    
    productionProvider = getProductionTagProvider()
    tagPath = parentPath + "/" + tagName
    tagExists = system.tag.exists(tagPath)
            
    if tagExists:
#        print tagName, " already exists!"
        pass
    elif provider != productionProvider:
        log.infof("Skipping the creation of %s, a %s, because we are in Isolation", tagName, UDTType)
    else:
        log.info("Creating a %s, Name: %s, Path: %s" % (UDTType, tagName, tagPath)) 
        system.tag.addTag(parentPath=parentPath, name=tagName, tagType="UDT_INST", 
            attributes={"UDTParentType":UDTType} )