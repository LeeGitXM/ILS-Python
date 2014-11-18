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

def sfcRegisterClient(payload):
    from ils.sfc.common.constants import  PROJECT, DATABASE
    from system.ils.sfc import setSfcProjectInfo
    setSfcProjectInfo(payload[PROJECT], payload[DATABASE])

