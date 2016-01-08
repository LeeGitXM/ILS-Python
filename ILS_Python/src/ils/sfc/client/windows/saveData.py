'''
Created on Jan 8, 2016

@author: rforbes
'''

def okActionPerformed(event):
    from ils.sfc.client.windowUtil import sendCloseWindow
    import system.gui
    window = system.gui.getParentWindow(event)
    sendCloseWindow(window, 'SfcSaveData')