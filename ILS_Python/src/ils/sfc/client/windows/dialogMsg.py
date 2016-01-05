'''
Created on Jan 5, 2016

@author: rforbes
'''

'''
Created on Jan 5, 2016

@author: rforbes
'''

def okActionPerformed(event):
    from ils.sfc.client.windowUtil import sendWindowResponse
    import system.gui.getParentWindow
    window=system.gui.getParentWindow(event)
    sendWindowResponse(window, "Yes")