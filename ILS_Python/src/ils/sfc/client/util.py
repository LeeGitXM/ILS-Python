'''
Created on Oct 31, 2014

@author: rforbes
'''
import system.util 

def sendResponse(messageId, response):
    ''' send a message to the Gateway in response to a previous request message''' 
    from ils.sfc.common.constants import RESPONSE, MESSAGE_ID
    replyPayload = dict() 
    replyPayload[RESPONSE] = response
    replyPayload[MESSAGE_ID] = messageId    
    project = system.util.getProjectName()
    system.util.sendMessage(project, 'sfcResponse', replyPayload, "G")

# This is always called from the client
def runChart(chartName, isolationMode):
    from ils.sfc.common.constants import PROJECT, USER, ISOLATION_MODE, CHART_NAME
    project = system.util.getProjectName()
    user = system.security.getUsername()
    initialChartProps = dict()
    initialChartProps[ISOLATION_MODE] = isolationMode
    initialChartProps[PROJECT] = project
    initialChartProps[USER] = user
    # chart name is not really needed in the initial chart properties, but we
    # are using the same dictionary for message payload and initial chart 
    # properties so we put it in--it is really just in the payload
    initialChartProps[CHART_NAME] = chartName
    system.util.sendMessage(project, 'sfcStartChart', initialChartProps, "G")
    
def openWindow(windowName, position, scale, windowProps):
    '''Open the given window inside the main window with the given position and size'''
    from ils.sfc.common.constants import LEFT, CENTER, TOP
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
    return newWindow

def testQuery(query, isolationMode):
    from java.lang import Exception
    from system.ils.sfc import getDatabaseName
    try:
        results = system.db.runQuery(query, getDatabaseName(isolationMode))
        system.gui.messageBox("Query is OK; returned %d row(s)"%len(results))
    except Exception, e:
        cause = e.getCause()
        system.gui.messageBox("query failed: %s"%cause.getMessage())
        
def checkConfig():
    messages = []
    from system.ils.sfc import getDatabaseName, getTimeFactor, getProviderName 
    from ils.sfc.common.util import isEmpty
    isolationDatabase = getDatabaseName(True)
    print 'isolation database', isolationDatabase
    nonIsolationDatabase = getDatabaseName(False)
    print 'non-isolation database', nonIsolationDatabase
    if isEmpty(isolationDatabase):
        messages.append('No database defined for isolation mode')
    elif system.db.getConnectionInfo(isolationDatabase) == None:
        messages.append('Isolation database name ' + isolationDatabase + " is not a defined Datasource")        
    else:
        checkSchema(isolationDatabase, 'Isolation', messages)
    if isEmpty(nonIsolationDatabase):
        messages.append('No database defined for non-isolation mode')
    elif system.db.getConnectionInfo(nonIsolationDatabase) == None:
        messages.append('Non-Isolation database name ' + nonIsolationDatabase + " is not a defined Datasource")        
    else:
        checkSchema(nonIsolationDatabase, 'Non-Isolation', messages)
    if isEmpty(getProviderName(True)):
        messages.append('No provider defined for isolation mode')
    if isEmpty(getProviderName(False)):
        messages.append('No provider defined for non-isolation mode')       
        
    if len(messages) == 0:
        system.gui.messageBox("config OK")
    else:
        errorMsg = ''
        for msg in messages:
            errorMsg = errorMsg + msg + '\n'
        system.gui.errorBox(errorMsg)
    
def checkSchema(database, dbType, messages):
    tableNames = ['Junk', 'SfcControlPanelMsgs', 'Units', 'UnitAliases', 'QueueMessageStatus', 'QueueDetail', 'QueueMaster']
    for table in tableNames:
        if not tableExists(table, database):
            messages.append("Table " + table + " does not exist in " + dbType + " database")

def tableExists(table, database):
    query = "select count(*) from " + table
    try:
        system.db.runQuery(query, database)
        return True
    except:
        return False