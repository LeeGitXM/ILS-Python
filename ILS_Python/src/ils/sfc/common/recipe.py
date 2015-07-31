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

def createRecipeDataTag(provider, folder, rdName, rdType, valueType):    
    fullFolder = getRecipeDataTagPath(provider, folder)
    #print 'creating', rdType, rdName, 'in', fullFolder
    typePath = RECIPE_DATA_FOLDER + "/" + rdType
    system.tag.addTag(parentPath=fullFolder, name=rdName, tagType='UDT_INST', attributes={"UDTParentType":typePath})
    if rdType == 'Value' and valueType != None:
        changeType(fullFolder, rdName, valueType)
        
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
    #print 'set', fullPath, value
    if synchronous:
        system.tag.writeSynchronous(fullPath, value)
    else:
        system.tag.write(fullPath, value)

def changeType(folderPath, tagName, valueType):
    '''For the value tag only, change the tag type to
    agree with the value type'''
    from system.ils.sfc.common.Constants import INT, FLOAT, BOOLEAN, STRING

    if valueType == INT:
        newType = 'Int8'
    elif valueType == FLOAT:
        newType = 'Float8'
    elif valueType == BOOLEAN:
        newType = 'Boolean'
    elif valueType == STRING:
        newType = 'String' 
    else:   
        newType = 'String' 
    valuePath = folderPath + "/" + tagName
    print 'setting', valuePath, " to ", newType
    system.tag.editTag(valuePath, overrides={"value": {"DataType":newType}})
    
def recipeDataTagExists(provider, path):
    fullPath = getRecipeDataTagPath(provider, path)
    return system.tag.exists(fullPath)