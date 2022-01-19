'''
Created on Sep 10, 2014

@author: Pete
'''
import system, string
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
from ils.common.config import getProductionTagProvider
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
        if string.lower(dataType) == "string":
            dataType='String'
    
        if UDTType == 'Basic IO/OPC Output':          
            config = {
                'tagType': 'UdtInstance', 
                'name': tagName, 
                'typeId': UDTType, 
                'parameters': 
                    {
                        'scanClassName': scanClass, 
                        'serverName': serverName, 
                        'pythonClass': 'OPCOutput', 
                        'itemId': itemId,
                    },
                'tags': 
                [
                    {
                        'dataType': dataType, 
                        'name': 'value'
                    }
                ]
            
            }
            system.tag.configure(basePath=parentPath, tags=[config])

        elif UDTType == 'Basic IO/OPC ConfitionalOutput':
            permissiveItemId = morphItemIdPermissive(itemId, modeAttribute, modeAttributeValue)
            config = {
                'name': tagName,
                'tagType': 'UdtInstance', 
                'typeId': 'Basic IO/OPC Conditional Output',     
            
                'tags': 
                    [
                        {
                            'dataType': dataType, 
                            'name': 'value', 
                        },
                    ], 
                    
                'parameters': 
                    {
                        'scanClassName': scanClass, 
                        'serverName': serverName, 
                        'pythonClass': 'OPCConditionalOutput', 
                        'itemId': itemId, 
                        'permissiveItemId': permissiveItemId
                    }
                }
    
            system.tag.configure(basePath=parentPath, tags=[config])
            
        else:
            log.errorf("Unexpected UDT Type: %s", UDTType)


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
        print "TODO TODO TODO NEED TO CONVERT THIS "
#        system.tag.addTag(parentPath=parentPath, name=tagName, tagType="UDT_INST", 
#            attributes={"UDTParentType":UDTType} )