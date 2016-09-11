'''
Created on Sep 5, 2016

@author: ils
'''

import system
log=system.util.getLogger("com.ils.common.message")

# Get the client ids of all clients logged in with a user name that matches a post name.
# This returns a list of client ids.
# Note: This does not use the message-reply utility because there is a system utility, getSessionInfo()
# that lists information about each client. 
def getPostClientIds(post, project="", db=""):
    log.trace("%s - Looking for a client logged in as: <%s>" % (__name__, post))

    if project == "":
        project = system.util.getProjectName()

    clientIds = []
    sessions=system.util.getSessionInfo(post)
    for session in sessions:
        if session["project"] == project:
            clientIds.append(session["clientId"])

    return clientIds


# Get the client ids of all clients that are showing the console window for a specific console.
# This returns a list of client ids 
def getConsoleClientIds(consoleName, project="", db=""):
    log.trace("%s - Looking for a client showing console: <%s>" % (__name__, consoleName))
    clientIds = []
    
    SQL = "select windowName from TkConsole where ConsoleName = '%s'" % (consoleName)
    consoleWindow=system.db.runScalarQuery(SQL, db=db)
    log.trace("  ...(console window: %s)" % (consoleWindow))

    # If we don't have a window name then we'll never find a client!
    if consoleWindow == None:
        return clientIds
    
    windowList = listWindows(project, db)
    for record in windowList:
        windows = str(record["Reply"])
        print "Windows: ", windows
        if windows <> None and windows.find(consoleWindow) >= 0:
            clientIds.append(record["ClientId"])

    return clientIds

#
# Get the client ids of all clients that are showing the console window for a specific console.
# This returns a list of client ids 
def getConsoleClientIdsForPost(post, project="", db=""):
    log.trace("%s - Looking for a client showing console for post: <%s>" % (__name__, post))
    clientIds = []
    
    SQL = "select C.WindowName from TkConsole C, TkPost P where C.PostId = P.PostId and P.Post = '%s'" % (post)
    print SQL
    consoleWindows=system.db.runQuery(SQL, db=db)
    log.trace("  ...(there are %i console windows)" % (len(consoleWindows)))

    # If we don't have a window name then we'll never find a client!
    if len(consoleWindows) == 0:
        return clientIds
    
    windowList = listWindows(project, db)
    for record in windowList:
        windows = str(record["Reply"])
        print "Windows: ", windows
        for consoleWindow in consoleWindows:
            windowName = consoleWindow["WindowName"]
            if windows <> None and windows.find(windowName) >= 0:
                clientIds.append(record["ClientId"])

    return clientIds

# Get a list of windows that are currently displayed by each client.
# This uses the message reply utility to send a request to all clients to return a list of the windows 
# that are showing. This will run until a response is received from every connected window.
# This returns a dataset with three columns: Reply, ReplyTime, ClientId.  Reply is a comma 
# separated string of the window names. 
def listWindows(project="", db=""):
    log.trace("%s - Listing windows..." % (__name__))
    if project == "":
        project = system.util.getProjectName()
    from ils.common.message.gateway import sendAndReceive
    pds=sendAndReceive('listWindows', project, db)
    
    return pds