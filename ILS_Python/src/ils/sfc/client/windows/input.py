'''
Created on Jan 16, 2015

@author: rforbes
'''
'''
Created on Jan 15, 2015

@author: rforbes
'''
def visionWindowOpened(event):
    rootContainer = event.source.getRootContainer()
    label = rootContainer.getComponent("label")
    label.text = rootContainer.prompt
 
def okActionPerformed(event):
    from ils.sfc.client.util import sendResponse
    import system.gui.getParentWindow
    # get the selected value
    textField = event.source.parent.getComponent("TextField")
    response = textField.text
    
    # send response to the Gateway
    thisWindow = system.gui.getParentWindow(event)
    sendResponse(event.source.parent.messageId, response)
    system.nav.closeWindow(thisWindow)
    
def cancelActionPerformed(event):
    from ils.sfc.client.util import sendResponse
    import system.gui.getParentWindow
    thisWindow = system.gui.getParentWindow(event)
    response = None
    sendResponse(event.source.parent.messageId, response)
    system.nav.closeWindow(thisWindow)