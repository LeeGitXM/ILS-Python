'''
Created on Sep 5, 2016

@author: ils
'''
import system, time
log=system.util.getLogger("com.ils.common.message")

# Send a request to all clients to return a list of the windows that are showing
# This will run until a response is received from every connected window
def sendAndReceive(command, project, db, timeout=30):
    log.trace("%s - %s..." % (__name__, command))
    
    # Determine how many clients there are so we know how replies to wait for
    sessions=system.util.getSessionInfo()
    numClients=0
    for session in sessions:
        if not(session["isDesigner"]) and session["project"] == project:
            numClients+=1
    
    # If there are no clients then there won't ever be a reply
    if numClients == 0:
        ds = system.dataset.toDataSet([], [])
        pds = system.dataset.toPyDataSet(ds)
        return pds

    # Send the message to the clients
    requestId=send(command, project, db)
    
    # Poll for a reply
    SQL = "select Reply, ReplyTime, ClientId from TkMessageReply where RequestId = %i" % requestId
    pds = system.db.runQuery(SQL, database=db)
    startTime = system.date.now()
    timeout = system.date.addSeconds(startTime, timeout)
    
    while len(pds) <> numClients and system.date.now() < timeout:
        time.sleep(1)
        log.trace("   ..checking for %i replies..." % (numClients)) 
        pds = system.db.runQuery(SQL, database=db)
    
    log.trace("   ...the replies have been received!")
    return pds

def send(requestType, project, db):
    log.trace("Sending a <%s> message" % (requestType))

    messageHandler="MessageRequest"
    
    SQL = "Insert into tkMessageRequest (RequestType, RequestTime) values ('%s',  getdate())" % (requestType)
    requestId = system.db.runUpdateQuery(SQL, getKey=True, database=db)
    
    payload={"requestId": requestId, "requestType": requestType}
    system.util.sendMessage(project, messageHandler, payload, scope="C")
    
    return requestId