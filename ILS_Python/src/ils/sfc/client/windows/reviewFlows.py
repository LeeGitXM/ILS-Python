'''
Created on Sep 22, 2015

@author: rforbes
'''

def okActionPerformed(event):
    from ils.sfc.client.windowUtil import sendWindowResponse
    from ils.sfc.common.constants import VALUE, DATA, OK
    import system.gui
    window = system.gui.getParentWindow(event)
    dataTable = window.getRootContainer().getComponent("dataTable")
    payload = dict()
    payload[VALUE] = OK
    payload[DATA] = dataTable.data   
    sendWindowResponse(window, payload)

def cancelActionPerformed(event):
    from ils.sfc.client.windowUtil import sendWindowResponse
    from system.gui import getParentWindow
    from ils.sfc.common.constants import VALUE, DATA, CANCEL
    window = getParentWindow(event)
    payload = dict()
    payload[DATA] = None
    payload[VALUE] = CANCEL
    sendWindowResponse(window, payload)
