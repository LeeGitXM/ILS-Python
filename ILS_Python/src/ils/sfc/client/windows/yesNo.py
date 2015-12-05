'''
Created on Dec 3, 2015

@author: rforbes
'''

import system
from ils.sfc.client.windowUtil import responseWindowClosed

def yesActionPerformed(event):
    window=system.gui.getParentWindow(event)
    sendResponse(window, "Yes")
#    system.nav.closeParentWindow(event)
  
def noActionPerformed(event):
    window=system.gui.getParentWindow(event)
    sendResponse(window, "No")
#    system.nav.closeParentWindow(event)

def timeoutActionPerformed(event):
    window=system.gui.getParentWindow(event)
    sendResponse(window, "Timeout")
#    system.nav.closeParentWindow(event)

def sendResponse(window, textResponse): 
    # I'm not sure who this message is going to - presumably the gateway handler
    from ils.sfc.client.windowUtil import responseWindowClosed 
    responseWindowClosed(window, textResponse)