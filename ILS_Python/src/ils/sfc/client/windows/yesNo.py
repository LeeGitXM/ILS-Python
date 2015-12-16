'''
Created on Dec 3, 2015

@author: rforbes
'''

import system
yesNoTable = 'SfcYesNo'

def yesActionPerformed(event):
    window=system.gui.getParentWindow(event)
    sendResponse(window, yesNoTable, "Yes")
  
def noActionPerformed(event):
    window=system.gui.getParentWindow(event)
    sendResponse(window, yesNoTable, "No")

def timeoutActionPerformed(event):
    window=system.gui.getParentWindow(event)
    sendResponse(window, yesNoTable, "Timeout")
    
def sendResponse(window, windowTable, response):
    '''standard actions when a window representing a response is closed by the user'''
    from ils.sfc.client.util import sendResponse
    import system.db
    from ils.sfc.common.constants import RESPONSE, MESSAGE_ID
    rootContainer = window.getRootContainer()
    windowId = rootContainer.windowId
    system.db.runUpdateQuery("delete from %s where windowId = '%s'" % (windowTable, windowId))
    system.db.runUpdateQuery("delete from SfcWindow where windowId = '%s'" % (windowId))
    replyPayload = dict() 
    replyPayload[RESPONSE] = response
    replyPayload[MESSAGE_ID] = windowId    
    project = system.util.getProjectName()
    system.util.sendMessage(project, 'sfcResponse', replyPayload, "G")
    system.nav.closeWindow(window)