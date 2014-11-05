'''
Created on Nov 3, 2014

@author: rforbes
'''
import system

from ils.sfc.common.constants import CHART_PARENT, INSTANCE_ID, DATABASE

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
