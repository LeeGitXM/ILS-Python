'''
Created on Mar 31, 2015

@author: Pete
'''

import system

def sendAlert(project, post, topMessage, bottomMessage, buttonLabel, callback=None, callbackPayloadDictionary=None, timeoutEnabled=False, timeoutSeconds=0):

    if callbackPayloadDictionary == None:
        callbackPayloadDataset = None
    else:
        callbackPayloadDataset=system.dataset.toDataSet(["payload"], [[callbackPayloadDictionary]])

    # Now make the payload for the OC alert window
    payload = {
        "post": post,
        "topMessage": topMessage, 
        "bottomMessage": bottomMessage, 
        "buttonLabel": buttonLabel,
        "callback": callback,
        "callbackPayloadDataset": callbackPayloadDataset,
        "timeoutEnabled": timeoutEnabled,
        "timeoutSeconds": timeoutSeconds
        }
    print "Payload: ", payload
    system.util.sendMessage(project, "ocAlert", payload, scope="C")
    
def handleMessage(payload):
    print "In ils.common.ocAlert.handleMessage()", payload
    
    targetPost=payload.get("post","")
    if targetPost != "" and targetPost != None:
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
    ds = rootContainer.callbackPayloadDataset
    if ds == None:
        payload = None
    else:
        payload=ds.getValueAt(0,0)
    
    print "Dictionary: ", payload

    if callback == "" or callback == None or callback == "None":
        system.nav.closeParentWindow(event)
        return
    
    print "Need to call: ", callback
    from ils.labData.validityLimitWarning import launcher
    launcher(payload)
    system.nav.closeParentWindow(event)
