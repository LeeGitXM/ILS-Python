'''
Created on Oct 31, 2014

@author: rforbes
'''
import system.util, time
from ils.io.util import readTag
from ils.sfc.common.constants import CLIENT_DONE, CHART_SCOPE, STEP_SCOPE, PROJECT, ISOLATION_MODE, \
    CONTROL_PANEL_NAME, CONTROL_PANEL_ID, ORIGINATOR, MESSAGE_QUEUE, DEFAULT_MESSAGE_QUEUE, DATABASE, TAG_PROVIDER, TIME_FACTOR
from ils.sfc.common.util import chartIsRunning
from ils.config.client import getDatabase, getTagProvider, getTimeFactor
from ils.sfc.recipeData.core import splitKey, setRecipeData
from ils.sfc.recipeData.api import s88GetStepInfoFromId
from ils.log import getLogger
log = getLogger(__name__)

# This is called from a timer
def checkTimeout(rootContainer):
    timeoutTime = rootContainer.timeout
    
    if timeoutTime == None or timeoutTime <= 0:
        return False
    
    if timeoutTime < time.time():
        return True
    
    return False

def setClientResponse(rootContainer, response):
    '''
    This runs in client scope when the user presses OK on any of the myriad of GUI windows that get a response.
    This stores the response in the appropriate location..
    '''
    log.infof("In %s.setClientResponse()...", __name__)
    
    responseLocation = rootContainer.responseLocation
    chartId = rootContainer.chartId
    stepId = rootContainer.stepId
    keyAndAttribute = rootContainer.keyAndAttribute
    
    if responseLocation == CHART_SCOPE:
        log.tracef("  chart Id: %s", chartId)
        log.tracef("   step id: %s", stepId)
        system.sfc.setVariable(chartId, keyAndAttribute, response)
        
    elif responseLocation == STEP_SCOPE:
        log.tracef("  chart Id: %s", chartId)
        log.tracef("   step id: %s", stepId)
        system.sfc.setVariable(chartId, stepId, keyAndAttribute, response)
    
    else:
        targetStepId = rootContainer.targetStepId
        db = getDatabase()
        
        '''
        An optimization is to assume that the attribute is ".value" if they did not enter an attribute.
        At one point, I assumed that the response could ONLT be stuffed into a SIMPLE VALUE type of recipe data.  
        Segun came up with a pretty cool use case where they would select the mode of a control from a SELECT INPUT step.
        So in stead of looking for ".value",  just look for a "."  Segun wants the response to go to the outputValue of an OUTPUT.
        The new strategy might get confused if we are specifying a folder; but I think that if they specify a folder then they MUST specify the attribute.
        '''
        if keyAndAttribute.find(".value") < 0:
            keyAndAttribute = keyAndAttribute + ".value"
            
        folder,key,attribute = splitKey(keyAndAttribute)
        log.tracef("   folder: %s", folder)
        log.tracef("   key: %s", key)
        log.tracef("   attribute: %s", attribute)
        chartPath, stepName = s88GetStepInfoFromId(targetStepId, db)
        log.tracef("  chartPath: %s", chartPath)
        log.tracef("   stepName: %s", stepName)
        setRecipeData(stepName, targetStepId, folder, key, attribute, response, db)


def setClientDone(rootContainer):
    '''
    This runs in client scope when the user presses OK on any of the myriad of GUI windows that get a response.
    This signals the SFC in the gateway that the user has finished.
    '''
    log.infof("In %s.setClientDone()...", __name__)
    chartId = rootContainer.chartId
    stepId = rootContainer.stepId
    log.tracef("  chart Id: %s", chartId)
    log.tracef("   step id: %s", stepId)
    system.sfc.setVariable(chartId, stepId, CLIENT_DONE, True)

def sendResponse(messageId, response):
    ''' send a message to the Gateway in response to a previous request message''' 
    from ils.sfc.common.constants import RESPONSE, WINDOW_ID
    replyPayload = dict() 
    replyPayload[RESPONSE] = response
    replyPayload[WINDOW_ID] = messageId    
    project = system.util.getProjectName()
    sendMessageToGateway(project, 'sfcResponse', replyPayload)  


''' 
We need to get the queue name out of the unit procedure and use that as the default message queue, but
unlike in the old system, where we ran a unit procedure, here we are running a chart, and the chart had
better have a unit procedure on the top chart.  However all this method has is a chart path, it has no
way of knowing about the unit procedure block.  So when the unit procedure block runs we will update the 
record in the SfcControlParameter table. 

1/28/22 - I am now assuming that this is only called from a client.  If there is some mechanism to call this from the gateway
          then it needs to check scope.
'''
def startChart(chartPath, controlPanelName, project, originator, isolationMode, chartParams={}):
    print "Starting a chart: <%s>, control panel: <%s>, project: <%s>, originator: <%s>, isolation: <%s>" % (chartPath, controlPanelName, project, originator, str(isolationMode))
    if chartIsRunning(chartPath, isolationMode):
        print "Exiting because the chart is already running!"
        return
    
    db = getDatabase()
    tagProvider = getTagProvider()
    timeFactor = getTimeFactor()

    from ils.sfc.client.windows.controlPanel import createControlPanel, getControlPanelIdForName
    controlPanelId = getControlPanelIdForName(controlPanelName, db)
    if controlPanelId == None:
        controlPanelId = createControlPanel(controlPanelName, db)
    
    initialChartParams = dict()
    initialChartParams[PROJECT] = project
    initialChartParams[ISOLATION_MODE] = isolationMode
    initialChartParams[CONTROL_PANEL_NAME] = controlPanelName
    initialChartParams[CONTROL_PANEL_ID] = controlPanelId
    initialChartParams[ORIGINATOR] = originator
    initialChartParams[MESSAGE_QUEUE] = DEFAULT_MESSAGE_QUEUE
    initialChartParams[DATABASE] = db
    initialChartParams[TAG_PROVIDER] = tagProvider
    initialChartParams[TIME_FACTOR] = timeFactor

    # What does this do??? (PH 12/21/2021
    initialChartParams.update(chartParams)

    print "Starting a chart with: ", initialChartParams
    runId = system.sfc.startChart(chartPath, initialChartParams)
    
    if isolationMode:
        isolationFlag = 1
    else:
        isolationFlag = 0
    
    updateSql = "Update SfcControlPanel set chartRunId = '%s', originator = '%s', project = '%s', isolationMode = %d, "\
        "EnableCancel = 1, EnablePause = 1, EnableReset = 1, EnableResume = 1, EnableStart = 1 "\
        "where controlPanelId = %s" % (runId, originator, project, isolationFlag, str(controlPanelId))
    print "SQL: ", updateSql
    system.db.runUpdateQuery(updateSql, database=db)
    print "...done..."
    return runId

def startChartWithoutControlPanel(chartPath, project, originator, isolationMode, chartParams={}):
    print "Starting a chart: <%s>, project: <%s>, originator: <%s>, isolation: <%s>" % (chartPath, project, originator, str(isolationMode))
    if chartIsRunning(chartPath, isolationMode):
        print "Exiting because the chart is already running!"
        return
    
    db = getDatabase()
    tagProvider = getTagProvider()
    
    initialChartParams = dict()
    initialChartParams[PROJECT] = project
    initialChartParams[ISOLATION_MODE] = isolationMode
    initialChartParams[ORIGINATOR] = originator
    initialChartParams[MESSAGE_QUEUE] = DEFAULT_MESSAGE_QUEUE
    initialChartParams[DATABASE] = db
    initialChartParams[TAG_PROVIDER] = tagProvider
    
    initialChartParams.update(chartParams)
    
    print "Starting a chart with: ", initialChartParams
    runId = system.sfc.startChart(chartPath, initialChartParams)
    
    return runId

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

    tableNames = ['SfcControlPanelMessage', 'Units', 'UnitAliases', 'QueueMessageStatus', 'QueueDetail', 'QueueMaster']
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
        
def getStartInIsolationMode():
    '''Get the client-side flag that indicates whether to start charts in isolation mode.
       CAUTION: this does not relate to any particular chart run and is only meaningful
       at the moment a chart is started.'''
    return readTag('[Client]/Isolation Mode').value

def sendMessageToGateway(project, handler, payload):
    '''Send a message to the gateway'''
    from ils.sfc.common.constants import HANDLER
    from system.util import sendMessage
    payload[HANDLER] = handler
    # print 'sending msg', handler
    sendMessage(project, 'sfcMessage', payload, "G")
    
def getIndexNames():
    results = system.db.runQuery('select KeyName from SfcRecipeDataKeyMaster', getDatabase())
    names = []
    names.append(None)
    for row in results:
        names.append(row[0])
    return names

def getKeySize(keyName):
    '''Get the individual key values for the given key index'''
    import system
    sql = "select count(KeyValue) from SfcRecipeDataKeyMaster master, SfcRecipeDataKeyDetail detail where \
        master.KeyName = '%s' and detail.KeyId = master.KeyId order by KeyIndex asc" % (keyName)
    return system.db.runScalarQuery(sql, getDatabase())
