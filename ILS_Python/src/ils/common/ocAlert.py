'''
Created on Mar 31, 2015

@author: Pete
'''

import system, string, sys, traceback
from ils.common.notification import notifyError
from ils.common.config import getIsolationModeClient, getTagProvider
from ils.sfc.common.constants import CLIENT_DONE
from ils.log.LogRecorder import LogRecorder
logger = LogRecorder(__name__)

# This is generally called from the gateway, but will also work when called from test (like from the test window)
def sendAlert(project, post, topMessage, bottomMessage, mainMessage, buttonLabel, callback=None, 
              callbackPayloadDictionary=None, timeoutEnabled=False, timeoutSeconds=0, db="", isolationMode=False, windowName=""):
    logger.trace("In %s.sendAlert() to post: %s (Isolation: %s)" % (__name__, post, isolationMode))
    
    if callbackPayloadDictionary == None:
        callbackPayloadDataset = None
    else:
        callbackPayloadDataset=system.dataset.toDataSet(["payload"], [[callbackPayloadDictionary]])
        
    print "Main Message: ", mainMessage

    # Now make the payload for the OC alert window
    payload = {
        "post": post,
        "windowName": windowName,
        "topMessage": "<HTML>" + topMessage, 
        "bottomMessage": "<HTML>" + bottomMessage, 
        "mainMessage": "<HTML>" + mainMessage,
        "buttonLabel": buttonLabel,
        "callback": callback,
        "callbackPayloadDataset": callbackPayloadDataset,
        "timeoutEnabled": timeoutEnabled,
        "timeoutSeconds": timeoutSeconds,
        "isolationMode": isolationMode
        }

    logger.tracef("Payload: %s", str(payload))
    message = "ocAlert"
    notifyError(project, message, payload, post, db, isolationMode)
    
    ''' 
    If the site has specified a custom alert callback, now is the time to call it.  A good thing to do here is to maximize the OC Ignition client. 
    ''' 
    provider = getTagProvider()
    callback = system.tag.read("[%s]Configuration/Common/ocAlertCallback" % (provider)).value
    if callback not in ["", None, "None"]:
        logger.tracef("Calling a callback...")
        ocAlertCallback(callback, payload)
        
        
def ocAlertCallback(callback, payload):
    # If they specify shared or project scope, then we don't need to do this
    logger.tracef("In ocAlertCallback")
    if callback not in ["", None] and (not(string.find(callback, "project") == 0 or string.find(callback, "shared") == 0)):
        # The method contains a full python path, including the method name
        try:
            separator=string.rfind(callback, ".")
            packagemodule=callback[0:separator]
            separator=string.rfind(packagemodule, ".")
            package = packagemodule[0:separator]
            module  = packagemodule[separator+1:]
            logger.tracef("   ...using External Python, the package is: <%s>.<%s>", package,module)
            exec("import %s" % (package))
            exec("from %s import %s" % (package,module))
        except:
            errorType,value,trace = sys.exc_info()
            errorTxt = str(traceback.format_exception(errorType, value, trace, 500))
            logger.errorf("Caught an exception importing an external reference method named %s %s", str(callback), errorTxt)
            return [], errorTxt, "ERROR"
        else:
            logger.tracef("...import of external reference was successful...")
            
    try:
        if callback not in ["", None]:
            logger.tracef("...making the call...")
            eval(callback)(payload)
            logger.tracef("...back from the OC alert callback!")
    except:
        logger.error("Error calling the OC alert callback")
    

# This runs in a client and is called when the OC alert message is sent to every client.  The first
# step is to sort out if THIS client is meant to display the OC alert.  OC alerts are sent to a post,
# which corresponds to a username.  So if the OC alert is sent to post XO1RLA3 and the [Client]Post
# tag is XO1RLA3, then the OC alert should be displayed.  A second client that should receive the
# OC alert is if the client has the console open for the post.  This is applicable to an AE that 
# is shadowing a console from his office.  All he would need to do is open the RLA3 console and
# he will receive the OC alerts for the XO1RLA3 post.
# Alas, if they did not provide a post in the payload then display the alert everywhere.  
def handleMessage(payload):
    logger.trace("In %s.handleMessage() - payload: %s" % (__name__, str(payload)))
    
    '''
    This is a hack.  We have a common notifyError API that implements so good logic to figure out if a window should be shown on a client.
    For some reason it adds "showOverride" to the payload.  It is no longer obvious who uses this property, but it throws an error
    for the OC alert. 
    '''
    if payload.has_key('showOverride'):
        del payload['showOverride']
    
    if payload.has_key('isolationMode'):
        messageIsolationMode = payload["isolationMode"]
        clientIsolationMode = getIsolationModeClient()
        print "**************************************************"
        print "Client Isolation Mode:  ", clientIsolationMode
        print "Message Isolation Mode: ", messageIsolationMode
        print "**************************************************"
        if messageIsolationMode <> clientIsolationMode:
            print "Ignoring the message because the isolation mode of the message does not match the isolation mode of the client"
            return
        
        del payload['isolationMode']

    windowName = payload["windowName"]
    del payload['windowName']
    if windowName in ["", None]:
        windowName = "Common/OC Alert"
    
    system.nav.openWindowInstance("Common/OC Alert", payload)
    

def buttonHandler(event):
    '''
    This is called from the button smack in the middle of the screen.
    '''
    logger.trace("In %s..." % (__name__))
    rootContainer = event.source.parent
    callback=rootContainer.callback
    
    # The payload is a dataset
    ds = rootContainer.callbackPayloadDataset
    if ds == None:
        payload = None
    else:
        payload=ds.getValueAt(0,0)
    
    logger.trace("Dictionary: %s" % (str(payload)))

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
        logger.trace("Using External Python, the package is: <%s>.<%s>" % (package,module))
        exec("import %s" % (package))
        exec("from %s import %s" % (package,module))
        
    try:
        logger.trace("Calling custom callback procedure %s..." % (callback))
        eval(callback)(event, payload)
        logger.trace("   ...back from the callback!")
                
    except:
        errorType,value,trace = sys.exc_info()
        errorTxt = traceback.format_exception(errorType, value, trace, 1000)
        logger.trace("Caught an exception calling callback... \n%s" % (errorTxt))


def sfcHandshake(event, payload):
    '''
    When the OC Alert is called from the SFC built in step this is automatically called.  
    '''
    chartId = str(payload.get("chartId", "-1"))
    stepId = str(payload.get("stepId", "-1"))

    system.sfc.setVariable(chartId, stepId, str(CLIENT_DONE), True)
    system.nav.closeParentWindow(event)
    
# This is a callback from the Acknowledge button in the middle of the loud workspace.
def testCallback(event, payload):
    system.nav.closeParentWindow(event)    
    system.gui.messageBox("Hello - this is from the custom callback!")
