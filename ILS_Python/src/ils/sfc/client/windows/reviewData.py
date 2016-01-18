'''
Created on Jan 14, 2015

@author: rforbes
'''

def okActionPerformed(event):
    from ils.sfc.client.windowUtil import sendWindowResponse
    from ils.sfc.common.constants import OK
    from system.gui import getParentWindow
    window = getParentWindow(event)
    sendWindowResponse(window, OK)
  
def cancelActionPerformed(event):
    from ils.sfc.client.windowUtil import sendWindowResponse
    from ils.sfc.common.constants import CANCEL
    from system.gui import getParentWindow
    window = getParentWindow(event)
    sendWindowResponse(window, CANCEL) 

def togglePrimary(window):
    primaryTable = window.getRootContainer().getComponent('primaryDataTable') 
    secondaryTable = window.getRootContainer().getComponent('secondaryDataTable') 
    tabStrip = window.getRootContainer().getComponent('tabs') 
    if tabStrip.selectedTab == "primary":
        secondaryTable.visible = False
        primaryTable.visible = True
    else:
        primaryTable.visible = False
        secondaryTable.visible = True
