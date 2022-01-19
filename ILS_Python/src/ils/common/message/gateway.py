'''
Created on Sep 5, 2016

@author: ils
'''
import system, time
from ils.log.LogRecorder import LogRecorder
log = LogRecorder(__name__)

# Send a request to all clients to return a list of the windows that are showing
# This will run until a response is received from every connected window
def sendAndReceive(command, project, db, timeout=30):
    log.trace("%s - %s..." % (__name__, command))
    
    # Determine how many clients there are so we know how replies to wait for
    sessions=system.util.getSessionInfo()
    numClients=0
    for session in sessions:
        log.tracef("Session client id: %s, address: %s, Designer: %s, Username: %s", session["clientId"], session["address"], session["isDesigner"], session["username"])
        if not(session["isDesigner"]) and session["project"] == project:
            log.tracef("Found a client...")
            numClients+=1
    
    # If there are no clients then there won't ever be a reply
    if numClients == 0:
        log.warnf("There are no clients!")
        ds = system.dataset.toDataSet([], [])
        pds = system.dataset.toPyDataSet(ds)
        return pds

    # Send the message to the clients
    requestId=send(command, project, db)
    
    # Poll for a reply
    SQL = "select Reply, ReplyTime, ClientId, IsolationMode from TkMessageReply where RequestId = %i" % requestId
    pds = system.db.runQuery(SQL, database=db)
    startTime = system.date.now()
    timeout = system.date.addSeconds(startTime, timeout)
    
    while len(pds) <> numClients and system.date.now() < timeout:
        time.sleep(1)
        log.trace("   ...checking for %i replies..." % (numClients)) 
        pds = system.db.runQuery(SQL, database=db)
    
    if len(pds) <> numClients:
        log.trace("   ...the request timed out!")
    else:
        log.trace("   ...the replies have been received!")
    
    system.db.runUpdateQuery("delete from TkMessageRequest where RequestId = %s" % (str(requestId)), database=db)    
    
    return pds

# Send a request to all clients to return a list of the windows that are showing
# This will run until a response is received from every connected window
def sendAndReceiveToAClient(command, project, clientSessionId, db, timeout=30):
    log.trace("%s - %s..." % (__name__, command))

    # Send the message to the specific client we are interested in
    requestId=send(command, project, db, clientSessionId)
    
    # Poll for a reply
    SQL = "select Reply, ReplyTime, ClientId from TkMessageReply where RequestId = %i" % requestId
    pds = system.db.runQuery(SQL, database=db)
    startTime = system.date.now()
    timeout = system.date.addSeconds(startTime, timeout)
    
    ''' Since we only sent it to one client, we only expect one answer '''
    while len(pds) == 0 and system.date.now() < timeout:
        time.sleep(1)
        log.trace("   ...checking for a reply...") 
        pds = system.db.runQuery(SQL, database=db)
    
    if len(pds) == 0:
        log.trace("   ...request timed out!")
    else:
        log.trace("   ...the replies have been received!")

    system.db.runUpdateQuery("delete from TkMessageRequest where RequestId = %s" % (str(requestId)), database=db)
    return pds

def send(requestType, project, db, clientSessionId=""):
    log.trace("Sending a <%s> message" % (requestType))

    messageHandler="MessageRequest"
    
    SQL = "Insert into tkMessageRequest (RequestType, RequestTime) values ('%s',  getdate())" % (requestType)
    requestId = system.db.runUpdateQuery(SQL, getKey=True, database=db)
    
    payload={"requestId": requestId, "requestType": requestType, "database": db}
    
    if clientSessionId == "":
        system.util.sendMessage(project, messageHandler, payload, scope="C")
    else:
        system.util.sendMessage(project, messageHandler, payload, scope="C", clientSessionId=clientSessionId)

    return requestId

''' 
This is a generic way to open a window on a client from gateway scope or from one client to another, although that is not common. 
Normally we specify the console or the post, but not both.
'''
def openWindow(window, payload={}, position="center", scale=1.0, post="", console="", project=""):
    messageHandler="openWindow"
    messagePayload = {"console":console, "post":post, "window":window, "windowPayload":payload, "position": position, "scale":scale}
    system.util.sendMessage(project, messageHandler, messagePayload, scope="C")
    

    
        