'''
Created on Sep 5, 2016

@author: ils
'''
import system
log=system.util.getLogger("com.ils.common.message")
 
def send(requestType, project='XOM'):
    log.trace("Sending a <%s> message" % (requestType))

    messageHandler="MessageRequest"
    
    SQL = "Insert into tkMessageRequest (RequestType, RequestTime) values ('%s',  getdate())" % (requestType)
    requestId = system.db.runUpdateQuery(SQL, getKey=True)
    
    payload={"requestId": requestId, "requestType": requestType}
    system.util.sendMessage(project, messageHandler, payload, scope="C")
    
    return requestId