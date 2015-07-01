'''
Created on Jun 30, 2015

@author: Pete
'''
import system

# Not sure if this is used in production, but it is neded for testing
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
    
    console=payload.get('console', '')
    notificationText=payload.get('notificationText', '')
    print "Notification Text: <%s>" % (notificationText)
    windows = system.gui.getOpenedWindows()
    
    # First check if the setpoint spreadsheet is already open.  This does not check which console's
    # spreadsheet is open, it assumes a client can only be interested in one console.
    for window in windows:
        windowPath=window.getPath()
        pos = windowPath.find('Setpoint Spreadsheet')
        if pos >= 0:
            print "The spreadsheet is already open!"
            rootContainer=window.rootContainer
            rootContainer.refresh=True
            
            if notificationText != "":
                system.gui.messageBox(notificationText, "Vector Clamp Advice")
                
            return
    
    # We didn't find an open setpoint spreadsheet, so check if this client is interested in the console
    for window in windows:
        windowPath=window.getPath()
        pos = windowPath.find(console)
        if pos >= 0:
            print "Found an interested window - post the setpoint spreadsheet"
            system.nav.openWindow('DiagToolkit/Setpoint Spreadsheet', {'console': console})
            system.nav.centerWindow('DiagToolkit/Setpoint Spreadsheet')
            
            if notificationText != "":
                system.gui.messageBox(notificationText, "Vector Clamp Advice")
                
            return