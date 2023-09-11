'''
Created on Jul 9, 2014

@author: chuckc
'''
def addTag(parentPath, name, tagType, dataType, attributes, parameters, overrides):
    return []

def browseConfiguration(path, udtParentType):
    return []

def browseTags(path, udtParentType):
    return []

def browseTagsSimple(path, sort):
    return []

def editTag(tagPath, attributes, parameters):
    return True

def exists(tagPath):
    return True

def getAttribute(tagPath, attr):
    return ""

def getConfiguration(fullTagPath, recursive):
    return ""

def getTagValue(tagPath):
    return ""

def queryTagCalculations():
    ds=1
    return ds

def queryTagHistory():
    ds=1
    return ds

def read(tagPath):
    return 0.0

def readBlocking( tagPaths ):
    return 0.0

def readAll(paths):
    return []

def removeTag(path):
    pass

def removeTags(paths):
    return []

def write(tagPath,command):
    pass

def writeBlocking(tagPath, value, timeout=45000):
    pass

def writeSynchronous(tagPath, value):
    pass

def writeAllSynchronous(tagPath, value):
    pass

def writeAll(tags, vals):
    return True

def writeToTag(tagpath, vals):
    return True
