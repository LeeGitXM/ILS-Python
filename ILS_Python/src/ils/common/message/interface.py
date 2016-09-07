'''
Created on Sep 5, 2016

@author: ils
'''

import system, time

def isConsoleShowing(console):
    clientId = False
    windowList = listWindows()
    for record in windowList:
        windows = record["Reply"]
        clientId = record["ClientId"]
        
    return clientId

# Send a request to all clients to return a list of the windows that are showing
# This will run until a response is received from every connected window
def listWindows():
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
    
    SQL = "select * from TkMessageReply where RequestId = %i" % requestId
    pds = system.db.runQuery(SQL)
    while len(pds) <> numClients:
        time.sleep(1)
        print "fetching..." 
        pds = system.db.runQuery(SQL)
    
    return pds