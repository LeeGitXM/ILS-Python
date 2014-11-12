'''
Created on Nov 3, 2014

@author: rforbes
'''
import system
from ils.sfc.common.constants import MESSAGE_ID, USER

def sfcResponse(payload):
    '''Handle a message that is a response to a request sent from the Gateway'''
    from system.ils.sfc import setResponse
    messageId = payload[MESSAGE_ID]
    setResponse(messageId, payload)

def sfcStartChart(payload):
    from ils.sfc.common.constants import CHART_NAME, INSTANCE_ID, PROJECT, DATABASE
    chartName = payload[CHART_NAME]
    project = payload[PROJECT]
    chartRunId = system.sfc.startChart(chartName, payload)
    payload[INSTANCE_ID] = chartRunId
    system.util.sendMessage(project, 'sfcChartStarted', payload, "C")

