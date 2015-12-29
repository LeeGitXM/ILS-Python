'''
Created on Dec 3, 2015

@author: rforbes
'''
import system.gui
from ils.sfc.client.windowUtil import sendWindowResponse

def yesActionPerformed(event):
    window=system.gui.getParentWindow(event)
    sendWindowResponse(window, "Yes")
  
def noActionPerformed(event):
    window=system.gui.getParentWindow(event)
    sendWindowResponse(window, "No")
    
