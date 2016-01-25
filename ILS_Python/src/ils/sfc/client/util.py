'''
Created on Oct 31, 2014

@author: rforbes
'''
import system.util 

def sendResponse(messageId, response):
    ''' send a message to the Gateway in response to a previous request message''' 
    from ils.sfc.common.constants import RESPONSE, WINDOW_ID
    replyPayload = dict() 
    replyPayload[RESPONSE] = response
    replyPayload[WINDOW_ID] = messageId    
    project = system.util.getProjectName()
    sendMessageToGateway(project, 'sfcResponse', replyPayload)  

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
    productionDatabase = getDatabaseName(False)
    messages.append('============Checking Production settings...=============')
    checkDatabaseConfig(productionDatabase, messages)
    productionTimeFactor = getTimeFactor(False)
    if productionTimeFactor == None:
        messages.append("No time factor is defined")
    elif productionTimeFactor != 1.:
        messages.append("WARNING: production time factor is not 1 (" + productionTimeFactor + ")")
    productionProvider = getProviderName(False)
    if isEmpty(productionProvider):
        messages.append('No provider defined')
    #TODO check if provider is defined in gateway

    messages.append('==============Checking Isolation settings...===============')
    isolationDatabase = getDatabaseName(True)
    if(isolationDatabase == productionDatabase):
        messages.append("Caution: isolation database is the same as production database")
    else:
        checkDatabaseConfig(isolationDatabase, messages)
    isolationTimeFactor = getTimeFactor(True)
    if isolationTimeFactor == None:
        messages.append("No time factor is defined")
    isolationProvider = getProviderName(True)
    if isEmpty(isolationProvider):
        messages.append('No tag provider defined')
    #TODO check if provider is defined in gateway
    
    #todo: check for unit loading and time conversion
    
    boxMessage = ''
    for msg in messages:
        boxMessage = boxMessage + msg + '\n'
    system.gui.messageBox(boxMessage)
    
def checkDatabaseConfig(database, messages):
    from ils.sfc.common.util import isEmpty
    import ils.common.units
    from ils.sfc.common.constants import SECOND, MINUTE
    
    if isEmpty(database):
        messages.append('No database defined')
        return
    elif system.db.getConnectionInfo(database) == None:
        messages.append(database + " is not a defined Datasource")        
        return

    tableNames = ['SfcControlPanelMsgs', 'Units', 'UnitAliases', 'QueueMessageStatus', 'QueueDetail', 'QueueMaster']
    for table in tableNames:
        if not tableExists(table, database):
            messages.append("Table " + table + " does not exist")
    
    if(tableExists('QueueMaster', database)):
        printMessageQueueNames(database, messages)
        
    if tableExists('Units', database):            
        ils.common.units.Unit.lazyInitialize(database)
        results = system.db.runQuery("select count(*) from Units", database)
        numUnits = results[0][0]
        if numUnits == 0:
            messages.append("The Units table is empty")
        elif numUnits == 3:
            messages.append("The Units table contains only time units")
        if numUnits >= 3:
            secondsUnit = ils.common.units.Unit.getUnit(SECOND)
            minutesUnit = ils.common.units.Unit.getUnit(MINUTE)
            if secondsUnit == None:
                messages.append("Seconds unit " + SECOND + " not in database")
            elif minutesUnit == None:
                messages.append("Minutes unit " + MINUTE + " not in database")
            else:
                secondsPerMinute = minutesUnit.convertTo(secondsUnit, 1)
                if round(secondsPerMinute) != 60:
                    messages.append("time unit conversions wrong: " + secondsPerMinute + " seconds per minute")

def printMessageQueueNames(db, messages):
    from ils.queue.commons import getQueueNames
    from system.util import jsonEncode
    queueNames = getQueueNames(db)
    messages.append("FYI, Message Queues are: %s" % jsonEncode(queueNames))
    
def tableExists(table, database):
    query = "select count(*) from " + table
    try:
        results = system.db.runQuery(query, database)
        return results != None
    except:
        return False
   
def openWindow(windowId, window):
    '''Open a window given its type and database key'''
    import system.nav
    from ils.sfc.common.constants import WINDOW_ID
    windowProps = {WINDOW_ID:windowId}
    system.nav.openWindow(window, windowProps)

def startChart(controlPanelId):
    from ils.sfc.common.constants import PROJECT, ISOLATION_MODE, CONTROL_PANEL_ID
    from ils.sfc.client.windows.controlPanel import getControlPanelChartPath
    project = system.util.getProjectName()
    isolationMode = getStartInIsolationMode()
    initialChartParams = dict()
    initialChartParams[PROJECT] = project
    initialChartParams[ISOLATION_MODE] = isolationMode
    initialChartParams[CONTROL_PANEL_ID] = controlPanelId
    chartPath = getControlPanelChartPath(controlPanelId)
    runId = system.sfc.startChart(chartPath, initialChartParams)
    originator = system.security.getUsername()
    if isolationMode:
        isolationFlag = 1
    else:
        isolationFlag = 0
    updateSql = "Update SfcControlPanel set chartRunId = '%s', originator = '%s', project = '%s', isolationMode = %d where controlPanelId = %d" % (runId, originator, project, isolationFlag, controlPanelId)
    numUpdated = system.db.runUpdateQuery(updateSql)
    if numUpdated == 0:
        system.gui.messageBox("Failed to updated SfcControlPanel with chart start info")

    
def getChartStatus(runId):
    '''Get the status of a running chart. Returns None if the run is not found'''
    from system.sfc import getRunningCharts
    runningCharts = getRunningCharts()
    status = 'None'
    for row in range(runningCharts.rowCount):
        rowRunId = runningCharts.getValueAt(row, 'instanceId')
        if rowRunId == runId:
            chartState = runningCharts.getValueAt(row, 'chartState')
            status = str(chartState)
    return status

def getStartInIsolationMode():
    '''Get the client-side flag that indicates whether to start charts in isolation mode.
       CAUTION: this does not relate to any particular chart run and is only meaningful
       at the moment a chart is started.'''
    return system.tag.read('[Client]/Isolation Mode').value

def getDatabase():
    '''Get the database name, taking isolation mode into account'''
    return system.tag.read('[Client]/Database').value

def getTagProvider():
    '''Get the tag provider name, taking isolation mode into account'''
    return system.tag.read('[Client]/Tag Provider').value

def sendMessageToGateway(project, handler, payload):
    '''Send a message to the gateway'''
    from ils.sfc.common.constants import HANDLER
    from system.util import sendMessage
    payload[HANDLER] = handler
    print 'sending msg', handler
    sendMessage(project, 'sfcMessage', payload, "G")