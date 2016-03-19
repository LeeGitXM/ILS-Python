'''
Created on Jun 30, 2015

@author: Pete
'''
import system

# Not sure if this is used in production, but it is needed for testing
def postDiagnosisEntry(application, family, finalDiagnosis, UUID, diagramUUID, database=""):
    print "Sending a message to post a diagnosis entry..."
    projectName=system.util.getProjectName()
    payload={"application": application, "family": family, "finalDiagnosis": finalDiagnosis, "UUID": UUID, "diagramUUID": diagramUUID, "database": database}
    system.util.sendMessage(projectName, "postDiagnosisEntry", payload, "G")


# The purpose of this notification handler is to open the setpoint spreadsheet on the appropriate client when there is a 
# change in a FD / Recommendation.  The idea is that the gateway will send a message to all clients.  The payload of the 
# message includes the console name.  If the client is responsible for the console and the setpoint spreadsheet is not 
# already displayed, then display it.  There are a number of stratagies that could be used to determine if a client is 
# responsible for / interested in a certain console.  The first one I will try is to check to see if the console window
# is open.  (This depends on a reliable policy for keeping the console displayed)
def handleNotification(payload):
    print "Handling a notification", payload
    
    post=payload.get('post', '')
    notificationText=payload.get('notificationText', '')
    
    windows = system.gui.getOpenedWindows()
    
    # First check if the setpoint spreadsheet is already open.  This does not check which console's
    # spreadsheet is open, it assumes a client can only be interested in one console.
    print "Checking to see if the setpoint spreadsheet is already open..."
    for window in windows:
        windowPath=window.getPath()
        pos = windowPath.find('Setpoint Spreadsheet')
        if pos >= 0:
            print "...found an open spreadsheet..."
            rootContainer=window.rootContainer
            rootContainer.refresh=True
            
            if notificationText != "":
                system.gui.messageBox(notificationText)
                
            return
    
    # We didn't find an open setpoint spreadsheet, so check if this client is interested in the console
    print "Checking for a matching console window..."
    for window in windows:
        windowPath=window.getPath()
        rootContainer=window.rootContainer
        windowPost=rootContainer.getPropertyValue("post")
        if post == windowPost:
            print "Found an interested console window - post the setpoint spreadsheet"
            system.nav.openWindow('DiagToolkit/Setpoint Spreadsheet', {'post': post})
            system.nav.centerWindow('DiagToolkit/Setpoint Spreadsheet')
            
            if notificationText != "":
                system.gui.messageBox(notificationText)
                
            return
    
    print "*** This client is not interested in the setpoint spreadsheet for the %s post ***" % (post)
    