'''
Created on Sep 22, 2015

@author: rforbes
'''

def defaultPostingMethod(window, dataTable):
    dataTableComponent = window.getRootContainer().getComponent('dataTable') 
    dataTableComponent.data = dataTable
    
def windowClosed(event, buttonValue, data):
    from ils.sfc.client.windowUtil import responseWindowClosed
    from ils.sfc.common.constants import VALUE, DATA
    payload = dict()
    payload[VALUE] = buttonValue
    payload[DATA] = data   
    responseWindowClosed(event, payload)
