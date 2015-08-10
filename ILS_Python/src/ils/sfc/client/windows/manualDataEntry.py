'''
Created on Jul 28, 2015

@author: rforbes
'''

def defaultPostingMethod(window, dataset):
    table = window.getRootContainer().getComponent('table') 
    table.data = dataset
    
def sendData(window):
    from ils.sfc.client.util import sendResponse
    from ils.sfc.common.constants import DATA
    table = window.getRootContainer().getComponent('table')
    dataset = table.data
    responseId = window.getRootContainer().messageId
    response = {DATA: dataset}
    sendResponse(responseId, response)
