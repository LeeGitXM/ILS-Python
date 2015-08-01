'''
Created on Mar 31, 2015

@author: Pete
'''

import system, string, sys, traceback

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
# This runs in the client, so don't bother with loggers, just print debug messages...
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
    
    # If they specify shared or project scope, then we don't need to do this
    if not(string.find(callback, "project") == 0 or string.find(callback, "shared") == 0):
        # The method contains a full python path, including the package, module, and function name
        separator=string.rfind(callback, ".")
        packagemodule=callback[0:separator]
        separator=string.rfind(packagemodule, ".")
        package = packagemodule[0:separator]
        module  = packagemodule[separator+1:]
        print "Using External Python, the package is: <%s>.<%s>" % (package,module)
        exec("import %s" % (package))
        exec("from %s import %s" % (package,module))
        
    try:
        print "Calling validation procedure %s..." % (callback)
        eval(callback)(event, payload)
        print "   ...back from the callback!"
                
    except:
        errorType,value,trace = sys.exc_info()
        errorTxt = traceback.format_exception(errorType, value, trace, 1000)
        print"Caught an exception calling callback... \n%s" % (errorTxt)
