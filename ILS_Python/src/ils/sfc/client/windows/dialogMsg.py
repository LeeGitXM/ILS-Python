'''
Created on Jan 5, 2016

@author: rforbes
'''

'''
Created on Jan 5, 2016

@author: rforbes
'''

def okActionPerformed(event):
    from ils.sfc.client.windowUtil import sendWindowResponse, sendCloseWindow
    import system.gui.getParentWindow
    window=system.gui.getParentWindow(event)
    rootContainer = event.source.parent
    ackRequired = rootContainer.ackRequired
    if ackRequired:
        # send a synchronous response and close the window
        sendWindowResponse(window, "Yes")
    else:
        # send async window close request, 
        sendCloseWindow(window, 'SfcDialogMessage')
