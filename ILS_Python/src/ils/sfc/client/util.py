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
    
def runTests(testChartPaths, isolationMode, reportFile):
    from ils.sfc.common.constants import PROJECT, USER, ISOLATION_MODE, TEST_CHART_PATHS, TEST_REPORT_FILE
    project = system.util.getProjectName()
    user = system.security.getUsername()
    initialChartProps = dict()
    initialChartProps[ISOLATION_MODE] = isolationMode
    initialChartProps[PROJECT] = project
    initialChartProps[USER] = user
    initialChartProps[TEST_CHART_PATHS] = testChartPaths
    initialChartProps[TEST_REPORT_FILE] = reportFile
    system.util.sendMessage(project, 'sfcRunTests', initialChartProps, "G")
    

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