'''
Created on Jan 15, 2015

@author: rforbes
'''

def okActionPerformed(event):
    from ils.sfc.client.windowUtil import sendWindowResponse
    import system.gui.getParentWindow
    # get the selected value
    choicesCombo = event.source.parent.getComponent("choices")
    selectedIndex = choicesCombo.selectedIndex
    if selectedIndex >= 0:
        response = choicesCombo.data.getValueAt(selectedIndex,0)
    else:
        response = None
    window=system.gui.getParentWindow(event)
    sendWindowResponse(window, response)    

    
def cancelActionPerformed(event):
    from ils.sfc.client.windowUtil import sendWindowResponse
    import system.gui.getParentWindow
    window=system.gui.getParentWindow(event)
    sendWindowResponse(window, None)