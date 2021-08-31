'''
Created on Dec 27, 2018

@author: phass
'''
import system
from ils.common.database import getConsoleWindowNameForPost
from ils.common.config import getDatabaseClient
from ils.log.LogRecorder import LogRecorder
log = LogRecorder(__name__)

def uirNotify(project, post, windowName, windowPayload):
    ''' Generally, creating a UIR is launched from a client, however, the diagnostic toolkit has the capability of launching a UIR.
        Since the diagnostic toolkit runs in the gateway, this function handles notifying clients. '''
    message = "uirNotify"
    payload = {
        "windowName": windowName,
        "post": post,
        "windowPayload": windowPayload
        }
    
    log.infof("In %s.uirNotify(), Sending <%s> message to project: <%s>, post: <%s>, payload: <%s>", __name__, str(message), str(project), str(post), str(payload))
    
    system.util.sendMessage(project, messageHandler=message, payload=payload, scope="C")
    
def uirHide(project, post, windowName, windowPayload):
    ''' This is called from a client, when a UIR that has been automatically created by the Diag Toolkit and shown to all of the interested clients.
        This implements the rule that the first response wins.  When the diagtoolkit automatically creates a UIR it creates the database record, then 
        if the operator presses 'Cancel' it is deleted from the DB.  If they press 'Save' then it is e-mailed to the world.  We do NOT want to provide the 
        operator the option of closing the UIR with any other option (i.e., just a X close button).  If multiple clients are connected and both showing the 
        UIR we only want the first response. [IA messages are really fast, I don't think we need worry about simultaneous transactions]'''
    message = "uirNotify"
    payload = {
        "windowName": windowName,
        "post": post,
        "windowPayload": windowPayload
        }
    
    log.infof("In %s.uirNotify(), Sending <%s> message to project: <%s>, post: <%s>, payload: <%s>", __name__, str(message), str(project), str(post), str(payload))
    
    system.util.sendMessage(project, messageHandler=message, payload=payload, scope="C")
    
def uirNotifyHandler(payload):
    '''This runs in a client when it receives a uirNotify message.  It determines if the window should be opened based on the console window for the specified post being open. '''

    print "In %s.uirNotifyHandler() - payload: %s" % (__name__, str(payload))
    db = getDatabaseClient()
    windowName = payload["windowName"]
    post = payload["post"]
    consoleWindowName = getConsoleWindowNameForPost(post, db)
    windowPayload = payload["windowPayload"]
    
    print "Checking for console window named: %s" % (consoleWindowName) 
    windows = system.gui.getOpenedWindows()
    found = False
    for window in windows:
        if window.getPath() == consoleWindowName:
            found = True
    
    if found:       
        system.nav.openWindow(windowName, windowPayload)
    else:
        print "Ignoring the notification because the console for %s is not open" % (post)