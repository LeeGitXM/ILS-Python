'''
Unit test support

@author: rforbes
'''

def addClientAction(chartProperties, methodName):
    '''send the name of a method to be executed on the client'''
    from ils.sfc.common.util import sendMessageToClient, getChartRunId
    from ils.sfc.common.constants import CHART_NAME, COMMAND, INSTANCE_ID
    from ils.sfc.gateway.util import getFullChartPath
    payload = dict();
    payload[COMMAND] = methodName
    payload[CHART_NAME] = getFullChartPath(chartProperties)
    payload[INSTANCE_ID] = getChartRunId(chartProperties)
    sendMessageToClient(chartProperties, 'sfcTestAddAction', payload)
    
