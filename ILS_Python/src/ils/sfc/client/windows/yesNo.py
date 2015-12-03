'''
Created on Dec 3, 2015

@author: rforbes
'''

def populate(window):
    promptField = window.getRootContainer().getComponent('prompt')
    promptField.setText(window.getRootContainer().prompt)
    
def sendResponse(window, response):   
    from ils.sfc.common.constants import RESPONSE
    from ils.sfc.client.windowUtil import responseWindowClosed
    responseWindowClosed(window, response)