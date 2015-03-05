'''
Created on Jan 14, 2015

@author: rforbes
'''

def okActionPerformed(event):
    from ils.sfc.client.util import sendResponse
    import system.gui.getParentWindow
    messageId = event.source.parent.messageId
    sendResponse(messageId, True)
    window = system.gui.getParentWindow(event)
    system.nav.closeWindow(window)
  
def cancelActionPerformed(event):
    from ils.sfc.client.util import sendResponse
    import system.gui.getParentWindow
    messageId = event.source.parent.messageId
    sendResponse(messageId, False)
    window = system.gui.getParentWindow(event)
    system.nav.closeWindow(window)
