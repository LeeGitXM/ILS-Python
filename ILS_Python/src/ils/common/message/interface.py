'''
Created on Sep 5, 2016

@author: ils
'''

import system, time
log=system.util.getLogger("com.ils.common.message")

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


# Use the message utility to get the first client logged in as 
def getConsoleClientIds(console, db=""):
    log.trace("%s - Looking for a client connected as: <%s>" % (__name__, console))
    SQL = "select C.windowName from TkConsole C, TkPost P where C.PostId = P.PostId and P.Post = '%s'" % (console)
    consoleWindow=system.db.runScalarQuery(SQL)
    log.trace("  ...found console window: %s" % (consoleWindow))

    clientIds = []
    windowList = listWindows()
    for record in windowList:
        windows = record["Reply"]
        if windows.find(consoleWindow) >= 0:
            clientIds.append(record["ClientId"])

    return clientIds

# Send a request to all clients to return a list of the windows that are showing
# This will run until a response is received from every connected window
def listWindows():
    log.trace("%s - Listing windows..." % (__name__))
    project = system.util.getProjectName()
    
    sessions=system.util.getSessionInfo()
    numClients=0
    for session in sessions:
        if not(session["isDesigner"]) and session["project"] == project:
            numClients+=1
    
    if numClients == 0:
        ds = system.dataset.toDataSet([], [])
        pds = system.dataset.toPyDataSet(ds)
        return pds
    
    from ils.common.message.gateway import send
    requestId=send('listWindows', project)
    
    SQL = "select Reply, ReplyTime, ClientId from TkMessageReply where RequestId = %i" % requestId
    pds = system.db.runQuery(SQL)
    while len(pds) <> numClients:
        time.sleep(1) 
        pds = system.db.runQuery(SQL)
    
    return pds