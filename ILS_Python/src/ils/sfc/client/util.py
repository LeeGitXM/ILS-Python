'''
Created on Oct 31, 2014

@author: rforbes
'''
import system.util 
from ils.sfc.common.constants import *
from ils.sfc.common.sessions import updateSessionStatus
from ils.sfc.client.controlPanel import ControlPanel

def sendResponse(request, response):
    ''' send a message to the Gateway in response to a previous request message''' 
    replyPayload = dict() 
    replyPayload[RESPONSE] = response
    messageId = request[MESSAGE_ID]
    replyPayload[MESSAGE_ID] = messageId    
    project = system.util.getProjectName()
    system.util.sendMessage(project, 'sfcResponse', replyPayload, "G")
       
def registerClient():
    from ils.sfc.common.util import getDatabaseFromSystem
    project = system.util.getProjectName()
    database = getDatabaseFromSystem()
    user = system.security.getUsername()
    payload = dict()
    payload[PROJECT] = project
    payload[USER] = user
    payload[DATABASE] = database
    system.util.sendMessage(project, 'sfcRegisterClient', payload, "G")
       
def runChart(chartName):
    from ils.sfc.common.util import getDatabaseFromSystem
    from ils.sfc.client.controlPanel import createControlPanel
    project = system.util.getProjectName()
    database = getDatabaseFromSystem()
    user = system.security.getUsername()
    initialChartProps = dict()
    initialChartProps[PROJECT] = project
    initialChartProps[CHART_NAME] = chartName
    initialChartProps[USER] = user
    initialChartProps[DATABASE] = database
    runId = system.sfc.startChart(chartName, initialChartProps)
    initialChartProps[INSTANCE_ID] = runId
    createControlPanel(initialChartProps)
    registerClient()

def onStop(chartProperties):
    '''this should be called from every SFC chart's onStop hook'''
    updateSessionStatus(chartProperties, STOPPED)
    
def onAbort(chartProperties):
    '''this should be called from every SFC chart's onPause hook'''
    updateSessionStatus(chartProperties, ABORTED)
    
def openWindow(windowName, position, scale, windowProps):
    '''Open the given window inside the main window with the given position and size'''
    newWindow = system.nav.openWindowInstance(windowName, windowProps)
    mainWindow = newWindow.parent
    position = position.lower()
    width = mainWindow.getWidth() * scale
    height = mainWindow.getHeight() * scale
    if position.endswith(LEFT):
        ulx = 0
    elif position.endswith(CENTER):
        ulx = .5 * mainWindow.getWidth() - .5 * width
    else:
        ulx = mainWindow.getWidth() - width

    if position.startswith(TOP):
        uly = 0
    elif position.startswith(CENTER):
        uly = .5 * mainWindow.getHeight() - .5 * height
    else:
        uly = mainWindow.getHeight() - height
    newWindow.setSize(int(width), int(height))
    newWindow.setLocation(int(ulx), int(uly))

def testQuery(query, database):
    from java.lang import Exception
    try:
        results = system.db.runQuery(query, database)
        system.gui.messageBox("Query is OK; returned %d row(s)"%len(results))
    except Exception, e:
        cause = e.getCause()
        system.gui.messageBox("query failed: %s"%cause.getMessage())