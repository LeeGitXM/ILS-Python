'''
Created on Jun 30, 2015

@author: Pete
'''
import system, string
from ils.diagToolkit.constants import RECOMMENDATION_NONE_MADE, RECOMMENDATION_NO_SIGNIFICANT_RECOMMENDATIONS, RECOMMENDATION_ERROR
from ils.common.config import getDatabaseClient, getTagProviderClient
from ils.diagToolkit.common import fetchApplicationsForPost, fetchActiveTextRecommendationsForPost
from ils.diagToolkit.setpointSpreadsheet import acknowledgeTextRecommendationProcessing
log=system.util.getLogger("com.ils.diagToolkit")

# Not sure if this is used in production, but it is needed for testing
def postDiagnosisEntry(projectName, application, family, finalDiagnosis, UUID, diagramUUID, database="", provider=""):
    log.infof("Sending a message to post a diagnosis entry...")
    payload={"application": application, "family": family, "finalDiagnosis": finalDiagnosis, "UUID": UUID, "diagramUUID": diagramUUID, "database": database, "provider":provider}
    system.util.sendMessage(projectName, "postDiagnosisEntry", payload, "G")


# This is called when the press the Setpoint Spreadsheet Button on a console.  This needs to check if we should show the setpoint
# spreadsheet, with numeric recommendations or the loud workspace with text recommendations.
def openSetpointSpreadsheetCallback(post):
    log.infof("In %s.openSetpointSpreadsheetCallback() checking what to open...", __name__)
    
    # First, see if there is a loud workspace on this window.  If there is and I decide to press the red button instead then
    # hide the loud workspace.
    openWindows = system.gui.getOpenedWindows()
    for window in openWindows:
        if window.getPath() == "Common/OC Alert":
            rootContainer = window.rootContainer
            log.infof("The window is of type: %s", rootContainer.notificationType)
            if  rootContainer.notificationType == "Setpoint Spreadsheet":
                log.infof("Found an open OC alert that I am closing")
                system.nav.closeWindow(window)

    noTextRecommendations = False
    noQuantRecommendations = False
    database=getDatabaseClient()
    provider=getTagProviderClient()

    # Check if there is a text recommendation for this post
    pds = fetchActiveTextRecommendationsForPost(post, database)
    
    if len(pds) == 1:
        log.infof("I found a single text recommendation!")
        record = pds[0]
        
        notificationText = record["TextRecommendation"]
        application = record["ApplicationName"]
        diagnosisEntryId = record["DiagnosisEntryId"]
        
        ''' The system messageBox supports <HTML> formatting!  The word wrapping is less than ideal (in my opinion), it will stretch to the width of the display, not the window, THE DISPLAY!
        I can't think of a reasaonable way to change the behavior of this.  Of course the writer of the recommendation can insert <br> tags where they make sense to make the recommendation look good.  '''        
        if notificationText.find("<HTML>") < 0:
            notificationText = "<HTML> " + notificationText
        
        # Now display the text recommendation
        log.infof("Displaying a text recommendation from %s.openSetpointSpreadsheetCallback(): %s", __name__, notificationText)
        system.gui.messageBox(notificationText, "Text Recommendation")
    
        # Once the text recommendation is acknowledged proceed to perform the standard resets
        log.infof("Proceeding to acknowledge the text recommendation...")
        acknowledgeTextRecommendationProcessing(post, application, diagnosisEntryId, database, provider)
    elif len(pds) > 1:
        log.infof("Handling multiple text recommendations (%d)...", len(pds))
        window = system.nav.openWindow("DiagToolkit/Multiple Text Recommendation Ack", {"post": post, "provider": provider})
        system.nav.centerWindow(window)
        
    else:
        log.infof("There are no text recommendations...")
        noTextRecommendations = True

    # If there is at least 1 quant recommendation for the post the open the setpoint spreadsheet
    from ils.diagToolkit.common import fetchActiveOutputsForPost
    pds = fetchActiveOutputsForPost(post, database)
    if len(pds) > 0:
        window = system.nav.openWindow('DiagToolkit/Setpoint Spreadsheet', {'post' : post})
        system.nav.centerWindow(window)
    else:
        log.infof("There are no quantitative recommendations...")
        noQuantRecommendations = True
        
    if noTextRecommendations and noQuantRecommendations:
        system.gui.messageBox("There are no recommendations pending (text or quant).", " ")


'''
The purpose of this notification handler is to handle directly opening the setpoint spreadsheet
for Rate Change specifically.
'''
def handleOpenSpreadsheetForSpecificClientNotification(payload):
    log.infof("-----------------------")
    log.infof("In %s.handleOpenSpreadsheetForSpecificClientNotification with %s", __name__, str(payload))
    
    post=payload.get("post","")
                    
    system.nav.openWindow('DiagToolkit/Setpoint Spreadsheet', {'post': post})
    system.nav.centerWindow('DiagToolkit/Setpoint Spreadsheet')


'''
The purpose of this notification handler is to open the setpoint spreadsheet on the appropriate client when there is a 
change in a FD / Recommendation.  The idea is that the gateway will send a message to all clients.  The payload of the 
message includes the console name.  If the client is responsible for the console and the setpoint spreadsheet is not 
already displayed, then display it.  There are a number of stratagies that could be used to determine if a client is 
responsible for / interested in a certain console.  The first one I will try is to check to see if the console window
is open.  (This depends on a reliable policy for keeping the console displayed)
'''
def handleNotification(payload):
    log.infof( "-----------------------")
    log.infof("In %s.handleNotification with %s",__name__, str(payload))
    
    post=payload.get('post', '')
    notificationText=payload.get('notificationText', '')
    notificationMode=payload.get('notificationMode', 'loud')
    numOutputs=payload.get('numOutputs', 1)
    callback="ils.diagToolkit.finalDiagnosisClient.postSpreadsheet"
    gatewayDatabase=payload.get("gatewayDatabase")
    clientDatabase=getDatabaseClient()
    if gatewayDatabase <> clientDatabase:
        print "Exiting handleNotification() because the gateway database does not match the client database"
        return

    windows = system.gui.getOpenedWindows()
    
    '''
    This seems like it might not be right - if console A is showing the loud workspace and a notification for console B
    comes through then it should be ignored.  I think the console should be checked first!  
    (Look at how I did it for text recommendations below)
    '''
    log.infof("Checking to see if the setpoint spreadsheet or Loud Workspace is already open...")
    for window in windows:
        windowPath=window.getPath()
        rootContainer=window.rootContainer
        
        pos = windowPath.find('Setpoint Spreadsheet')
        if pos >= 0:
            print "...found an open spreadsheet - skipping the OC alert"

            # If we found an open setpoint spreadsheet AND if there is some notification text then display it immediately 
            # since we already have the operator's attention.  One type of notification text is vector clamp advice.

            if not(notificationText in ["", "None Made", RECOMMENDATION_NONE_MADE, RECOMMENDATION_NO_SIGNIFICANT_RECOMMENDATIONS, RECOMMENDATION_ERROR]):
                system.gui.messageBox(notificationText)
            
            if numOutputs == 0:
                print "Closing an open setpoint spreadsheet because there are no outputs!"
                system.nav.closeWindow(windowPath)
                return

            # The most common reason to use "quiet" notification mode is for a recalc.
            if notificationMode == "quiet":
                # This should trigger the spreadsheet to refresh
                print "...skipping the OC alert because we are in quiet mode..."
                rootContainer.refresh=True
                return
            else:
                
                print "...found an existing setpoint spreadsheet, checking to see if it needs to be updated..."
                from ils.diagToolkit.setpointSpreadsheet import getSetpointSpreadsheetDataset
                newDs = getSetpointSpreadsheetDataset(post, clientDatabase)
                
                repeater = rootContainer.getComponent("Template Repeater")
                oldDs = repeater.templateParams
                
                '''
                If the contents that we are wishing to notify the operator about are the same as what is already in the setpoint spreadsheet then 
                there is nothing we need to do.  This was added to handle the Rate Change system where we throw up the setpoint spreadsheet immediatly and the
                normal notification comes some time later.
                '''
                if datasetsMatch(newDs, oldDs):
                    print "The datasets are the same - Aborting the notifction"
                    return
                
                print "The datasets are different, continuing with notification processing..."
                
                lastAction = rootContainer.lastAction
                print "...the last action was: ", lastAction
                
                '''
                If we found a setpoint spreadsheet and its lastAction is "noDownload" then this is the client that just pressed the NO DOWNLOAD buuton,
                so we don't need to get the OC's attention, but we do need to refresh the SS.
                '''
                if string.upper(lastAction) in ["NODOWNLOAD", "DOWNLOAD"]:
                    rootContainer.lastAction = "notified"

                    ''' Reset any applications that are in the SS, for us to get here there must have been at least one INACTIVE '''
                    from ils.diagToolkit.setpointSpreadsheet import resetAllApplicationAndOutputActions, initialize
                    resetAllApplicationAndOutputActions(rootContainer)
                    initialize(rootContainer)
                    return
                        
                else:
                    print "...closing the setpoint spreadsheet so we can regain the operator's attention..."
                    system.nav.closeWindow(windowPath)
                
        pos = windowPath.find('OC Alert')
        if pos >= 0:
            print "... checking post and payload for an OC Alert ..."
            rootContainer = window.rootContainer
            notificationType = rootContainer.getPropertyValue("notificationType")
            if post == rootContainer.getPropertyValue("post") and notificationType == "Setpoint Spreadsheet": 
                print "...found a matching OC alert..."
                
                if numOutputs == 0:
                    print "...closing an OC alert that has not been answered because the recommendations have been cleared!"
                    system.nav.closeWindow(windowPath)
                    return
                
                print "...updating the OC alert payload..."
                callbackPayloadDictionary = {"post": post, "notificationText": notificationText}
                callbackPayloadDataset=system.dataset.toDataSet(["payload"], [[callbackPayloadDictionary]])
                
                rootContainer.setPropertyValue("callbackPayloadDataset", callbackPayloadDataset)
                
                rootContainer.callback = callback
                rootContainer.mainMessage = "<HTML> Click on either the 'Pend Recc' button on the<br>Operator Console or this Acknowledge button"
                rootContainer.setPropertyValue("bottomMessage", "A New diagnosis is here!")
 
                # If there is some notification text then display it immediately since we already have
                # the operator's attention.  One type of notification text is vector clamp advice.
                
                # --- This was wrong - they need to ack the loud WS and then see the modal message ---
#                if not(notificationText in ["", "None Made", RECOMMENDATION_NONE_MADE, RECOMMENDATION_NO_SIGNIFICANT_RECOMMENDATIONS, RECOMMENDATION_ERROR]):
#                    system.gui.messageBox(notificationText)

                return
    # If we fall through the checks above, then we are going to  post the loud workspace.
    # The above checks must first determine that the alert is meant for this client

    if numOutputs == 0:
        log.infof( "Skipping the load workspace posting because the spreadsheet would be empty...")
        return
    
    # We didn't find an open setpoint spreadsheet, so post the Loud workspace
    # We don't want to open the setpoint spreadsheet immediately, rather we want to post an OC Alert,
    # the load workspace, which will get their attention.  We are already on the client that is 
    # interested, we don't have to broadcast an OC alert message, so call the message handler which opens
    # the OC alert window on this client.

    log.infof("Posting the loud workspace...")
    callbackPayloadDictionary = {"post": post, "notificationText": notificationText}
    callbackPayloadDataset=system.dataset.toDataSet(["payload"], [[callbackPayloadDictionary]])
    
    ocPayload = {
                 "post": post,
                 "topMessage": "Attention!! Attention!!", 
                 "bottomMessage": "A New diagnosis is here!", 
                 "buttonLabel": "Acknowledge",
                 "callback": callback,
                 "callbackPayloadDataset": callbackPayloadDataset,
                 "mainMessage": "<HTML> Click on either the 'Pend Recc' button on the<br>Operator Console or this Acknowledge button",
                 "timeoutEnabled": False,
                 "timeoutSeconds": 300,
                 "notificationType": "Setpoint Spreadsheet"
                 }

    # This is not the normal way to post the OC alert - normally a message is sent out to clients, but in this case 
    # we already caught a message so we are in the client            
    from ils.common.ocAlert import handleMessage
    handleMessage(ocPayload)
    

# The purpose of this notification handler is to notify the operator of a text recommendation.
# The idea is that the gateway will send a message to all clients.  The payload of the 
# message includes the console name.  If the client is responsible for the console specified then a loud workspace is 
# displayed.  There are a number of stratagies that could be used to determine if a client is 
# responsible for / interested in a certain console.  The first one I will try is to check to see if the console window
# is open.  (This depends on a reliable policy for keeping the console displayed)
def handleTextRecommendationNotification(payload):
    log.infof("-----------------------")
    log.infof("In %s.handleTextRecommendationNotification with %s", __name__, str(payload))
    
    post=payload.get('post', '')
    notificationText=payload.get('notificationText', '')
    application=payload.get('application', '')
    database=payload.get('database', '')
    provider=payload.get('provider', '')
    diagnosisEntryId=payload.get('diagnosisEntryId', '')
    
    gatewayDatabase=payload.get("gatewayDatabase")
    clientDatabase=getDatabaseClient()
    if gatewayDatabase <> clientDatabase:
        print "Exiting handleTextRecommendationNotification() because the gateway database does not match the client database"
        return

    callback="ils.diagToolkit.finalDiagnosisClient.ackTextRecommendation"
    callbackPayloadDictionary = {"post": post, "application": application, "notificationText": notificationText, "diagnosisEntryId": diagnosisEntryId, "database": database, "provider": provider}
    callbackPayloadDataset=system.dataset.toDataSet(["payload"], [[callbackPayloadDictionary]])
    
    windows = system.gui.getOpenedWindows()
    
    '''
    We are handling a text recommendation, so if there is already an open setpoint spreadsheet that has not been dealt with then
    hide it.  The diagnosis entry/recommendation that triggered it will be rescinded.
    >>> This might not be correct, what if they were equal priority??? <<<
    >>> Hopefully the gateway manager figured out the highest priorities <<<
    
    We are checking 3 different scenarios here, there shouldn't ever be two of them...
    '''
    print "Checking for an open setpoint spreadsheet..."
    for window in windows:
        windowPath=window.getPath()
        pos = windowPath.find('Setpoint Spreadsheet')
        if pos >= 0:
            rootContainer=window.rootContainer
            if post == rootContainer.post: 
                print "...closing an open setpoint spreadsheet because we have what must be a higher priority text recommendation!"
                system.nav.closeWindow(windowPath)

    print "Checking to see if the Loud Workspace is already open..."
    '''
    Not sure if I should be checking the type of the OC alert, we shouldn't let an OC alert for comms interfere with this
    '''
    for window in windows:
        windowPath=window.getPath()
        pos = windowPath.find('OC Alert')
        if pos >= 0:
            rootContainer=window.rootContainer
            if post == rootContainer.post: 
                print "...found a matching OC alert - updating its properties!"

                rootContainer.callback = callback
                rootContainer.mainMessage = "<HTML> %s" % (notificationText)
                rootContainer.callbackPayloadDataset = callbackPayloadDataset
                rootContainer.setPropertyValue("bottomMessage", "A new TEXT recommendation is ready!")
                return
    
    print "Checking if the Multiple text rec window is open..."
    for window in windows:
        windowPath=window.getPath()
        pos = windowPath.find('Multiple Text Recommendation Ack')
        if pos >= 0:
            rootContainer=window.rootContainer
            from ils.diagToolkit.multipleTextRecommendationAck import refresh
            refresh(rootContainer)
            return
    
    print "Posting the loud workspace because there wasn't already one and there wasn't a setpoint spreadsheet either..."
    
    ocPayload = {
                 "post": post,
                 "topMessage": "Attention!! Attention!!", 
                 "bottomMessage": "A new TEXT recommendation is ready!", 
                 "buttonLabel": "Acknowledge",
                 "callback": callback,
                 "callbackPayloadDataset": callbackPayloadDataset,
                 "mainMessage": "<HTML> Click on either the 'Pend Recc' button on the<br>Operator Console or this Acknowledge button",
                 "timeoutEnabled": False,
                 "timeoutSeconds": 300
                 }

    # This is not the normal way to post the OC alert - normally a message is sent out to clients, but in this case 
    # we already caught a message so we are in the client            
    from ils.common.ocAlert import handleMessage
    handleMessage(ocPayload)
    



# The purpose of this notification handler is to notify the operator of a really generic text message.
# The idea is that the gateway will send a message to all clients.  The payload of the 
# message includes the console name.  If the client is responsible for the console specified then generic
# modal message is displayed.
def handleTextNotification(payload):
    log.infof("-----------------------")
    log.infof("In %s.handleTextNotification with %s", __name__, str(payload))
    
    notificationText=payload.get('notificationText', '')
    database=payload.get('database', '')
    clientDatabase=getDatabaseClient()
    
    if database != "" and database <> clientDatabase:
        print "Exiting handleTextNotification() because the gateway database does not match the client database"
        return
    
    system.gui.messageBox(notificationText)


def ackTextRecommendation(event, payload):
    log.infof("In %s.ackTextRecommendation() ACKing a text recommendation - the payload is: %s", __name__, str(payload))
    
    post=payload.get("post", "")
    application=payload.get("application","")
    database=payload.get("database","")
    provider=payload.get("provider","")

    pds = fetchActiveTextRecommendationsForPost(post, database)
    
    # Dismiss the loud workspace
    system.nav.closeParentWindow(event)
    
    if len(pds) == 0:
        log.warnf("There are no pending text recommendations - they must have cleared since the notification was sent.")
    elif len(pds) == 1:
        log.infof("I found a single text recommendation!")
        record = pds[0]
        notificationText = record["TextRecommendation"]
        diagnosisEntryId = record["DiagnosisEntryId"]
        
        ''' The system messageBox supports <HTML> formatting!  The word wrapping is less than ideal (in my opinion), it will stretch to the width of the display, not the window, THE DISPLAY!
        I can't think of a reasaonable way to change the behavior of this.  Of course the writer of the recommendation can insert <br> tags where they make sense to make the recommendation look good.  '''        
        if notificationText.find("<HTML>") < 0:
            notificationText = "<HTML> " + notificationText
            
        log.infof("Displaying a text recommendation from %s.ackTextRecommendation(): %s", __name__, notificationText)
        system.gui.messageBox(notificationText, "Text Recommendation")
        
        # Once the text recommendation is acknowledged proceed to perform the standard resets
        log.infof("Proceeding to acknowledge the text recommendation...")
        acknowledgeTextRecommendationProcessing(post, application, diagnosisEntryId, database, provider)
    
    else:
        log.infof("Handling multiple text recommendations (%d)...", len(pds))
        window = system.nav.openWindow("DiagToolkit/Multiple Text Recommendation Ack", {"post": post, "provider": provider})
        system.nav.centerWindow(window)


# This is called when they press ???
def postSpreadsheet(event, payload):
    print "Posting the setpoint spreadsheet - the payload is: ", payload
    
    # Dismiss the loud workspace
    system.nav.closeParentWindow(event)
    
    # Open the setpoint spreadsheet
    post=payload.get("post","")
    notificationText=payload.get("notificationText","")
                    
    system.nav.openWindow('DiagToolkit/Setpoint Spreadsheet', {'post': post})
    system.nav.centerWindow('DiagToolkit/Setpoint Spreadsheet')
    
    # If there is some notification text then display it immediately.
    # One type of notification text is vector clamp advice.
    if notificationText != "":
        system.gui.messageBox(notificationText)

'''
Compare two datasets cell by cell.
'''
def datasetsMatch(oldDs, newDs):
    for row in range(oldDs.getRowCount()):
        for col in range(oldDs.getColumnCount()):
            oldVal = oldDs.getValueAt(row, col)
            newVal = newDs.getValueAt(row, col)
            if oldVal != newVal:
                return False
    return True

