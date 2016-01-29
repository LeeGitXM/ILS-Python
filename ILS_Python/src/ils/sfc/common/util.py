'''
Created on Nov 3, 2014

@author: rforbes
'''
import system

from ils.sfc.common.constants import PARENT, INSTANCE_ID, RECIPE_DATA, PROJECT

def startChart(chartPath, controlPanelId, project, originator, isolationMode):
    from ils.sfc.common.constants import ISOLATION_MODE, CONTROL_PANEL_ID
    initialChartParams = dict()
    initialChartParams[PROJECT] = project
    initialChartParams[ISOLATION_MODE] = isolationMode
    initialChartParams[CONTROL_PANEL_ID] = controlPanelId
    runId = system.sfc.startChart(chartPath, initialChartParams)
    if isolationMode:
        isolationFlag = 1
    else:
        isolationFlag = 0
    updateSql = "Update SfcControlPanel set chartRunId = '%s', originator = '%s', project = '%s', isolationMode = %d where controlPanelId = %d" % (runId, originator, project, isolationFlag, controlPanelId)
    numUpdated = system.db.runUpdateQuery(updateSql)
    if numUpdated == 0:
        system.gui.messageBox("Failed to updated SfcControlPanel with chart start info")

def readFile(filepath):
    '''
    Read the contents of a file into a string
    '''
    import StringIO
    out = StringIO.StringIO()
    fp = open(filepath, 'r')
    line = "dummy"
    while line != "":
        line = fp.readline()
        out.write(line)
    fp.close()
    result = out.getvalue()
    out.close()
    return result   

def boolToBit(bool):
    if bool:
        return 1
    else:
        return 0

def substituteProvider(chartProperties, tagPath):
    from ils.sfc.gateway.api import getProviderName
    '''alter the given tag path to reflect the isolation mode provider setting'''
    if tagPath.startswith('[Client]') or tagPath.startswith('[System]'):
        return tagPath
    else:
        provider = getProviderName(chartProperties)
        rbIndex = tagPath.find(']')
        if rbIndex >= 0:
            return '[' + provider + ']' + tagPath[rbIndex+1:len(tagPath)]
        else:
            return '[' + provider + ']' + tagPath
    
# this should really be in client.util
def handleUnexpectedClientError(msg):
    from ils.sfc.client.windowUtil import openErrorPopup
    openErrorPopup(msg)

def isEmpty(str):
    return str == None or str.strip() == ""

def createUniqueId():
    '''
    create a unique id
    '''
    import uuid
    return str(uuid.uuid4())

def callMethod(methodPath, stringLiteral=""):
    '''given a fully qualified package.method name, call the method and return the result'''
    lastDotIndex = methodPath.rfind(".")
    packageName = methodPath[0:lastDotIndex]
    globalDict = dict()
    localDict = dict()
    exec("import " + packageName + "\nresult = " + methodPath + "(" + stringLiteral + ")\n", globalDict, localDict)
    result = localDict['result']
    return result

def callMethodWithParams(methodPath, keys, values):
    '''given a fully qualified package.method name, call the method and return the result'''
    lastDotIndex = methodPath.rfind(".")
    packageName = methodPath[0:lastDotIndex]
    paramCount = 0
    paramLiterals = ""
    globalDict = dict()
    for i in range(len(keys)):
        key = keys[i]
        value = values[i]
        globalDict[key] = value
        if paramCount > 0:
            paramLiterals = paramLiterals + ", " 
        paramLiterals = paramLiterals + key
        paramCount = paramCount + 1
    localDict = dict()
    execString = "import " + packageName + "\nresult = " + methodPath + "(" + paramLiterals + ")\n"
    exec(execString, globalDict, localDict)
    result = localDict['result']
    return result

def getHoursMinutesSeconds(floatTotalSeconds):
    '''break a floating point seconds value into integer hours, minutes, seconds (round to nearest second)'''
    import math
    intHours = int(math.floor(floatTotalSeconds/3600))
    floatSecondsRemainder = floatTotalSeconds - intHours * 3600
    intMinutes = int(math.floor(floatSecondsRemainder/60))
    floatSecondsRemainder = floatSecondsRemainder - intMinutes * 60
    intSeconds = int(round(floatSecondsRemainder))
    return intHours, intMinutes, intSeconds

def formatTime(epochSecs):
    '''given an epoch time, return a formatted time in the local time zone'''
    import time
    return time.strftime("%d %b %Y %I:%M:%S %p", time.localtime(epochSecs))

def getMinutesSince(epochSecs):
    '''get the elapsed time in minutes since the given epoch time'''
    import time
    return (time.time() - epochSecs) / 60.

def printDataset(dataset):
    for row in range(dataset.rowCount):
        print ''
        for col in range(dataset.columnCount):
            value = dataset.getValueAt(row, col)
            print value

def doNothing():
    '''a minimal function useful for timing tests on java-to-python calls'''
    return 1


def splitPath(path):
    '''split the path at the last slash'''
    slashIndex = path.rfind('/')
    if slashIndex == -1:
        return path, ''
    else:
        prefix = path[0 : slashIndex]
        suffix = path[slashIndex + 1 : len(path)]
        return prefix, suffix
    
def isString(value):
    '''check if the given value is a string'''
    return isinstance(value, str)

def escapeSqlQuotes(string):
    return string.replace("'", "''")