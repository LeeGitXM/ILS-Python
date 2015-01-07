'''
Created on Nov 3, 2014

@author: rforbes
'''
import system

from ils.sfc.common.constants import CHART_PARENT, INSTANCE_ID, DATABASE, RECIPE_DATA

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

def getChartState(chartProperties):
    from system.ils.sfc import getChartState
    #note: getChartState requires a java UUID
    return getChartState(chartProperties[INSTANCE_ID])

def getRunningCharts(chartProperties):
    from system.ils.sfc import getRunningCharts
    return getRunningCharts()

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
    return str(getTopLevelProperties(chartProperties)[INSTANCE_ID])

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
    
# this should really be in client.util
def handleUnexpectedClientError(message):
    system.gui.errorBox(message, 'Unexpected Error')

def createUniqueId():
    '''
    create a unique id
    '''
    import uuid
    return str(uuid.uuid4())