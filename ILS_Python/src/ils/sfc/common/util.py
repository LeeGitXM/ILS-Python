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
    from ils.sfc.common.constants import MESSAGE_ID, TEST_RESPONSE
    project = getProject(chartProperties)
    testResponse = getTestResponse(chartProperties)
    if testResponse != None:
        payload[TEST_RESPONSE] = testResponse
    messageId = createUniqueId()
    payload[MESSAGE_ID] = messageId
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
    from ils.sfc.common.constants import ISOLATION_MODE
    from system.ils.sfc import getDatabaseName
    isolationMode = chartProperties[ISOLATION_MODE]
    return getDatabaseName(isolationMode)

def getTagProvider(chartProperties):
    from ils.sfc.common.constants import ISOLATION_MODE
    from system.ils.sfc import getProviderName
    isolationMode = chartProperties[ISOLATION_MODE]
    return getProviderName(isolationMode)
        
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