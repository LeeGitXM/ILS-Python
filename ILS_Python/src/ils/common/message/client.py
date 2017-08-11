'''
Created on Sep 5, 2016

@author: ils
'''
import system
from ils.common.config import getDatabaseClient

def handle(payload):
    print "Received a message with payload: ", payload
    
    requestId = payload.get("requestId", -1)
    requestType = payload.get("requestType", "unknown")
    clientId = system.util.getClientId()
    
    # Get a list of all of the open windows on a client
    if requestType == "listWindows":
        db = getDatabaseClient()
        windows=system.gui.getOpenedWindowNames()
        reply = ",".join(map(str,windows))
        SQL = "Insert into TkMessageReply (RequestId, Reply, ReplyTime, ClientId)"\
            " values (%i, '%s', getdate(), '%s')"\
             % (requestId, reply, clientId)
        system.db.runUpdateQuery(SQL, database=db)