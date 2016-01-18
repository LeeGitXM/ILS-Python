'''
Created on Dec 3, 2015

@author: rforbes
'''
import system.gui
from ils.sfc.client.windowUtil import sendWindowResponse
from ils.sfc.common.constants import YES_RESPONSE, NO_RESPONSE

def yesActionPerformed(event):
    window=system.gui.getParentWindow(event)
    sendWindowResponse(window, YES_RESPONSE)
  
def noActionPerformed(event):
    window=system.gui.getParentWindow(event)
    sendWindowResponse(window, NO_RESPONSE)
    
