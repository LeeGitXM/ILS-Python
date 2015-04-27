'''
Created on Mar 31, 2015

@author: Pete
'''

import system

def handleMessage(payload):
    print "In ils.common.ocAlert.handleMessage()", payload
    
    targetPost=payload.get("post","")
    if targetPost != "":
        post = system.tag.read("[Client]Post").value
        if targetPost == post:
            system.nav.openWindowInstance("Common/OC Alert", payload)
        else:
            print "Skipping this OC alert because it was destined for a different post"
    else:
        system.nav.openWindowInstance("Common/OC Alert", payload)


# This is called from the button smack in the middle of the screen 
def buttonHandler(event):
    print "In the button handler..."
    rootContainer = event.source.parent
    callback=rootContainer.callback
    
    # The payload is a dataset
    ds = rootContainer.ds
    payload=ds.getValueAt(0,0)
    
    print "Dictionary: ", payload

    if callback == "" or callback == None or callback == "None":
        system.nav.closeParentWindow(event)
        return
    
    print "Need to call: ", callback
    from ils.labData.validityLimitWarning import launcher
    launcher(payload)
    system.nav.closeParentWindow(event)
