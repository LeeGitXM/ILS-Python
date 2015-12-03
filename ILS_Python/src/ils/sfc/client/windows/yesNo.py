'''
Created on Dec 3, 2015

@author: rforbes
'''

import system

def yesActionPerformed(event):
    rootContainer=event.source.parent
    messageId=rootContainer.messageId
    sendResponse(messageId, "Yes")
    system.nav.closeParentWindow(event)
  
def noActionPerformed(event):
    rootContainer=event.source.parent
    messageId=rootContainer.messageId
    sendResponse(messageId, "No")
    system.nav.closeParentWindow(event)

def timeoutActionPerformed(event):
    rootContainer=event.source.parent
    messageId=rootContainer.messageId
    sendResponse(messageId, "Timeout")
    system.nav.closeParentWindow(event)

def sendResponse(messageId, textResponse): 
    # I'm not sure who this message is going to - presumably the gateway handler
    from ils.sfc.client.util import sendResponse 
    sendResponse(messageId, textResponse)