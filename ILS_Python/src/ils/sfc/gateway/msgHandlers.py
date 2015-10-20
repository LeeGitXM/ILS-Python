'''
Created on Nov 3, 2014

@author: rforbes
'''
from ils.sfc.common.constants import MESSAGE_ID

def sfcResponse(payload):
    '''Handle a message that is a response to a request sent from the Gateway'''
    from system.ils.sfc import setResponse
    messageId = payload[MESSAGE_ID]
    setResponse(messageId, payload)

def sfcActivateStep(payload):
    '''For testing only--activate a step as if it was being run in a chart'''
    from ils.sfc.common.constants import  CLASS_NAME, CHART_PROPERTIES, STEP_PROPERTIES
    from system.ils.sfc import activateStep
    activateStep(payload[CLASS_NAME], payload[CHART_PROPERTIES], payload[STEP_PROPERTIES])
    
def sfcRunTests(payload):
    '''Run test charts'''
    from ils.sfc.common.constants import TEST_CHART_PATHS, TEST_REPORT_FILE 
    import system.ils.sfc
    testChartPaths = payload[TEST_CHART_PATHS]
    reportFile = payload[TEST_REPORT_FILE]
    system.ils.sfc.initializeTests(reportFile)
    for chartPath in testChartPaths:
        system.ils.sfc.startTest(chartPath)
        sfcStartChart(payload)
        system.sfc.startChart(chartPath, payload)
 
def sfcReportTests(payload):
    import system.ils.sfc
    system.ils.sfc.reportTests()
        
def sfcStartChart(payload):
    '''Prepare for chart start. lazy init the units for this script mgr
       (CAUTION--there are other gateway script mgrs) and also to save the name of
       the invoking project, as chart status message currently needs this.'''
    import ils.common.units
    from system.ils.sfc import registerSfcProject
    from ils.sfc.gateway.api import getDatabaseName
    from ils.sfc.common.constants import PROJECT
    project = payload[PROJECT]
    registerSfcProject(project)
    database = getDatabaseName(payload)
    ils.common.units.Unit.lazyInitialize(database)
    
def sfcFailTest(payload):
    '''this is a message handler'''
    from system.ils.sfc import failTest
    from ils.sfc.common.constants import CHART_NAME, MESSAGE
    failTest(payload[CHART_NAME], payload[MESSAGE])
    
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
    print('gateway msg handler: sfcCancelChart')    
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
        