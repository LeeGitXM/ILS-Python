'''
Created on Nov 3, 2014

@author: rforbes
'''
import system

from ils.sfc.common.constants import PARENT, INSTANCE_ID, RECIPE_DATA, PROJECT

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

def sendMessageToClient(chartProperties, handler, payload):
    # TODO: check returned list of recipients
    # TODO: restrict to a particular client session
    from ils.sfc.common.constants import MESSAGE_ID, TEST_RESPONSE, MESSAGE
    project = getProject(chartProperties)
    testResponse = getTestResponse(chartProperties)
    if testResponse != None:
        payload[TEST_RESPONSE] = testResponse
    messageId = createUniqueId()
    payload[MESSAGE_ID] = messageId
    #print 'sending message to client', project, handler, payload.get(MESSAGE, 'None')
    system.util.sendMessage(project, handler, payload, "C")
    return messageId

def getLogger():
    import logging
    return logging.getLogger('ilssfc')

def boolToBit(bool):
    if bool:
        return 1
    else:
        return 0
    
def getTopLevelProperties(chartProperties):
    while chartProperties.get(PARENT, None) != None:
        chartProperties = chartProperties.get(PARENT)
    return chartProperties

def getChartRunId(chartProperties):
    return str(getTopLevelProperties(chartProperties)[INSTANCE_ID])
    
def getProject(chartProperties):
    return str(getTopLevelProperties(chartProperties)[PROJECT])

def getTestResponse(chartProperties):
    from ils.sfc.common.constants import TEST_RESPONSE
    return getTopLevelProperties(chartProperties).get(TEST_RESPONSE, None)

def getDatabaseName(chartProperties):
    from system.ils.sfc import getDatabaseName
    isolationMode = getIsolationMode(chartProperties)
    return getDatabaseName(isolationMode)

def getTagProvider(chartProperties):
    from system.ils.sfc import getProviderName
    isolationMode = getIsolationMode(chartProperties)
    return getProviderName(isolationMode)

def getIsolationMode(chartProperties):
    from ils.sfc.common.constants import ISOLATION_MODE
    topProperties = getTopLevelProperties(chartProperties)
    return topProperties[ISOLATION_MODE]
   
def getTimeFactor(chartProperties):
    from system.ils.sfc import getTimeFactor
    isolationMode = getIsolationMode(chartProperties)
    return getTimeFactor(isolationMode)

def substituteProvider(chartProperties, tagPath):
    '''alter the given tag path to reflect the isolation mode provider setting'''
    if tagPath.startsWith('[Client]') or tagPath.startsWith('[System]'):
        return tagPath
    else:
        provider = getTagProvider(chartProperties)
        rbIndex = tagPath.indexOf(']')
        if rbIndex >= 0:
            return provider + tagPath[rbIndex+1:len(tagPath)]
        else:
            # no provider was specified?! can't to anything
            return tagPath
    
# this should really be in client.util
def handleUnexpectedClientError(message):
    system.gui.errorBox(message, 'Unexpected Error')

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

    