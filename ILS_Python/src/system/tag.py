'''
Created on Jul 9, 2014

@author: chuckc
'''


def browse(path, aFilter):
    results = []
    return results

def browseHistoricalTags(path, nameFilters, maxSize, continuationPoint):
    results = []
    return results

def configure(basePath, tags, collisionPolicy):
    return []

def copy(tags, destination, collisionPolicy):
    return

def deleteAnnotations(paths, storageIds):
    return []

def deleteTags(tagPaths):
    return []

def exists(tagPath):
    return True

def exportTags(filepath, tagPaths, recursive, exportType):
    return

def getConfiguration(basePath, recursive):
    return ""

def importTags(filePath, basePath, collisionPolicy):
    return

def isOverlaysEnabled():
    isEnabled = True
    return isEnabled

def move(tags, destination, collisionPolicy):
    return ""

def queryAnnotations(paths, startTime, endTime, types):
    return

def queryTagCalculations(paths, calculations, startDate, endDate, rangeHours, rangeMinutes, aliases, includeBoundingValues, validatesSCExec, noInterpolation, ignoreBadQuality):
    ds=1
    return ds

def queryTagDensity(paths, startDate, endDate):
    ds=1
    return ds

def queryTagHistory(paths, startDate, endDate, returnSize, aggregationMode, returnFormat, columnNames, intervalHours, intervalMinutes, rangeHours, rangeMinutes, aggregationModes, includeBoundingValues, validateSCExec, noInterpolation, ignoreBadQuality, timeout, intervalSeconds, rangeSeconds):
    ds=1
    return ds

def readAsync(tagPaths, callback):
    return 0.0

def readBlocking(tagPaths, timeout):
    return []

def rename(tag, newName, collisionPolicy):
    qualityCode = True
    return qualityCode

def requestGroupExecution(tagPath):
    return []

def setOverlaysEnabled(enabled):
    pass

def storeAnnotations(paths, startTimes, endTimes, types, data, storageIds, deleted):
    return []

def storeTagHistory(historyprovider, tagprovider, paths, values, qualities, timestamps):
    pass

def writeAsync(tagPaths, values, callback):
    pass

def writeBlocking(tagPaths, values, timeout):
    return []
