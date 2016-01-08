'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):  
    from ils.sfc.gateway.util import transferStepPropertiesToMessage, sendMessageToClient, \
    getStepProperty, handleUnexpectedGatewayError
    from system.ils.sfc.common.Constants import COMPUTER, SERVER, FILENAME, MESSAGE
    from ils.sfc.gateway.api import getProject, getChartLogger
    from ils.sfc.common.util import readFile
    # extract property values
    try:
        chartScope = scopeContext.getChartScope()
        chartLogger = getChartLogger(chartScope)
        computer = getStepProperty(stepProperties, COMPUTER) 
        payload = dict()
        if computer == SERVER:
            fileName = getStepProperty(stepProperties, FILENAME) 
            payload[MESSAGE] = readFile(fileName)
        transferStepPropertiesToMessage(stepProperties, payload)
        project = getProject(chartScope)
        sendMessageToClient(project, 'sfcPrintFile', payload)
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in printFile.py', chartLogger)
