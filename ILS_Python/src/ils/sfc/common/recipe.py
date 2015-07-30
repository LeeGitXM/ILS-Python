'''
Created on Jul 13, 2015

Basic operations on tags used to store recipe data. The method names are
self-explanatory

@author: rforbes
'''
import system.tag
from system.ils.sfc.common.Constants import RECIPE_DATA_FOLDER

def getRecipeDataTagPrefix(provider):
    '''Return the root folder for recipe data'''
    return "[" + provider + "]" + RECIPE_DATA_FOLDER + "/"

def getRecipeDataTagPath(provider, path):
    '''given a recipe data "key", return the full absolute tag path'''
    # treat dot separators like slash:
    if path.find('.') != -1:
        path = path.replace(".", "/")
    return getRecipeDataTagPrefix(provider) + path

def createRecipeDataTag(provider, folder, rdName, rdType):    
    fullFolder = getRecipeDataTagPath(provider, folder)
    #print 'creating', rdType, rdName, 'in', fullFolder
    typePath = RECIPE_DATA_FOLDER + "/" + rdType
    system.tag.addTag(parentPath=fullFolder, name=rdName, tagType='UDT_INST', attributes={"UDTParentType":typePath})

def deleteRecipeDataTag(provider, tagPath):    
    fullPath = getRecipeDataTagPath(provider, tagPath)
    #print 'delete', fullPath
    system.tag.removeTag(fullPath)
    
def getRecipeData(provider, path): 
    fullPath = getRecipeDataTagPath(provider, path)
    qv = system.tag.read(fullPath)
    #print 'get', fullPath, qv.value, 'quality', qv.quality
    return qv.value

def setRecipeData(provider, path, value, synchronous):
    fullPath = getRecipeDataTagPath(provider, path)
    changeType(fullPath, value)
    #print 'set', fullPath, value
    if synchronous:
        system.tag.writeSynchronous(fullPath, value)
    else:
        system.tag.write(fullPath, value)


def changeType(tagFieldPath, value):
    '''For the value tag only, change the tag type to
    agree with the value type'''
    valueSuffix = '/value'
    if not tagFieldPath.endswith(valueSuffix):
        return
    # strip off the /value
    tagPath = tagFieldPath[0:len(tagFieldPath) - len(valueSuffix)]
    if type(value) == type(''):
        newType = 'String'
    elif type(value) == type(1):
        newType = 'Int8'
    elif type(value) == type(1.):
        newType = 'Float8'
    elif type(value) == type(False):
        newType = 'Boolean'
    else:
        newType = 'String'    
    print 'tagPath', tagPath, 'newType', newType
    system.tag.editTag(tagPath, overrides={"value": {"DataType":newType}})
    
def recipeDataTagExists(provider, path):
    fullPath = getRecipeDataTagPath(provider, path)
    return system.tag.exists(fullPath)