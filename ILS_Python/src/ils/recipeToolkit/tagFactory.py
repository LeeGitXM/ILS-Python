'''
Created on Sep 10, 2014

@author: Pete
'''
import system, string
from ils.common.config import getProductionTagProvider
from ils.log import getLogger
log = getLogger(__name__)


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
    
    '''
    I used to skip creating a UDT is we are in isolation mode.  I think that was before we had a good parallel set of isolation UDTs.
    I think that the UDT that is created is the one defined for that provider.  So an isolation instance will use the isolation UDT.
    PAH - 1/20/2022
    '''
    tagPath = parentPath + "/" + tagName
    tagExists = system.tag.exists(tagPath)
    
    if tagExists:
        log.tracef("%s already exists!", tagPath)
    else:
        log.info("Creating a %s, Name: %s, Path: %s, Item Id: %s, Data Type: %s, Scan Class: %s, Server: %s, Conditional Data Type: %s" % (UDTType, tagName, tagPath, itemId, dataType, scanClass, serverName, conditionalDataType))
        if string.lower(dataType) == "string":
            dataType='String'
        elif string.lower(dataType) == "float":
            dataType='Float4'
    
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

        elif UDTType == 'Basic IO/OPC Conditional Output':
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
    
    '''
    I used to skip creating a UDT is we are in isolation mode.  I think that was before we had a good parallel set of isolation UDTs.
    I think that the UDT that is created is the one defined for that provider.  So an isolation instance will use the isolation UDT.
    PAH - 1/20/2022
    '''
    
    tagPath = parentPath + "/" + tagName
    tagExists = system.tag.exists(tagPath)
            
    if tagExists:
        log.tracef("%s already exists!", tagName)
    else:
        log.info("Creating a %s, Name: %s, Path: %s" % (UDTType, tagName, tagPath)) 
        config = {
            'tagType': 'UdtInstance', 
            'name': tagName, 
            'typeId': UDTType
        }
        system.tag.configure(basePath=parentPath, tags=[config])
            
#        print "TODO TODO TODO NEED TO CONVERT THIS "
#        system.tag.addTag(parentPath=parentPath, name=tagName, tagType="UDT_INST", 
#            attributes={"UDTParentType":UDTType} )