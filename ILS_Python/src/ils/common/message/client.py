'''
Created on Sep 5, 2016

@author: ils

'''
import system, string
from ils.common.config import getDatabaseClient, getIsolationModeClient
from ils.common.windowUtil import positionWindow
from ils.common.database import getConsoleWindowNameForConsole
from ils.log.LogRecorder import LogRecorder
log = LogRecorder(__name__)

def handle(payload):
    print "Received a message with payload: ", payload
    
    requestId = payload.get("requestId", -1)
    requestType = payload.get("requestType", "unknown")
    requestDatabase = payload.get("database", "")
    clientId = system.util.getClientId()
    
    # Get a list of all of the open windows on a client
    if requestType == "listWindows":
        isolationMode = system.tag.read("[Client]Isolation Mode").value
        windows=system.gui.getOpenedWindowNames()
        reply = ",".join(map(str,windows))
        SQL = "Insert into TkMessageReply (RequestId, Reply, ReplyTime, ClientId, IsolationMode)"\
            " values (%i, '%s', getdate(), '%s', %d)"\
             % (requestId, reply, clientId, isolationMode)
        print SQL
        system.db.runUpdateQuery(SQL, database=requestDatabase)
        
    elif requestType == "listUserAndIsolationMode":
        isolationMode = system.tag.read("[Client]Isolation Mode").value
        username = system.tag.read("[System]Client/User/Username").value
        SQL = "Insert into TkMessageReply (RequestId, Reply, ReplyTime, ClientId, IsolationMode)"\
            " values (%i, '%s', getdate(), '%s', %d)"\
             % (requestId, username, clientId, isolationMode)
        print SQL
        system.db.runUpdateQuery(SQL, database=requestDatabase)
    
    else:
        print "Unexpected request type: <%s>" % (requestType)
        
    print "...done handling the message request..."

def openWindow(payload):
    print "Opening:", payload
    console = payload.get("console", "")
    post = payload.get("post", "")
    window = payload["window"]
    position = payload.get("position", "center")
    scale = payload.get("scale", 1.0)
    windowPayload = payload.get("windowPayload", {})
        
    if console == "" and post == "":
        print "Showing the window because neither the post or console were specified"
        window = system.nav.openWindow(window, windowPayload)
        positionWindow(window, position, scale)
    elif console != "" and consoleMatch(console):
        print "The console Matches..."
        window = system.nav.openWindow(window, windowPayload)
        positionWindow(window, position, scale)
    elif post != "" and postMatch(post):
        print "The post Matches..."
        window = system.nav.openWindow(window, windowPayload)
        positionWindow(window, position, scale)
    else:
        print "Ignoring the request to show the window!"


def sendCloseWindowMessage(projectName, windowName, isolationMode, payload):
    print "Sending to %s... " % (projectName)
    payload["window"] = windowName
    payload["isolationMode"] = isolationMode
    print "Payload: ", payload
    system.util.sendMessage(project=projectName, messageHandler="closeWindow", payload=payload, scope="C")

def closeWindowHandler(payload):
    '''
    This message goes to every client.
    If the window is open and the isolation mode matches and any addition rootcontainer properties match, then close it.  
    '''
    print "Closing:", payload
    isolationMode = payload["isolationMode"]
    if isolationMode != getIsolationModeClient():
        print "--- exiting because the isolation mode does not match ---"
        return
    
    window = payload["window"]
        
    print "Hiding window: ", window
    system.nav.closeWindow(window)    

def consoleMatch(consoleName):
    '''
    Determine if this client is the console.  There are two slightly different ways that we could do this.  I could look at the usernames or
    or I could look to see if the console window is open.  These are generally one in the same, but the latter approach makes it easier to test because
    all I need to do is open a console and then I am the operatoe.  It might also help an AE who wants to see what an operator sees.
    '''
    if consoleName == "":
        return False

    consoleWindowName = getConsoleWindowNameForConsole(consoleName)
    print "Checking if <%s> is open..." % (consoleWindowName)
    
    windowNames = system.gui.getOpenedWindowNames()
    for windowName in windowNames:
        print "Checking: ", windowName
        if windowName == consoleWindowName:
            print "Found the console window so open this window..."
            return True
    return False

'''
This uses the convention that the post is the same as the username.  So read the system client tag for the username and see if that matches the requested post
'''
def postMatch(post):
    if post == "":
        return False
    print "Checking post:", post
    username = system.tag.read("[System]Client/User/Username").value
    print "Username: ", username
    if string.upper(username) == string.upper(post):
        print "The post matches the username so show the window."
        return True
    return False
