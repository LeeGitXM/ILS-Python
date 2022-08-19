'''
Unit test support

@author: rforbes
'''

def addClientAction(chartProperties, methodName):
    '''send the name of a method to be executed on the client'''
    from ils.sfc.gateway.api import sendMessageToClient, getProject, getTopChartRunId, getChartPath

    from ils.sfc.common.constants import CHART_NAME, COMMAND, INSTANCE_ID
    payload = dict();
    payload[COMMAND] = methodName
    payload[CHART_NAME] = getChartPath(chartProperties)
    payload[INSTANCE_ID] = getTopChartRunId(chartProperties)
    project = getProject(chartProperties)
    sendMessageToClient(project, 'sfcTestAddAction', payload) 

def cleanupTestControlPanels(database):
    import system.db
    from ils.sfc.common.windowUtil import removeControlPanelRecord
    results = system.db.runQuery("select controlPanelId from SfcControlPanel where controlPanelId < 0")
    for result in results:
        controlPanelId = result[0]
        removeControlPanelRecord(controlPanelId, database)

def runTests(originator, isolationMode, project, reportFile, testPattern, timeoutSecs):
    '''Run test charts'''
    from system.ils.sfc import getMatchingCharts, getDatabaseName, \
    initializeTests, testsAreRunning, timeoutRunningTests
    from ils.sfc.client.util import startChart
    import system.db, time
    testCharts = getMatchingCharts(testPattern)
    initializeTests(reportFile)
    database = getDatabaseName(isolationMode)
    system.db.runUpdateQuery("SET IDENTITY_INSERT SfcControlPanel ON")
    cleanupTestControlPanels(database)
    timeoutTime = time.time() + timeoutSecs
    controlPanelId = -1
    for chartPath in testCharts:
        system.db.runUpdateQuery("insert into SfcControlPanel (controlPanelId, controlPanelName, chartPath) values (%d, '%s', '%s')" % (controlPanelId, chartPath, chartPath), database)
        print 'starting test', chartPath
        startChart(chartPath, controlPanelId, project, originator, isolationMode)
        controlPanelId -= 1
    system.db.runUpdateQuery("SET IDENTITY_INSERT SfcControlPanel OFF")
    time.sleep(5) # fudge factor to allow at least one test to get started
    while time.time() < timeoutTime and testsAreRunning():
        time.sleep(5)
    timeoutRunningTests()
    cleanupTestControlPanels(database)

def countMessages(chartScope): 
    '''count the number of messages in the current queue'''
    from ils.queue.message import queueSQL
    from system.ils.sfc import assertEqual
    from ils.sfc.gateway.api import getDatabaseName, getCurrentMessageQueue
    import system.db
    queue = getCurrentMessageQueue(chartScope)
    db = getDatabaseName(chartScope)
    SQL = queueSQL(queue, True, "ASC", db)
    pds = system.db.runQuery(SQL, db)
    return len(pds)
        