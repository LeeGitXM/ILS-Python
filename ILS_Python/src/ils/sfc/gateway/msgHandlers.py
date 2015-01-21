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

def sfcRegisterClient(payload):
    '''Bad name? should be sfcSetProjectInfo'''
    from ils.sfc.common.constants import  PROJECT, DATABASE
    from system.ils.sfc import setSfcProjectInfo
    setSfcProjectInfo(payload[PROJECT], payload[DATABASE])

def sfcActivateStep(payload):
    '''For testing only--activate a step as if it was being run in a chart'''
    from ils.sfc.common.constants import  CLASS_NAME, CHART_PROPERTIES, STEP_PROPERTIES
    from system.ils.sfc import activateStep
    activateStep(payload[CLASS_NAME], payload[CHART_PROPERTIES], payload[STEP_PROPERTIES])