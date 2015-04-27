'''
Created on Jan 15, 2015

@author: rforbes
'''
def visionWindowOpened(event):
    import system.util.jsonDecode
    rootContainer = event.source.getRootContainer()
    label = rootContainer.getComponent("label")
    label.text = rootContainer.prompt
    choices = system.util.jsonDecode(rootContainer.choices)
    headers = [""]
    choiceRows = []
    for choice in choices:
        choiceRows.append([choice])
    choicesDataset = system.dataset.toDataSet(headers, choiceRows)
    choicesCombo = rootContainer.getComponent("choices")
    choicesCombo.data = choicesDataset

def okActionPerformed(event):
    from ils.sfc.client.util import sendResponse
    import system.gui.getParentWindow
    # get the selected value
    choicesCombo = event.source.parent.getComponent("choices")
    selectedIndex = choicesCombo.selectedIndex
    if selectedIndex >= 0:
        response = choicesCombo.data.getValueAt(selectedIndex,0)
    else:
        response = None
    
    # send response to the Gateway
    thisWindow = system.gui.getParentWindow(event)
    sendResponse(event.source.parent.messageId, response)
    system.nav.closeWindow(thisWindow)
    
def cancelActionPerformed(event):
    from ils.sfc.client.util import sendResponse
    import system.gui.getParentWindow
    thisWindow = system.gui.getParentWindow(event)
    sendResponse(event.source.parent.messageId, response)
    system.nav.closeWindow(thisWindow)