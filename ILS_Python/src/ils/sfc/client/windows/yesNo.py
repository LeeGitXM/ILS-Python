'''
Created on Dec 3, 2015

@author: rforbes
'''

import system

def yesActionPerformed(event):
    window=system.gui.getParentWindow(event)
    sendResponse(window, "Yes")
  
def noActionPerformed(event):
    window=system.gui.getParentWindow(event)
    sendResponse(window, "No")
    
def sendResponse(window, response):
    '''standard actions when a window representing a response is closed by the user'''
    from ils.sfc.common.constants import RESPONSE, MESSAGE_ID
    rootContainer = window.getRootContainer()
    windowId = rootContainer.windowId
    replyPayload = dict() 
    replyPayload[RESPONSE] = response
    replyPayload[MESSAGE_ID] = windowId    
    project = system.util.getProjectName()
    system.util.sendMessage(project, 'sfcResponse', replyPayload, "G")
    system.nav.closeWindow(window)