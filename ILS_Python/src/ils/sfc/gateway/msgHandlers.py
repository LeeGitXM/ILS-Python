'''
Created on Nov 3, 2014

@author: rforbes
'''

import system
from ils.sfc.common.api import callMethodWithParams
from ils.sfc.common.constants import HANDLER, WINDOW_ID, ID, INSTANCE_ID, DATABASE, WINDOW_ID, TABLE, PROJECT
from ils.sfc.gateway.api import deleteAndSendClose
from system.ils.sfc import setResponse
from ils.sfc.gateway.monitoring import getMonitoringMgr

def dispatchMessage(payload):
    methodName = payload[HANDLER]
    methodPath = 'ils.sfc.gateway.msgHandlers.' + methodName
    keys = ['payload']
    values = [payload]
    try:
        callMethodWithParams(methodPath, keys, values)
    except Exception, e:
        try:
            cause = e.getCause()
            errMsg = "Error dispatching gateway message %s: %s" % (methodName, cause.getMessage())
        except:
            errMsg = "Error dispatching gateway message %s: %s" % (methodName, str(e))
        #TODO: whats the right logger here?
        print errMsg
                              
def sfcResponse(payload):
    '''Handle a message that is a response to a request sent from the Gateway'''
    windowId = payload[WINDOW_ID]
    setResponse(windowId, payload)
        
def sfcUpdateDownloads(payload):

    timerId = payload[ID]
    chartRunId = payload[INSTANCE_ID]
    monitoringMgr = getMonitoringMgr(chartRunId, timerId)
    if monitoringMgr != None:
        monitoringMgr.sendClientUpdate()
    # else chart probably ended
    
def sfcCloseWindow(payload):
    '''close an open window. this is not usually called, as the step methods delete their own 
       windows. The client only needs to message a close window request when the window persists
       beyond the step scope, like for MessageDialog'''


    table = payload[TABLE]
    project = payload[PROJECT]
    windowId = payload[WINDOW_ID]
    database = payload[DATABASE]
    system.db.runUpdateQuery("delete from %s where windowId = '%s'" % (table, windowId), database)   
    deleteAndSendClose(project, windowId, database)

def sfcRunTests(payload):
    '''Run test charts'''
    from ils.sfc.common.constants import TEST_REPORT_FILE, TEST_PATTERN, \
    ISOLATION_MODE, PROJECT, USER, TIMEOUT
    from ils.sfc.gateway.test import runTests
    originator = payload[USER]
    isolationMode = payload[ISOLATION_MODE]
    project = payload[PROJECT]
    reportFile = payload[TEST_REPORT_FILE]
    testPattern = payload[TEST_PATTERN]
    timeoutSecs = payload[TIMEOUT]
    runTests(originator, isolationMode, project, reportFile, testPattern, timeoutSecs)
         
def sfcReportTests(payload):
    import system.ils.sfc
    system.ils.sfc.reportTests()
    
def sfcFailTest(payload):
    '''this is a message handler'''
    from ils.sfc.common.constants import CHART_NAME, MESSAGE
    import system.ils.sfc
    system.ils.sfc.failTestChart(payload[CHART_NAME], payload[MESSAGE])