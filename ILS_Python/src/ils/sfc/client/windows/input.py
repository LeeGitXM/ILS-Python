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
    payload = dict()
    payload['messageId'] = event.source.parent.messageId
    payload['response'] = response
    sendResponse(payload, response)
    system.nav.closeWindow(thisWindow)
    
def cancelActionPerformed(event):
    from ils.sfc.client.util import sendResponse
    import system.gui.getParentWindow
    thisWindow = system.gui.getParentWindow(event)
    payload = dict()
    payload['messageId'] = event.source.parent.messageId
    response = None
    sendResponse(payload, response)
    system.nav.closeWindow(thisWindow)