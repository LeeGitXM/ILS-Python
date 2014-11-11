'''
Created on Nov 3, 2014

@author: rforbes
'''
import system

from ils.sfc.common.constants import CHART_PARENT, INSTANCE_ID, DATABASE
UNEXPECTED_ERROR_HANDLER = 'sfcUnexpectedError'

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

def sendMessage(project, handler, payload):
    # TODO: check returned list of recipients
    # TODO: restrict to a particular client session
    from ils.sfc.common.constants import MESSAGE_ID
    messageId = createUniqueId()
    payload[MESSAGE_ID] = messageId
    system.util.sendMessage(project, handler, payload, "C")
    return messageId

def getLogger():
    import logging
    return logging.getLogger('ilssfc')

def handleUnexpectedError(chartProps, msg):
    '''
    Report an unexpected error so that it is visible to the operator--
    e.g. put in a message queue
    '''
    from ils.sfc.common.constants import PROJECT, MESSAGE
    project = chartProps[PROJECT]
    getLogger().error(msg)
    payload = dict()
    payload[MESSAGE] = msg
    sendMessage(project, UNEXPECTED_ERROR_HANDLER, payload)

def boolToBit(bool):
    if bool:
        return 1
    else:
        return 0
    
def getTopLevelProperties(chartProperties):
    while chartProperties.get(CHART_PARENT, None) != None:
        chartProperties = chartProperties.get(CHART_PARENT)
    return chartProperties

def getChartRunId(chartProperties):
    return getTopLevelProperties(chartProperties)[INSTANCE_ID]

def getDatabase(chartProperties):
    return getTopLevelProperties(chartProperties)[DATABASE]

def getDatabaseFromSystem():
    '''Get the project database'''
    connections = system.db.getConnections()
    numConnections = connections.rowCount
    if numConnections == 0:
        system.gui.errorBox("no database connection is available")
        return None
    else:
        if numConnections > 1:
            system.gui.warningBox("several database connections are available; one will be chosen randomly")        
        db = connections.getValueAt(0, 'name')
        return db

def createUniqueId():
    '''
    create a unique id
    '''
    import uuid
    return str(uuid.uuid4())