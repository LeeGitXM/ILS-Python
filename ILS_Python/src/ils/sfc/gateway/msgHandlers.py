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
    
def sfcStartChart(payload):
    '''start the chart and message the client. At this point the only reason
       we start on the gateway side is to lazy init the units. Maybe we can
       move that elsewhere and get rid of this method, just start chart on client'''
    import system.sfc.startChart
    import system.util.sendMessage
    import ils.common.units
    from system.ils.sfc import registerSfcProject
    from ils.sfc.common.util import getDatabaseName
    from ils.sfc.common.constants import INSTANCE_ID, PROJECT, CHART_NAME
    print 'units by name', ils.common.units.Unit.unitsByName
    chartName = payload[CHART_NAME]
    project = payload[PROJECT]
    registerSfcProject(project)
    database = getDatabaseName(payload)
    ils.common.units.Unit.lazyInitialize(database)
    runId = system.sfc.startChart(chartName, payload)
    # add the chart run id so the client can know it
    payload[INSTANCE_ID] = runId
    system.util.sendMessage(project, 'sfcChartStarted', payload, "C")

