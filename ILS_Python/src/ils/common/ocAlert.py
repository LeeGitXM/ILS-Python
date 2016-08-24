'''
Created on Mar 31, 2015

@author: Pete
'''

import system, string, sys, traceback

def sendAlert(project, post, topMessage, bottomMessage, mainMessage, buttonLabel, callback=None, 
              callbackPayloadDictionary=None, timeoutEnabled=False, timeoutSeconds=0):

    if callbackPayloadDictionary == None:
        callbackPayloadDataset = None
    else:
        callbackPayloadDataset=system.dataset.toDataSet(["payload"], [[callbackPayloadDictionary]])

    # Now make the payload for the OC alert window
    payload = {
        "post": post,
        "topMessage": topMessage, 
        "bottomMessage": bottomMessage, 
        "mainMessage": mainMessage,
        "buttonLabel": buttonLabel,
        "callback": callback,
        "callbackPayloadDataset": callbackPayloadDataset,
        "timeoutEnabled": timeoutEnabled,
        "timeoutSeconds": timeoutSeconds
        }
    print "Payload: ", payload
    system.util.sendMessage(project, "ocAlert", payload, scope="C")

# This runs in a client and is called when the OC alert message is sent to every client.  The first
# step is to sort out if THIS client is meant to display the OC alert.  OC alerts are sent to a post,
# which corresponds to a username.  So if the OC alert is sent to post XO1RLA3 and the [Client]Post
# tag is XO1RLA3, then the OC alert should be displayed.  A second client that should receive the
# OC alert is if the client has the console open for the post.  This is applicable to an AE that 
# is shadowing a console from his office.  All he would need to do is open the RLA3 console and
# he will receive the OC alerts for the XO1RLA3 post.
# Alas, if they did not provide a post in the payload then display the alert everywhere.  
def handleMessage(payload):
    print "In ils.common.ocAlert.handleMessage()", payload
    
    targetPost=payload.get("post","")
    if targetPost != "" and targetPost != None:
        post = system.tag.read("[Client]Post").value
        if targetPost == post:
            system.nav.openWindowInstance("Common/OC Alert", payload)
        else:
            windows = system.gui.getOpenedWindows()
            print 'There are %d windows open' % len(windows)
            found=False
            for window in windows:
                windowPath=string.upper(window.getPath())
                print windowPath
                if windowPath.find("CONSOLE") >= 0:
                    if window.getRootContainer().getPropertyValue('post') == targetPost:
                        system.nav.openWindowInstance("Common/OC Alert", payload)
                        found=True
            if not(found):
                print "Skipping this OC alert because it was destined for a different post"
    else:
        system.nav.openWindowInstance("Common/OC Alert", payload)


# This is called from the button smack in the middle of the screen 
# This runs in the client, so don't bother with loggers, just print debug messages...
def buttonHandler(event):
    print "In %s..." % (__name__)
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
        print "Calling custom callback procedure %s..." % (callback)
        eval(callback)(event, payload)
        print "   ...back from the callback!"
                
    except:
        errorType,value,trace = sys.exc_info()
        errorTxt = traceback.format_exception(errorType, value, trace, 1000)
        print"Caught an exception calling callback... \n%s" % (errorTxt)


# This is a callback from the Acknowledge button in the middle of the loud workspace.
def testCallback(event, payload):
    system.nav.closeParentWindow(event)    
    system.gui.messageBox("Hello - this is from the custom callback!")
