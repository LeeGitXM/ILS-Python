'''
Unit test support

@author: rforbes
'''

def addClientAction(chartProperties, methodName):
    '''send the name of a method to be executed on the client'''
    from ils.sfc.gateway.util import getTopChartRunId
    from ils.sfc.gateway.api import sendMessageToClient, getProject

    from ils.sfc.common.constants import CHART_NAME, COMMAND, INSTANCE_ID
    from ils.sfc.gateway.util import getChartPath
    payload = dict();
    payload[COMMAND] = methodName
    payload[CHART_NAME] = getChartPath(chartProperties)
    payload[INSTANCE_ID] = getTopChartRunId(chartProperties)
    project = getProject(chartProperties)
    sendMessageToClient(project, 'sfcTestAddAction', payload) 
    
# old test msg handlers
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