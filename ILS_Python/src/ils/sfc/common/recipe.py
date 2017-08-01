'''
Created on Jul 13, 2015

Basic operations on tags used to store recipe data. The method names are
self-explanatory

@author: rforbes
'''
import system.tag
from system.ils.sfc.common.Constants import RECIPE_DATA_FOLDER
from com.inductiveautomation.ignition.common.util import LogUtil
log = LogUtil.getLogger("ils.sfc.common")

def getBasicTagPathCRAP(chartProperties, stepProperties, valuePath, location):
    '''Get the "basic" path to the recipe data tag. This does not include the provider or top folder'''
    from system.ils.sfc import getRecipeDataTagPath
    from system.ils.sfc.common.Constants import NAMED
    location = location.lower()
    if location == NAMED:
        tagPath = valuePath
    else:
        # Confusing!! this is not the getRecipeDataTagPath that is in this module!
        stepPath = getRecipeDataTagPath(chartProperties, stepProperties, location)
        tagPath = stepPath + "/" + valuePath
    return tagPath

def getRecipeDataTagPrefixCRAP(provider):
    '''Return the root folder for recipe data'''
    if provider == None:
        provider = ""
    return "[" + provider + "]" + RECIPE_DATA_FOLDER + "/"

def getRecipeDataTagPathCRAP(provider, path):
    '''Given a recipe data "key", return the full absolute tag path'''
    # treat dot separators like slash:
    if path.find('.') != -1:
        path = path.replace(".", "/")
    return getRecipeDataTagPrefix(provider) + path 

def createGroupPropertyTagCRAP(provider, folder, rdName):    
    '''For creating simple string members of Groups'''
    fullFolder = getRecipeDataTagPath(provider, folder)
    log.infof("createGroupPropertyTag: %s in %s", rdName, fullFolder)
    system.tag.addTag(parentPath=fullFolder, name=rdName, tagType = 'MEMORY', dataType='String')

def createRecipeDataTagCRAP(provider, folder, rdName, rdType, valueType):    
    fullFolder = getRecipeDataTagPath(provider, folder)
    log.infof("createRecipeDataTag: %s(%s:%s) in %s", rdName,rdType, valueType,fullFolder)
    typePath = RECIPE_DATA_FOLDER + "/" + rdType
    if rdType == 'Group':
        rdTagType = 'Folder'
        system.tag.addTag(parentPath=fullFolder, name=rdName, tagType=rdTagType)
    else:
        rdTagType='UDT_INST'
        system.tag.addTag(parentPath=fullFolder, name=rdName, tagType=rdTagType, attributes={"UDTParentType":typePath})
        if (rdType == 'Value' or rdType == 'Output' or rdType == 'Input' ) and valueType != None:
            changeType(fullFolder, rdName, valueType)
        elif (rdType == 'Array' ) and valueType != None:
            changeArrayType(fullFolder, rdName, valueType)


def changeTypeCRAP(folderPath, tagName, valueType):
    '''For the value, input, and output tags, change the tag type to
       agree with the value type'''
    from system.ils.sfc.common.Constants import INT, FLOAT, BOOLEAN, STRING, DATE_TIME

    if valueType == INT:
        newType = 'Int8'
    elif valueType == FLOAT:
        newType = 'Float8'
    elif valueType == BOOLEAN:
        newType = 'Boolean'
    elif valueType == STRING:
        newType = 'String' 
    elif valueType == DATE_TIME:
        newType = 'DateTime' 
    else:   
        newType = 'String' 
    valuePath = folderPath + "/" + tagName
    system.tag.editTag(valuePath, overrides={"value": {"DataType":newType}})
    
#
def changeArrayTypeCRAP(folderPath, tagName, valueType):
    '''For the array tags, change the tag array type to
       agree with the value type'''
    from system.ils.sfc.common.Constants import INT, FLOAT, BOOLEAN, STRING, DATE_TIME

    if valueType == INT:
        newType = 'Int8Array'
    elif valueType == FLOAT:
        newType = 'Float8Array'
    elif valueType == BOOLEAN:
        newType = 'BooleanArray'
    elif valueType == STRING:
        newType = 'StringArray' 
    elif valueType == DATE_TIME:
        newType = 'DateTimeArray' 
    else:   
        newType = 'StringArray' 
    valuePath = folderPath + "/" + tagName
    system.tag.editTag(valuePath, overrides={"value": {"DataType":newType}})
    
# TODO: the methods below are called form Java. Should consolidate with s88 methods
# in api            
def deleteRecipeDataTagCRAP(provider, tagPath):    
    fullPath = getRecipeDataTagPath(provider, tagPath)
    #print 'delete', fullPath
    system.tag.removeTag(fullPath)

def getRecipeDataCRAP(provider, path): 
    raise Exception('Obsolete Python API %s.getRecipeData()' % (__name__))
    fullPath = getRecipeDataTagPath(provider, path)
    qv = system.tag.read(fullPath)
    # print 'get', fullPath, qv.value, 'quality', qv.quality
    return qv.value
    
def setRecipeDataCRAP(provider, path, value, synchronous):
    fullPath = getRecipeDataTagPath(provider, path)
    log.infof("setRecipeData: %s = %s",fullPath,str(value))
    if synchronous:
        system.tag.writeSynchronous(fullPath, value)
    else:
        system.tag.write(fullPath, value)
        
def recipeDataTagExistsCRAP(provider, path):
    fullPath = getRecipeDataTagPath(provider, path)
    return system.tag.exists(fullPath)

def cleanupRecipeDataCRAP(provider, chartPath, sfcStepPaths):
    '''Remove any recipe data for the given chart that does not 
    belong to one of the supplied step names. This handles
    cleaning up recipe data for deleted steps and charts. '''
    from system.util import getLogger
    chartRdFolder = getRecipeDataTagPath(provider, chartPath)
    logger = getLogger(chartPath)
    tagInfos = system.tag.browseTags(chartRdFolder)
    logger.warnf('checking for orphaned recipe data tag in %s', chartRdFolder)
    for tagInfo in tagInfos:
        tagStepPath = tagInfo.name
        if not tagStepPath in sfcStepPaths:
            logger.warnf('removing orphaned recipe data tags for step %s', tagStepPath)
            system.tag.removeTag(tagInfo.fullPath)

   