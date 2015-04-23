'''
Created on Mar 31, 2015

@author: Pete
'''

import system

def handleMessage(payload):
    print "In ils.common.ocAlert.handleMessage()"
    
    ds = payload.get("dataset")
    payload=ds.getValueAt(0,0)
    print "Dictionary: ", payload
    
    buttonLabel=payload.get("buttonLabel", "Acknowledge")
    topMessage=payload.get("topMessage", "")
    bottomMessage=payload.get("bottomMessage", "")
    
    win=system.nav.openWindowInstance("Common/OC Alert", {"topMessage":topMessage, "bottomMessage": bottomMessage, "buttonLabel": buttonLabel, "payload":ds})
    
    # For some reason this centerWindow command doesn't do anything so I had to add it to the internalFrameOpened script as well
    system.nav.centerWindow(win)
    print "Opened Window"

# This is called from the button smack in the middle of the screen 
def buttonHandler(event):
    rootContainer = event.source.parent
    
    # The payload is a dataset
    ds = rootContainer.payload
    payload=ds.getValueAt(0,0)
    
    print payload

    callback=payload.get("callback", None)
    if callback == None:
        system.nav.closeParentWindow(event)
        return
    
    print "Need to call: ", callback
    from ils.labData.validityLimitWarning import launcher
    launcher(payload)
    system.nav.closeParentWindow(event)
    
    
    
    
