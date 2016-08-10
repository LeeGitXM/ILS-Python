'''
Created on Jun 30, 2015

@author: Pete
'''
import system
from ils.constants.constants import RECOMMENDATION_NONE_MADE, RECOMMENDATION_NO_SIGNIFICANT_RECOMMENDATIONS, RECOMMENDATION_ERROR
from ils.sfc.common.constants import DATABASE

# Not sure if this is used in production, but it is needed for testing
def postDiagnosisEntry(application, family, finalDiagnosis, UUID, diagramUUID, database=""):
    print "Sending a message to post a diagnosis entry..."
    projectName=system.util.getProjectName()
    payload={"application": application, "family": family, "finalDiagnosis": finalDiagnosis, "UUID": UUID, "diagramUUID": diagramUUID, "database": database}
    system.util.sendMessage(projectName, "postDiagnosisEntry", payload, "G")


# This is called when the press the Setpoint Spreadsheet Button on a console.  This needs to check if we should show the setpoint
# spreadsheet, with numeric recommendations, or the loud workspace with text recommendations.
def openSetpointSpreadsheetCallback(post):
    print "Checking what to open..."
    window = system.nav.openWindow('DiagToolkit/Setpoint Spreadsheet', {'post' : post})
    system.nav.centerWindow(window)


# The purpose of this notification handler is to open the setpoint spreadsheet on the appropriate client when there is a 
# change in a FD / Recommendation.  The idea is that the gateway will send a message to all clients.  The payload of the 
# message includes the console name.  If the client is responsible for the console and the setpoint spreadsheet is not 
# already displayed, then display it.  There are a number of stratagies that could be used to determine if a client is 
# responsible for / interested in a certain console.  The first one I will try is to check to see if the console window
# is open.  (This depends on a reliable policy for keeping the console displayed)
def handleNotification(payload):
    print "-----------------------"
    print "In %s.handleNotification with %s" % (__name__, str(payload))
    
    post=payload.get('post', '')
    notificationText=payload.get('notificationText', '')
    numOutputs=payload.get('numOutputs', 1)

    windows = system.gui.getOpenedWindows()
    
    # First check if the setpoint spreadsheet is already open.  This does not check which console's
    # spreadsheet is open, it assumes a client can only be interested in one console.
    print "Checking to see if the setpoint spreadsheet or Loud Workspace is already open..."
    for window in windows:
        windowPath=window.getPath()
        
        pos = windowPath.find('Setpoint Spreadsheet')
        if pos >= 0:
            print "...found an open spreadsheet - skipping the OC alert"
            rootContainer=window.rootContainer
            
            # This should trigger the spreadsheet to refresh
            rootContainer.refresh=True
            
            # If there is some notification text then display it immediately since we already have
            # the operator's attention.  One type of notification text is vector clamp advice.
            if not(notificationText in ["", "None Made", RECOMMENDATION_NONE_MADE, RECOMMENDATION_NO_SIGNIFICANT_RECOMMENDATIONS, RECOMMENDATION_ERROR]):
                system.gui.messageBox(notificationText)
            
            if numOutputs == 0:
                print "Closing an open setpoint spreadsheet because there are no outputs!"
                system.nav.closeWindow(windowPath)

            return

        pos = windowPath.find('OC Alert')
        if pos >= 0:
            print "... checking post and payload for an OC Alert ..."
            rootContainer=window.rootContainer
            if post == rootContainer.post: 
                print "...found a matching OC alert - skipping the OC alert!"
                
                # If there is some notification text then display it immediately since we already have
                # the operator's attention.  One type of notification text is vector clamp advice.
                if not(notificationText in ["", "None Made", RECOMMENDATION_NONE_MADE, RECOMMENDATION_NO_SIGNIFICANT_RECOMMENDATIONS, RECOMMENDATION_ERROR]):
                    system.gui.messageBox(notificationText)
                
                if numOutputs == 0:
                    print "Closing an OC alert that has not been answered because the recommendations have been cleared"
                    system.nav.closeWindow(windowPath)
                return
    
    # We didn't find an open setpoint spreadsheet, so if there are outputs check if this client is interested in the console
    print "Checking for a matching console window..."
    for window in windows:
        windowPath=window.getPath()
        rootContainer=window.rootContainer
        windowPost=rootContainer.getPropertyValue("post")
        if post == windowPost:
            print "Found an interested console window..."

            if numOutputs == 0:
                print "Skipping the load workspace posting because the spreadsheet would be empty..."
                return
            
            print "Posting the loud workspace..."
            
            # We don't want to open the setpoint spreadsheet immediately, rather we want to post an OC Alert,
            # the load workspace, which will get their attention.  We are already on the client that is 
            # interested, we don't have to broadcast an OC alert message, so call the message handler which opens
            # the OC alert window on this client.
                        
            callback="ils.diagToolkit.finalDiagnosisClient.postSpreadsheet"

            callbackPayloadDictionary = {"post": post, "notificationText": notificationText}
            callbackPayloadDataset=system.dataset.toDataSet(["payload"], [[callbackPayloadDictionary]])
            
            ocPayload = {
                         "post": post,
                         "topMessage": "Attention!! Attention!!", 
                         "bottomMessage": "New diagnosis(es) is(are) here!", 
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
                
            return
    
    print "*** This client is not interested in the setpoint spreadsheet for the %s post ***" % (post)

#
# The purpose of this notification handler is to notify the operator of a text recommendation.
# The idea is that the gateway will send a message to all clients.  The payload of the 
# message includes the console name.  If the client is responsible for the console specified then a loud workspace is 
# displayed.  There are a number of stratagies that could be used to determine if a client is 
# responsible for / interested in a certain console.  The first one I will try is to check to see if the console window
# is open.  (This depends on a reliable policy for keeping the console displayed)
def handleTextRecommendationNotification(payload):
    print "-----------------------"
    print "In %s.handleTextRecommendationNotification with %s" % (__name__, str(payload))
    
    post=payload.get('post', '')
    notificationText=payload.get('notificationText', '')
    application=payload.get('application', '')
    database=payload.get('database', '')
    provider=payload.get('provider', '')
    diagnosisEntryId=payload.get('diagnosisEntryId', '')
    
    windows = system.gui.getOpenedWindows()
    
    print "Checking for a matching console window..."
    for window in windows:
        windowPath=window.getPath()
        rootContainer=window.rootContainer
        windowPost=rootContainer.getPropertyValue("post")
        if post == windowPost:
            print "Found an interested console window, posting the loud workspace..."
            callback="ils.diagToolkit.finalDiagnosisClient.ackTextRecommendation"

            callbackPayloadDictionary = {"post": post, "application": application, "notificationText": notificationText, "diagnosisEntryId": diagnosisEntryId, "database": database, "provider": provider}
            callbackPayloadDataset=system.dataset.toDataSet(["payload"], [[callbackPayloadDictionary]])
            
            ocPayload = {
                         "post": post,
                         "topMessage": "Attention!! Attention!!", 
                         "bottomMessage": "New diagnosis(es) is(are) here!", 
                         "buttonLabel": "Acknowledge",
                         "callback": callback,
                         "callbackPayloadDataset": callbackPayloadDataset,
                         "mainMessage": "<HTML> %s" % (notificationText),
                         "timeoutEnabled": False,
                         "timeoutSeconds": 300
                         }

            # This is not the normal way to post the OC alert - normally a message is sent out to clients, but in this case 
            # we already caught a message so we are in the client            
            from ils.common.ocAlert import handleMessage
            handleMessage(ocPayload)
            return
    
    print "*** This client is not interested in the text recommendation for the %s post ***" % (post)


def ackTextRecommendation(event, payload):
    print "ACKing a text recommendation - the payload is: ", payload
    
    post=payload.get("post", "")
    application=payload.get("application","")
    database=payload.get("database","")
    provider=payload.get("provider","")
    diagnosisEntryId=payload.get("diagnosisEntryId","")
    
    from ils.diagToolkit.setpointSpreadsheet import acknowledgeTextRecommendationProcessing
    acknowledgeTextRecommendationProcessing(post, application, diagnosisEntryId, database, provider)
    # Dismiss the loud workspace
#    system.nav.closeParentWindow(event)
    


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
    
    