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
    
