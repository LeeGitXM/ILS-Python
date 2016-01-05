'''
Created on Nov 3, 2014

@author: rforbes
'''
from ils.sfc.common.constants import MESSAGE_ID

def dispatchMessage(payload):
    from ils.sfc.common.util import callMethodWithParams
    from ils.sfc.common.constants import MESSAGE
    msgName = payload[MESSAGE]
    methodPath = 'ils.sfc.gateway.msgHandlers.' + msgName
    keys = ['payload']
    values = [payload]
    try:
        callMethodWithParams(methodPath, keys, values)
    except Exception, e:
        try:
            cause = e.getCause()
            errMsg = "Error dispatching gateway message %s: %s" % (msgName, cause.getMessage())
        except:
            errMsg = "Error dispatching gateway message %s: %s" % (msgName, str(e))
        #TODO: whats the right logger here?
        print errMsg
                              
def sfcResponse(payload):
    '''Handle a message that is a response to a request sent from the Gateway'''
    from system.ils.sfc import setResponse
    messageId = payload[MESSAGE_ID]
    setResponse(messageId, payload)
        
def sfcUpdateDownloads(payload):
    from ils.sfc.common.constants import ID, INSTANCE_ID
    from ils.sfc.gateway.monitoring import getMonitoringMgr
    timerId = payload[ID]
    chartRunId = payload[INSTANCE_ID]
    monitoringMgr = getMonitoringMgr(chartRunId, timerId)
    if monitoringMgr != None:
        monitoringMgr.sendClientUpdate()
    # else chart probably ended

def sfcCancelChart(payload):
    from ils.sfc.common.constants import INSTANCE_ID
    from ils.sfc.gateway.util import basicCancelChart
    topChartRunId = payload[INSTANCE_ID]
    basicCancelChart(topChartRunId)

def sfcPauseChart(payload):
    from ils.sfc.common.constants import INSTANCE_ID
    from ils.sfc.gateway.util import basicPauseChart    
    topChartRunId = payload[INSTANCE_ID]
    basicPauseChart(topChartRunId)
    
def sfcResumeChart(payload):
    from ils.sfc.common.constants import INSTANCE_ID
    from ils.sfc.gateway.util import basicResumeChart    
    topChartRunId = payload[INSTANCE_ID]
    basicResumeChart(topChartRunId)

# test stuff
def sfcRunTests(payload):
    '''Run test charts'''
    from ils.sfc.common.constants import TEST_CHART_PATHS, TEST_REPORT_FILE 
    import system.ils.sfc
    testChartPaths = payload[TEST_CHART_PATHS]
    reportFile = payload[TEST_REPORT_FILE]
    system.ils.sfc.initializeTests(reportFile)
    for chartPath in testChartPaths:
        system.ils.sfc.startTest(chartPath)
        system.sfc.startChart(chartPath, payload)
 
def sfcReportTests(payload):
    import system.ils.sfc
    system.ils.sfc.reportTests()
    
def sfcFailTest(payload):
    '''this is a message handler'''
    from system.ils.sfc import failTest
    from ils.sfc.common.constants import CHART_NAME, MESSAGE
    failTest(payload[CHART_NAME], payload[MESSAGE])

def sfcActivateStep(payload):
    '''For testing only--activate a step as if it was being run in a chart'''
    from ils.sfc.common.constants import  CLASS_NAME, CHART_PROPERTIES, STEP_PROPERTIES
    from system.ils.sfc import activateStep
    activateStep(payload[CLASS_NAME], payload[CHART_PROPERTIES], payload[STEP_PROPERTIES])
        
def sfcDevTest(payload):
    # from system.ils.sfc.common.Constants import DATA
    obj = payload['data']
    obj.sayHi()
    
def sfcCloseWindow(payload):
    '''close an open window. this is not usually called, as the step methods delete their own 
       windows. The client only needs to message a close window request when the window persists
       beyond the step scope, like for MessageDialog'''
    from ils.sfc.common.constants import DATABASE, WINDOW_ID, TABLE, PROJECT
    from ils.sfc.gateway.util import deleteAndSendClose
    import system.db
    table = payload[TABLE]
    project = payload[PROJECT]
    windowId = payload[WINDOW_ID]
    database = payload[DATABASE]
    system.db.runUpdateQuery("delete from %s where windowId = '%s'" % (table, windowId), database)   
    deleteAndSendClose(project, windowId, database)
