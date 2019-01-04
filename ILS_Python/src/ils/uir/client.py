'''
Created on Dec 27, 2018

@author: phass
'''
import system
from ils.common.database import getConsoleWindowNameForPost
from ils.common.config import getDatabaseClient

log = system.util.getLogger("ils.uir")

def uirNotify(project, post, windowName, windowPayload):
    ''' Generally, creating a UIR is launched from a client, however, the diagnostic toolkit has the capability of launching a UIR.
        Since the diagnostic toolkit runs in the gateway, this function handles notifying clients. '''
    message = "uirNotify"
    payload = {
        "windowName": windowName,
        "post": post,
        "windowPayload": windowPayload
        }
    
    log.tracef("In %s.uirNotify(), Sending <%s> message to project: <%s>, post: <%s>, payload: <%s>", __name__, str(message), str(project), str(post), str(payload))
    
    system.util.sendMessage(project, messageHandler=message, payload=payload, scope="C")
    
def uirNotifyHandler(payload):
    '''This runs in a client when it receives a uirNotify message.  It determines if the window should be opened based on the console window for the specified post being open. '''
    
    log.infof("In uirNotifyHandler() - payload: %s", str(payload))
    db = getDatabaseClient()
    windowName = payload["windowName"]
    post = payload["post"]
    consoleWindowName = getConsoleWindowNameForPost(post, db)
    windowPayload = payload["windowPayload"]
    
    log.infof("Checking for console window named: %s", consoleWindowName) 
    windows = system.gui.getOpenedWindows()
    found = False
    for window in windows:
        if window.getPath() == consoleWindowName:
            found = True
    
    if found:       
        system.nav.openWindow(windowName, windowPayload)
    else:
        log.infof("Ignoring the notification because the console for %s is not open" % (post))