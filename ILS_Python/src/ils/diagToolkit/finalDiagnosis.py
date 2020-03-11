'''
Created on Sep 12, 2014

@author: Pete
'''

import system, string
import system.ils.blt.diagram as scriptingInterface
from ils.diagToolkit.common import fetchPostForApplication, fetchNotificationStrategy,fetchApplicationManaged, fetchActiveOutputsForPost
from ils.diagToolkit.setpointSpreadsheet import resetApplication
from ils.diagToolkit.api import insertApplicationQueueMessage
from ils.diagToolkit.constants import RECOMMENDATION_RESCINDED, RECOMMENDATION_NONE_MADE, RECOMMENDATION_NO_SIGNIFICANT_RECOMMENDATIONS, \
    RECOMMENDATION_REC_MADE, RECOMMENDATION_ERROR, RECOMMENDATION_POSTED, AUTO_NO_DOWNLOAD, RECOMMENDATION_TEXT_POSTED
from ils.io.util import getOutputForTagPath
from system.ils.blt.diagram import getProductionDatabase
from ils.queue.constants import QUEUE_ERROR, QUEUE_WARNING, QUEUE_INFO
from ils.common.operatorLogbook import insertForPost
from ils.common.util import addHTML
from ils.common.database import lookup

log = system.util.getLogger("com.ils.diagToolkit")
logSQL = system.util.getLogger("com.ils.diagToolkit.SQL")

'''
This is called from any global resource, either a SFC or a tag change script.  This runs in the gateway and must contain a project name 
which is use to send a message for notification.
'''
def manageFinalDiagnosisGlobally(projectName, applicationName, familyName, finalDiagnosisName, textRecommendation, database="", provider = ""):
    log.infof("In %s.manageFinalDiagnosisGlobally()", __name__)
    _manageFinalDiagnosis(projectName, applicationName, familyName, finalDiagnosisName, textRecommendation, database, provider)


'''
This is called from a client (and runs in a client) to directly manage a final diagnosis.
Because this runs ina client we can get the project automatically
'''
def manageFinalDiagnosis(applicationName, familyName, finalDiagnosisName, textRecommendation, database="", provider = ""):
    log.infof("In %s.manageFinalDiagnosis()", __name__)

    projectName = system.util.getProjectName()
    log.infof("...fetched project: %s", projectName)
    _manageFinalDiagnosis(projectName, applicationName, familyName, finalDiagnosisName, textRecommendation, database, provider)


'''
# This directly manages a final diagnosis.  It can be called from a client or in gateway scope from a tag or SFC.
'''
def _manageFinalDiagnosis(projectName, applicationName, familyName, finalDiagnosisName, textRecommendation, database, provider):
    log.infof("In %s._manageFinalDiagnosis()", __name__)
 
    ''' Lookup the application Id '''
    from ils.diagToolkit.common import fetchFinalDiagnosis
    record = fetchFinalDiagnosis(applicationName, familyName, finalDiagnosisName, database)
    
    finalDiagnosisId=record.get('FinalDiagnosisId', None)
    if finalDiagnosisId == None:
        log.error("ERROR posting a diagnosis entry for %s - %s - %s because the final diagnosis was not found!" % (applicationName, familyName, finalDiagnosisName))
        return

    unit=record.get('UnitName',None)
    if unit == None:
        log.error("ERROR posting a diagnosis entry for %s - %s - %s because we were unable to locate a unit!" % (applicationName, familyName, finalDiagnosisName))
        return
    
    ''' Reset the flag that indicates that minimum change requirements should be ignored. '''
    resetOutputLimits(finalDiagnosisId, database)
    
    grade=system.tag.read("[%s]Site/%s/Grade/Grade" % (provider,unit)).value
    log.info("The grade is: %s" % (str(grade)))

    ''' Insert an entry into the diagnosis queue '''
    SQL = "insert into DtDiagnosisEntry (FinalDiagnosisId, Status, Timestamp, Grade, TextRecommendation, "\
        "RecommendationStatus, Multiplier) "\
        "values (%i, 'Active', getdate(), '%s', '%s', '%s', 1.0)" \
        % (finalDiagnosisId, grade, textRecommendation, RECOMMENDATION_NONE_MADE)
    
    SQL2 = "update dtFinalDiagnosis set State = 1 where FinalDiagnosisId = %i" % (finalDiagnosisId)
    
    try:
        system.db.runUpdateQuery(SQL, database)
        
        SQL = SQL2
        system.db.runUpdateQuery(SQL, database)
    except:
        log.errorf("postDiagnosisEntry. Failed ... update to %s (%s)",database,SQL)
    
    ''' Set the output state of the Final diagnosis and propagate its value '''
    diagramUUID = record.get("DiagramUUID")
    finalDiagnosisUUID = record.get("FinalDiagnosisUUID")
    system.ils.blt.diagram.setBlockState(diagramUUID, finalDiagnosisName, "TRUE")
    system.ils.blt.diagram.propagateBlockState(diagramUUID, finalDiagnosisUUID)
    
    notificationText, activeOutputs, postTextRecommendation, noChange = manage(applicationName, recalcRequested=False, database=database, provider=provider)
    log.info("...back from manage!")
    
    ''' This specifically handles the case where a FD that is not the highest priority clears which should not disturb the client. '''
    if noChange:
        log.info("Nothing has changed so don't notify the clients")
        return

    '''
    The activeOutputs can only be trusted if the new FD that became True changes the highest priority one.  If it was of a lower priority
    then activeOutputs will be 0 because there was no change.  Note that this is a totally different logic thread than if a FD became False.
    '''
    post=fetchPostForApplication(applicationName, database)
    notificationStrategy, clientId = fetchNotificationStrategy(applicationName, database)
    
    '''
    The focus for manage is an application, but we are about to send a message to a post, which may be responsible for more than 1 application.  I need to
    be careful with the treatment of activeOutputs and consider the total for all applications going to the post.  Specifically, if they have 2 applications, 
    press the inactive button for 1 and then do a no download on the other, only the other one is managed and it now has 0 active outputs but the other one 
    still has active ones.
    '''
    pds = fetchActiveOutputsForPost(post, database)
    activeOutputs = len(pds)
    log.infof("There are still %d active outputs for %s", activeOutputs, post)
    log.infof("Using notification strategy <%s> for a directly managed final diagnosis.", notificationStrategy)

    if notificationStrategy == "ocAlert":
#            if activeOutputs > 0:
        '''
        Changed on 4/6/17 to notify even when there are no active outputs to fix problem where a FD cleared while the setpoint spreadsheet is open, but before it was
        acted upon.
        '''
        notifyClients(projectName, post, notificationText=notificationText, numOutputs=activeOutputs, database=database, provider=provider)

        if postTextRecommendation:
            notifyClientsOfTextRecommendation(projectName, post, applicationName, database, provider)
    elif notificationStrategy == "clientId":
        if activeOutputs > 0:
            print "Send a message to ", clientId
            notififySpecificClientToOpenSpreadsheet(projectName, post, applicationName, clientId, database, provider)
        else:
            print "Skipping notification because there are no active outputs"
    else:
        log.errorf("ERROR: Unknown notification strategy <%s>", notificationStrategy)
    
#-------------

# Send a message to clients to update their setpoint spreadsheet, or display it if they are an interested
# console and the spreadsheet isn't displayed.
def notifyClients(project, post, clientId=-1, notificationText="", notificationMode="loud", numOutputs=0, database="", provider=""):
    log.info("Notifying %s-%s client %s to open/update the setpoint spreadsheet, numOutputs: <%s>, notificationText: %s, database: %s, mode: %s..." % (project, post, str(clientId), str(numOutputs), notificationText, database, notificationMode))
    messageHandler="consoleManager"
    payload={'type':'setpointSpreadsheet', 'post':post, 'notificationText':notificationText, 'numOutputs':numOutputs, 'clientId':clientId, 'notificationMode':notificationMode, 'gatewayDatabase':database}
    notifier(project, post, messageHandler, payload, database)

    # If we are going to notify client to update their spreadsheet then maybe they should also update their recommendation maps...    
    from ils.diagToolkit.recommendationMap import notifyRecommendationMapClients
    notifyRecommendationMapClients(project, post, clientId)

# Send a message to clients to update their setpoint spreadsheet, or display it if they are an interested
# console and the spreadsheet isn't displayed.
def notifyClientsOfTextRecommendation(project, post, application, database, provider):
    log.info("Notifying %s-%s-%s client of a Text Recommendation..." % (project, post, application))
    messageHandler="consoleManager"
    payload={'type':'textRecommendation', 'post':post, 'application':application, 'database':database, 'provider':provider, 'gatewayDatabase':database}
    notifier(project, post, messageHandler, payload, database)

# The notification escalation is as follows:
#   1) Notify every client logged in as the console operator
#   2) If #1 is not found then notify every client displaying the console window
#   3) If #2 is not found then notify every client
def notifier(project, post, messageHandler, payload, database):
    log.infof("%s.notifier() - Notifying...", __name__)
    productionDatabase = getProductionDatabase()
    if database == productionDatabase:
        isolationMode = False
    else:
        isolationMode = True
    
    #-------------------------------------------------------------------------------------------------
    def work(project=project, post=post, messageHandler=messageHandler, payload=payload, isolationMode=isolationMode, database=database):
        log.tracef("...working asynchrounously using database: %s...", database)
        
        notifiedClients = []
        
        from ils.common.message.interface import getPostClientIds
        clientSessionIds = getPostClientIds(post, project, database, isolationMode)
        if len(clientSessionIds) > 0:
            log.tracef("Found %d clients logged in as %s sending OC alert them!", len(clientSessionIds), post)
            for clientSessionId in clientSessionIds:
                system.util.sendMessage(project=project, messageHandler=messageHandler, payload=payload, scope="C", clientSessionId=clientSessionId)
                notifiedClients.append(clientSessionId)

        from ils.common.message.interface import getConsoleClientIdsForPost
        clientSessionIds = getConsoleClientIdsForPost(post, project, database, isolationMode)
        log.tracef("The clients are: %s", str(clientSessionIds))
        if len(clientSessionIds) > 0:
            for clientSessionId in clientSessionIds:
                if clientSessionId not in notifiedClients:
                    log.tracef("Found a client with the console displayed %s with client Id %s", post, str(clientSessionId))
                    system.util.sendMessage(project=project, messageHandler=messageHandler, payload=payload, scope="C", clientSessionId=clientSessionId)
                    notifiedClients.append(clientSessionId)

        if len(notifiedClients) == 0:
            log.tracef("Notifying OC alert to every client because I could not find the post logged in")
            system.util.sendMessage(project=project, messageHandler=messageHandler, payload=payload, scope="C")
    #----------------------------------------------------------------------------------------------------------------      
    system.util.invokeAsynchronous(work)

'''
The notifies a specific client to open the setpoint spreadsheet.  It was implemented specifically for Rate Change where the user presses a button on the 
Review Data window to trigger the download, and then we want the Setpoint spredsheet to come up on that window as fast as possible without the loud workspace.
'''
def notififySpecificClientToOpenSpreadsheet(project, post, applicationName, clientId, database, provider):
    print "Notifying..."
    messageHandler="consoleManager"
    payload={'type':'openSpreadsheetForSpecificClient', 'application':applicationName, 'post': post, 
            'database':database, 'provider':provider, 'gatewayDatabase':database}
    system.util.sendMessage(project=project, messageHandler=messageHandler, payload=payload, scope="C", clientSessionId=clientId)

#handleOpenSpreadsheetForSpecificClientNotification

def postDiagnosisEntryMessageHandler(payload):
    '''
    Unpack the payload into arguments and call the method that posts a diagnosis entry.  
    This only runs in the gateway.  I'm not sure who calls this - this might be to facilitate testing, but I'm not sure
    '''
    log.infof("In %s.postDiagnosisEntryMessageHandler(), the payload is: %s", __name__, str(payload))

    application=payload["application"]
    family=payload["family"]
    finalDiagnosis=payload["finalDiagnosis"]
    UUID=payload["UUID"]
    diagramUUID=payload["diagramUUID"]
    database=payload["database"]
    provider=payload["provider"]
    
    postDiagnosisEntry(application, family, finalDiagnosis, UUID, diagramUUID, database, provider)

# This is called from the finalDiagnosis method acceptValue when the value is True.  This should only happen afer we receiv a False and have cleared the previous diagnosis entry.
# However, on a gateway restart, we may become True again.  There are two possibilities of how this could be handled: 1) I could ignore the Insert a record into the diagnosis queue
def postDiagnosisEntry(applicationName, family, finalDiagnosis, UUID, diagramUUID, database="", provider=""):
    log.infof("In %s.postDiagnosisEntry() ", __name__)
    projectName = system.util.getProjectName()
    
    managed = fetchApplicationManaged(applicationName, database)
    
    if not(managed):
        log.tracef("Exiting because %s is not a managed application!", applicationName)
        return
    
    log.info("Posting a diagnosis entry for project: %s, application: %s, family: %s, final diagnosis: %s" % (projectName, applicationName, family, finalDiagnosis))
    
    # Lookup the application Id
    from ils.diagToolkit.common import fetchFinalDiagnosis
    record = fetchFinalDiagnosis(applicationName, family, finalDiagnosis, database)
    
    finalDiagnosisId=record.get('FinalDiagnosisId', None)
    if finalDiagnosisId == None:
        log.error("ERROR posting a diagnosis entry for %s - %s - %s because the final diagnosis was not found!" % (applicationName, family, finalDiagnosis))
        return
    
    unit=record.get('UnitName',None)
    if unit == None:
        log.error("ERROR posting a diagnosis entry for %s - %s - %s because we were unable to locate a unit!" % (applicationName, family, finalDiagnosis))
        return
    
    # Reset the flag that indicates that minimum change requirements should be ignored.
    resetOutputLimits(finalDiagnosisId, database)
    
    finalDiagnosisName=record.get('FinalDiagnosisName','Unknown Final Diagnosis')
    
    grade=system.tag.read("[%s]Site/%s/Grade/Grade" % (provider,unit)).value
    log.info("The grade is: %s" % (str(grade)))
    
    txt = mineExplanationFromDiagram(finalDiagnosisName, diagramUUID, UUID)
    log.info("The text of the diagnosis entry is: %s" % (txt))
      
    # Insert an entry into the diagnosis queue
    SQL = "insert into DtDiagnosisEntry (FinalDiagnosisId, Status, Timestamp, Grade, TextRecommendation, "\
        "RecommendationStatus, Multiplier) "\
        "values (%i, 'Active', getdate(), '%s', '%s', '%s', 1.0)" \
        % (finalDiagnosisId, grade, txt, RECOMMENDATION_NONE_MADE)
    
    SQL2 = "update dtFinalDiagnosis set State = 1 where FinalDiagnosisId = %i" % (finalDiagnosisId)
    
    try:
        system.db.runUpdateQuery(SQL, database)
        
        SQL = SQL2
        system.db.runUpdateQuery(SQL, database)
    except:
        log.errorf("postDiagnosisEntry. Failed ... update to %s (%s)",database,SQL)

    # Update the UUID and DiagramUUID of the final diagnosis
    SQL = "update DtFinalDiagnosis set FinalDiagnosisUUID = '%s', DiagramUUID = '%s' "\
        " where FinalDiagnosisId = %i "\
        % (UUID, diagramUUID, finalDiagnosisId)
    logSQL.trace(SQL)
    
    try:
        system.db.runUpdateQuery(SQL, database)
    except:
        log.errorf("postDiagnosisEntry. Failed ... update to %s (%s)",database,SQL)

    requestToManage(applicationName, database, provider)
    
def requestToManage(applicationName, database, provider):
    log.infof("In %s.requestToManage()...", __name__)
    SQL = "select count(*) from DtApplicationManageQueue where applicationName = '%s'" % (applicationName)
    cnt = system.db.runScalarQuery(SQL, database=database)
    if cnt > 0:
        log.info("Updating the timestamp for an existing record in DtApplicationManageQueue...")
        SQL = "update DtApplicationManageQueue set timestamp = getdate() where applicationName = '%s'" % (applicationName)
        system.db.runUpdateQuery(SQL, database)
    else:
        log.info("Inserting a new record into DtApplicationManageQueue for %s..." % (applicationName))
        SQL = "Insert into DtApplicationManageQueue (applicationName, provider, timestamp) values ('%s', '%s', getdate())" % (applicationName, provider)
        rows = system.db.runUpdateQuery(SQL, database=database)
        log.infof("...inserted %d rows...", rows)


'''
This was implemented to solve the problem where a single new piece of data causes a change to a number of problems nearly simultaneously.  Previously
a management thread was launched for each of the FDs that changed state, all of which would lead to the exact same answer.  This is effectively a semaphore
of sorts.
'''
def scanner():
    projectName = system.util.getProjectName()
    if projectName == "[global]":
        print "Skipping the diagnostic scanner for the global project"
        return
    _scanner(scriptingInterface.getProductionDatabase(), scriptingInterface.getProductionTagProvider())
    _scanner(scriptingInterface.getIsolationDatabase(), scriptingInterface.getIsolationTagProvider())    

        
def _scanner(database, tagProvider):
    log.tracef("Checking to see if there are applications to manage using database: %s...", database)
    projectName = system.util.getProjectName()

    SQL = "select AMQ.ApplicationName, Provider, Timestamp "\
        " from DtApplicationManageQueue AMQ, DtApplication A"\
        " where AMQ.ApplicationName = A.ApplicationName "\
        " and A.Managed = 1"

    pds = system.db.runQuery(SQL, database)
    
    ageInterval = system.tag.read("[%s]Configuration/DiagnosticToolkit/diagnosticAgeInterval" % (tagProvider)).value

    for record in pds:  
        applicationName = record["ApplicationName"]  
        timestamp = record["Timestamp"]
        secondsSince = system.date.secondsBetween(timestamp, system.date.now())
        log.tracef("...%s - %s seconds since a diagnosis became tree...", applicationName, str(secondsSince))
        if secondsSince < ageInterval:
            log.info("There is an application to be managed, but it needs to age...")
        else:
            SQL = "delete from DtApplicationManageQueue where applicationName = '%s'" % (applicationName)
            system.db.runUpdateQuery(SQL, database)
            
            provider = record["Provider"]
            log.infof("Calling Manage...")
            notificationText, activeOutputs, postTextRecommendation, noChange = manage(applicationName, recalcRequested=False, database=database, provider=provider)
            log.infof("...back from manage, activeOutputs: %s, postTextRecommendation: %s, notificationText: %s!", str(activeOutputs), str(postTextRecommendation), notificationText)
            
            # This specifically handles the case where a FD that is not the highest priority clears which should not disturb the client.
            if noChange:
                log.info("Nothing has changed so don't notify the clients")
                return

            # The activeOutputs can only be trusted if the new FD that became True changes the highest priority one.  If it was of a lower priority
            # then activeOutputs will be 0 because there was no change.  Note that this is a totally different logic thread than if a FD became False.
            post=fetchPostForApplication(applicationName, database)
            notificationStrategy, clientId = fetchNotificationStrategy(applicationName, database)
            
            '''
            The focus for manage is an application, but we are about to send a message to a post, which may be responsible for more than 1 application.  I need to
            be careful with the treatment of activeOutputs and consider the total for all applications going to the post.  Specifically, if they have 2 applications, 
            press the inactive button for 1 and then do a no download on the other, only the other one is managed and it now has 0 active outputs but the other one 
            still has active ones.
            '''
            outputsPds = fetchActiveOutputsForPost(post, database)
            activeOutputs = len(outputsPds)
            log.infof("There are still %d active outputs for %s", activeOutputs, post)
            
            if notificationStrategy == "ocAlert":
    #            if activeOutputs > 0:
                '''
                Changed on 4/6/17 to notify even when there are no active outputs to fix problem where a FD cleared while the setpoint spreadsheet is open, but before it was
                acted upon.
                '''
                notifyClients(projectName, post, notificationText=notificationText, numOutputs=activeOutputs, database=database, provider=provider)
    
                if postTextRecommendation:
                    notifyClientsOfTextRecommendation(projectName, post, applicationName, database, provider)
            elif notificationStrategy == "clientId":
                if activeOutputs > 0:
                    print "Send a message to ", clientId
                    notififySpecificClientToOpenSpreadsheet(projectName, post, applicationName, clientId, database, provider)
                else:
                    print "Skipping notification because there are no active outputs"
            else:
                log.errorf("ERROR: Unknown notification strategy <%s>", notificationStrategy)
                
    log.tracef("...done managing for database: %s!", database)

def mineExplanationFromDiagram(finalDiagnosisName, diagramUUID, UUID):
    print "Mining explanation for %s - <%s> <%s>" % (finalDiagnosisName, str(diagramUUID), str(UUID)) 
    try:
        explanation=system.ils.blt.diagram.getExplanation(diagramUUID, UUID)
        txt = "%s is TRUE because %s" % (finalDiagnosisName, explanation)
    except:
        txt = "%s is TRUE for an unknown reason (explanation mining failed)" % (finalDiagnosisName)
    return txt
    
# Clear the final diagnosis (make the status = 'InActive') 
def clearDiagnosisEntry(applicationName, family, finalDiagnosis, database="", provider=""):
    projectName = system.util.getProjectName()
    log.info("Clearing the diagnosis entry for %s - %s - %s - %s..." % (projectName, applicationName, family, finalDiagnosis))

    from ils.diagToolkit.common import fetchFinalDiagnosis
    record = fetchFinalDiagnosis(applicationName, family, finalDiagnosis, database)
    finalDiagnosisId=record.get('FinalDiagnosisId', None)
    if finalDiagnosisId == None:
        log.error("ERROR clearing a diagnosis entry for %s - %s - %s because the final diagnosis was not found!" % (applicationName, family, finalDiagnosis))
        return    

    # If there was an active diagnosis entry then set its recommendation status to RESCINDED and its state to INACTIVE
    SQL = "update DtDiagnosisEntry set RecommendationStatus = '%s', Status = 'InActive' where FinalDiagnosisId = %i and Status = 'Active'" % (RECOMMENDATION_RESCINDED, finalDiagnosisId)
    logSQL.trace(SQL)
    rows = system.db.runUpdateQuery(SQL, database)
    log.trace("Cleared %i diagnosis entries" % (rows))

    # PAH 1/22/17 consolidated this SQL with the one above that had the same where clause...
#    SQL = "update DtDiagnosisEntry set Status = 'InActive' where FinalDiagnosisId = %i and Status = 'Active'" % (finalDiagnosisId)
#    logSQL.trace(SQL)
#    rows = system.db.runUpdateQuery(SQL, database)
#   log.info("...cleared %i diagnosis entries" % (rows))
    
    # Set the state of the Final Diagnosis to InActive
    SQL = "update DtFinalDiagnosis set State = 0, Active = 0 where FinalDiagnosisId = %i" % (finalDiagnosisId)
    logSQL.trace(SQL)
    rows = system.db.runUpdateQuery(SQL, database)
    log.info("...cleared %i final diagnosis" % (rows))
    
    requestToManage(applicationName, database, provider)


# Unpack the payload into arguments and call the method that posts a diagnosis entry.  
# This only runs in the gateway.  I'm not sure who calls this - this might be to facilitate testing, but I'm not sure
def recalcMessageHandler(payload):
    log.infof("In recalcMessageHandler, the payload is: %s", str(payload))
    post=payload["post"]
    applications=payload["applications"]
    project=system.util.getProjectName()
    
    database=payload["database"]
    provider=payload["provider"]

#    from ils.diagToolkit.common import fetchApplicationsForPost
#    pds=fetchApplicationsForPost(post, database)

#    needToNotifyClients=False
    totalActiveOutputs=0
    for applicationName in applications:
        log.infof("Handling recalc message for project: %s, post: %s, application: %s", project, post, applicationName)
        
        # I'm not sure why the first arg isn't notificationText and why it isn't passed to notify.
        txt, activeOutputs, postTextRecommendation, noChange = manage(applicationName, recalcRequested=True, database=database, provider=provider)
        totalActiveOutputs = totalActiveOutputs + activeOutputs
 
        if postTextRecommendation:
            notifyClientsOfTextRecommendation(project, post, applicationName, database, provider)
        else:
            notifyClients(project, post, notificationText="", numOutputs=totalActiveOutputs, database=database, notificationMode="quiet", provider=provider)


def postRecommendationMessage(application, finalDiagnosis, finalDiagnosisId, diagnosisEntryId, recommendations, quantOutputs, database):
    '''
    This is based on the original G2 procedure outout-msg-core()
    This inserts a message into the recommendation queue which is accessed from the "M" button on the common console.
    '''
    log.infof("In postRecommendationMessage(), the recommendations are: %s", str(recommendations))

    fdTextRecommendation = fetchTextRecommendation(finalDiagnosisId, database)
    textRecommendation = "The %s has detected %s. %s." % (application, finalDiagnosis, fdTextRecommendation)

    if len(recommendations) == 0:
        textRecommendation = textRecommendation + "\nNo Outputs Calculated"
    else:
        textRecommendation = textRecommendation + "\nOutputs are:"
    
    for recommendation in recommendations:
        autoOrManual=recommendation.get('AutoOrManual', None)
        outputName = recommendation.get('QuantOutput','')
        
        SQL = "Select MinimumIncrement, IgnoreMinimumIncrement from DtQuantOutput QO, DtRecommendationDefinition RD "\
            " where QO.QuantOutputId = RD.QuantOutputId "\
            " and QO.QuantOutputName = '%s' "\
            " and RD.FinalDiagnosisId = %s" % (outputName, str(finalDiagnosisId))
        pds=system.db.runQuery(SQL, database)
        if len(pds) != 1:
            return "Error fetching QuantOutput configuration: %s" % (SQL)
        record = pds[0]
        minimumIncrement=record["MinimumIncrement"]
        ignoreMinimumIncrement=record["IgnoreMinimumIncrement"]

        if autoOrManual == 'Auto':
            val = recommendation.get('AutoRecommendation', None)
            if ignoreMinimumIncrement:
                textRecommendation = "%s\n%s = %s" % (textRecommendation, outputName, str(val))
            else:
                textRecommendation = "%s\n%s = %s (min output = %s)" % (textRecommendation, outputName, str(val), str(minimumIncrement))

        elif autoOrManual == 'Manual':
            if ignoreMinimumIncrement:
                textRecommendation = "%s\nManual move for %s = %s" % (textRecommendation, outputName, str(val))
            else:
                textRecommendation = "%s\nManual move for %s = %s (min output = %s)" % (textRecommendation, outputName, str(val), str(minimumIncrement))

    from ils.queue.message import insert
    insert("RECOMMENDATIONS", "Info", textRecommendation, database)
    return textRecommendation

# Fetch the text recommendation for a final diagnosis from the database.  For FDs that have 
# static text this is easy, but we might need to call a callback that will return dynamic text.
def fetchTextRecommendation(finalDiagnosisId, database):
    SQL = "select textRecommendation from DtFinalDiagnosis where FinalDiagnosisId = %s" % (str(finalDiagnosisId)) 
    txt=system.db.runScalarQuery(SQL, database)
    return txt

def fetchExplanationUsingName(applicationName, finalDiagnosisName, database):
    SQL = "select explanation from DtFinalDiagnosisView where ApplicationName = '%s' and FinalDiagnosisName = '%s'" % (applicationName, finalDiagnosisName) 
    txt=system.db.runScalarQuery(SQL, database)
    return txt

def fetchTextRecommendationUsingName(applicationName, finalDiagnosisName, database):
    SQL = "select textRecommendation from DtFinalDiagnosisView where ApplicationName = '%s' and FinalDiagnosisName = '%s'" % (applicationName, finalDiagnosisName) 
    txt=system.db.runScalarQuery(SQL, database)
    return txt


# Delete all of the recommendations for an Application.  This is in response to a change in the status of a final diagnosis
# and is the first step in evaluating the active FDs and calculating new recommendations.
def resetRecommendations(applicationName, log, database):
    log.infof("Deleting recommendations for %s", applicationName)
    
    SQL = "delete from DtRecommendation " \
        " where DiagnosisEntryId in (select DE.DiagnosisEntryId "\
        " from DtDiagnosisEntry DE, DtFinalDiagnosis FD, DtFamily F, DtApplication A"\
        " where A.ApplicationId = F.ApplicationId "\
        " and F.FamilyId = FD.FamilyId "\
        " and FD.FinalDiagnosisId = DE.FinalDiagnosisId "\
        " and A.ApplicationName = '%s')" % (applicationName)
    log.trace(SQL)
    rows=system.db.runUpdateQuery(SQL, database)
    log.info("...deleted %i quantitative recommendations..." % (rows))
    
    SQL = "delete from DtTextRecommendation " \
        " where DiagnosisEntryId in (select DE.DiagnosisEntryId "\
        " from DtDiagnosisEntry DE, DtFinalDiagnosis FD, DtFamily F, DtApplication A"\
        " where A.ApplicationId = F.ApplicationId "\
        " and F.FamilyId = FD.FamilyId "\
        " and FD.FinalDiagnosisId = DE.FinalDiagnosisId "\
        " and A.ApplicationName = '%s')" % (applicationName)
    log.trace(SQL)
    rows=system.db.runUpdateQuery(SQL, database)
    log.info("...deleted %i text recommendations..." % (rows))


# Delete the quant outputs for an applicatuon.
def resetOutputs(applicationName, log, database):
    log.infof("Resetting QuantOutputs for application %s", applicationName)
    SQL = "update DtQuantOutput " \
        " set Active = 0, FeedbackOutputManual = 0.0, ManualOverride = 0 where ApplicationId in (select ApplicationId "\
        " from DtApplication where ApplicationName = '%s') and Active = 1" % (applicationName)
    log.trace(SQL)
    rows=system.db.runUpdateQuery(SQL, database)
    log.info("...reset %i QuantOutputs..." % (rows))
        
        
# This replaces _em-manage-diagnosis().  Its job is to prioritize the active diagnosis for an application diagnosis queue.
def manage(application, recalcRequested=False, database="", provider=""):
    log.info("Managing diagnosis for application: %s using database %s and tag provider %s" % (application, database, provider))

    #---------------------------------------------------------------------
    # Merge the list of output dictionaries for a final diagnosis into the list of all outputs
    def mergeOutputs(quantOutputs, fdQuantOutputs):
#        log.trace("Merging outputs %s into %s" % (str(fdQuantOutputs), str(quantOutputs)))
        for fdQuantOutput in fdQuantOutputs:
            fdId = fdQuantOutput.get('QuantOutputId', -1)
            found = False
            for quantOutput in quantOutputs:
                qoId = quantOutput.get('QuantOutputId', -1)
                if fdId == qoId:
                    # It already exists so don't overwrite it
                    found = True
            if not(found):
                quantOutputs.append(fdQuantOutput)
        return quantOutputs

    #---------------------------------------------------------------------    
    # There are two lists.  The first is a list of all quant outputs and the second is the list of all recommendations.
    # Merge the lists into one so the recommendations are with the appropriate output
    def mergeRecommendations(quantOutputs, recommendations):
        log.info("Merging Outputs: %s with %s " % (str(quantOutputs), str(recommendations)))
        for recommendation in recommendations:
            output1 = recommendation.get('QuantOutput', None)
            if output1 != None:
                newQuantOutputs=[]
                for quantOutput in quantOutputs:
                    output2 = quantOutput.get('QuantOutput',None)
                    if output1 == output2:
                        currentRecommendations=quantOutput.get('Recommendations', [])
                        currentRecommendations.append(recommendation)
                        quantOutput['Recommendations'] = currentRecommendations
                    newQuantOutputs.append(quantOutput)
                quantOutputs=newQuantOutputs
        log.info("...outputs merged with recommendations are: %s" % (str(quantOutputs)))
        return quantOutputs

    #---------------------------------------------------------------------
    # Sort out the families with the highest family priorities - this works because the records are fetched in 
    # descending order.  Remember that the highest priority is the lowest number (i.e. priority 1 is more important 
    # than priority 10.
    def selectHighestPriorityFamilies(pds):
        
        aList = []
        log.info("The families with the highest priorities are: ")
        highestPriority = pds[0]['FamilyPriority']
        for record in pds:
            if record['FamilyPriority'] == highestPriority:
                log.info("  Family: %s, Family Priority: %f, Final Diagnosis: %s, Final Diagnosis Priority: %f" % (record['FamilyName'], record['FamilyPriority'], record['FinalDiagnosisName'], record['FinalDiagnosisPriority']))
                aList.append(record)
        
        return aList
    
    #---------------------------------------------------------------------
    # Filter out low priority diagnosis where there are multiple active diagnosis within the same family
    def selectHighestPriorityDiagnosisForEachFamily(aList):
        log.info("Filtering out low priority diagnosis for families with multiple active diagnosis...")
        lastFamily = ''
        mostImportantPriority = 10000000
        bList = []
        for record in aList:
            family = record['FamilyName']
            finalDiagnosisPriority = record['FinalDiagnosisPriority']
            if family != lastFamily:
                lastFamily = family
                mostImportantPriority = finalDiagnosisPriority
                bList.append(record)
            elif finalDiagnosisPriority <= mostImportantPriority:
                bList.append(record)
            else:
                log.info("   ...removing %s because it's priority %f is greater than the most important priority %f" % (record["FinalDiagnosisName"], finalDiagnosisPriority, mostImportantPriority))
        return bList
    
    #---------------------------------------------------------------------
    # Whatever is Active must have been the highest priority
    def fetchPreviousHighestPriorityDiagnosis(applicationName, database):
        log.info("Fetching the previous highest priority diagnosis...")
        SQL = "Select FinalDiagnosisName, FinalDiagnosisId "\
            " from DtApplication A, DtFamily F, DtFinalDiagnosis FD "\
            " where A.ApplicationName = '%s' " \
            " and A.ApplicationId = F.ApplicationId "\
            " and F.FamilyId = FD.FamilyId "\
            " and FD.Active = 1"\
            % (applicationName)
        logSQL.trace(SQL)
        pds = system.db.runQuery(SQL, database)
        aList=[]
        
        if len(pds) == 0:
            log.info("There were NO previous active priorities!")
        else:
            for record in pds:
                aList.append(record["FinalDiagnosisId"])
                log.info("   %s - %i" % (record["FinalDiagnosisName"], record["FinalDiagnosisId"]))

        return aList

    #---------------------------------------------------------------------
    def setActiveDiagnosisFlag(alist, database):
        log.info("Updating the 'active' flag for FinalDiagnosis...")
        # First clear all of the active flags in 
        families = []   # A list of quantOutput dictionaries
        for record in alist:
            familyId = record['FamilyId']
            if familyId not in families:
                log.info("   ...clearing all FinalDiagnosis in family %s..." % str(familyId))
                families.append(familyId)
                SQL = "update dtFinalDiagnosis set Active = 0 where FamilyId = %i" % (familyId)
                logSQL.trace(SQL)
                rows=system.db.runUpdateQuery(SQL, database)
                log.info("      updated %i rows!" % (rows))

        # Now set the ones that are active...
        for record in alist:
            finalDiagnosisId = record['FinalDiagnosisId']
            log.info("   ...setting Final Diagnosis %i to active..." % (finalDiagnosisId))
            SQL = "update dtFinalDiagnosis set Active = 1, LastRecommendationTime = getdate() where FinalDiagnosisId = %i" % (finalDiagnosisId)
            logSQL.trace(SQL)
            rows = system.db.runUpdateQuery(SQL, database)
            log.info("      updated %i rows!" % (rows))
    
    #-------------------------------------------------------------------
    # Compare the list of most important final diagnosis from the last time we managed to the most important right
    # now.  If there was no change then we won't need to recalculate recommendations.  To make this a little more 
    # challenging the contents of the lists are in different formats.
    # oldList is simply a list of diagnosisFamilyIds
    def compareFinalDiagnosisState(oldList, activeList):       
        # Convert the activeList into a format identical to oldList.
        newList=[]
        for record in activeList:
            finalDiagnosisId=record.get("FinalDiagnosisId", -1)
            if finalDiagnosisId not in newList:
                newList.append(finalDiagnosisId)
        
        changed=False
        log.trace("   old list: %s" % (str(oldList)))
        log.trace("   new list: %s" % (str(newList)))
        
        # If the lengths of the lists are different then they must be different!
        if len(oldList) != len(newList):
            changed=True
        
        lowPriorityList=[]
        for fdId in oldList:
            if fdId not in newList:
                changed=True
                lowPriorityList.append(fdId)

        if changed:
            log.trace("   the low priority final diagnosis are: %s" % (str(lowPriorityList)))

        return changed, lowPriorityList

    #-------------------------------------------------------------------
    def rescindLowPriorityDiagnosis(lowPriorityList, database):
        log.info("...rescinding low priority diagnosis...")
        for fdId in lowPriorityList:
            log.info("   ...rescinding recommendations for final diagnosis id: %i..." % (fdId))
            SQL = "delete from DtRecommendation where DiagnosisEntryId in "\
                " (select DiagnosisEntryId from DtDiagnosisEntry "\
                " where Status = 'Active' and RecommendationStatus = '%s' "\
                " and FinalDiagnosisId = %i)" % (RECOMMENDATION_REC_MADE, fdId)
            logSQL.trace(SQL)
            rows=system.db.runUpdateQuery(SQL, database)
            log.info("      ... deleted %i quantitative recommendations..." % (rows))
            
            SQL = "delete from DtTextRecommendation where DiagnosisEntryId in "\
                " (select DiagnosisEntryId from DtDiagnosisEntry "\
                " where Status = 'Active' and RecommendationStatus = '%s' "\
                " and FinalDiagnosisId = %i)" % (RECOMMENDATION_REC_MADE, fdId)
            logSQL.trace(SQL)
            rows=system.db.runUpdateQuery(SQL, database)
            log.info("      ... deleted %i text recommendations..." % (rows))
            
            SQL = "update DtFinalDiagnosis set Active = 0 "\
                "where FinalDiagnosisId = %i" % (fdId)
            logSQL.trace(SQL)
            rows = system.db.runUpdateQuery(SQL, database)
            log.info("      ...updated %i final diagnosis Active flag to False" % (rows))

            SQL = "update DtDiagnosisEntry set RecommendationStatus = '%s'"\
                "where Status = 'Active' and RecommendationStatus = '%s' "\
                " and FinalDiagnosisId = %i" % (RECOMMENDATION_RESCINDED, RECOMMENDATION_REC_MADE, fdId)
            logSQL.trace(SQL)
            rows = system.db.runUpdateQuery(SQL, database)
            log.info("      ...updated %i diagnosis entries recommendation state to %s..." % (rows, RECOMMENDATION_REC_MADE))

    #-------------------------------------------------------------------
    def rescindActiveDiagnosis(application, database):
        log.info("...rescinding **active** diagnosis and deleting recommendations for application %s..." % (application))

        SQL = "select R.RecommendationId "\
            "from DtRecommendation R, DtDiagnosisEntry DE, DtFinalDiagnosis FD, DtFamily F, DtApplication A"\
              " where R.DiagnosisEntryId = DE.DiagnosisEntryId and DE.FinalDiagnosisId = FD.FinalDiagnosisId "\
              " and FD.FamilyId =F.FamilyId and F.ApplicationId = A.applicationId and A.applicationName = '%s'" % (application)
        
        pds = system.db.runQuery(SQL, database)
        totalRows=0
        for record in pds:
            recommendationId=record["RecommendationId"]
            SQL = "delete from DtRecommendation where RecommendationId = %i" % (recommendationId)
            rows=system.db.runUpdateQuery(SQL)
            totalRows=totalRows+rows
        log.info("     ...deleted %i quantitative recommendations..." % (totalRows))
        
        # Delete active text recommendations
        SQL = "select DE.DiagnosisEntryId "\
            "from DtTextRecommendation TR, DtDiagnosisEntry DE, DtFinalDiagnosis FD, DtFamily F, DtApplication A"\
              " where TR.DiagnosisEntryId = DE.DiagnosisEntryId and DE.FinalDiagnosisId = FD.FinalDiagnosisId "\
              " and FD.FamilyId =F.FamilyId and F.ApplicationId = A.applicationId and A.applicationName = '%s' " % (application)

        pds = system.db.runQuery(SQL, database)
        totalRows=0
        for record in pds:
            diagnosisEntryId=record["DiagnosisEntryId"]
            SQL = "delete from DtTextRecommendation where DiagnosisEntryId = %i" % (diagnosisEntryId)
            rows=system.db.runUpdateQuery(SQL)
            totalRows=totalRows+rows
        log.info("     ...deleted %i text recommendations..." % (totalRows))

        # Update the Quant Outputs 
        log.info("...rescinding active recommendations for %s..." % (application))
        resetOutputs(application, log, database)

        SQL = "update DtDiagnosisEntry set RecommendationStatus = '%s'"\
            "where Status = 'Active' and RecommendationStatus = '%s' "\
            " and FinalDiagnosisId in (select FD.FinalDiagnosisId "\
            " from DtDiagnosisEntry DE, DtFinalDiagnosis FD, DtFamily F, DtApplication A "\
            "where DE.Status = 'Active' and DE.FinalDiagnosisId = FD.FinalDiagnosisId "\
            " and FD.FamilyId =F.FamilyId and F.ApplicationId = A.applicationId "\
            " and A.ApplicationName = '%s')" % (RECOMMENDATION_RESCINDED, RECOMMENDATION_REC_MADE, application)
        logSQL.trace(SQL)
        rows = system.db.runUpdateQuery(SQL, database)
        log.info("      ...rescinded %i diagnosis entries!" % (rows))

    #----------------------------------------------------------------------
    # Is this needed / called??? Why not just call reset application??
    def setDiagnosisEntryErrorStatus(alist, database):
        # Somewhere an error should be logged, but not here
        log.info("Updating the diagnosis entries to indicate an error...")
        
        # First clear all of the active flags in 
        ids = []   # A list of quantOutput dictionaries
        for record in alist:
            finalDiagnosisId = record['FinalDiagnosisId']
            finalDiagnosis = record['FinalDiagnosisName']
            if finalDiagnosisId not in ids:
                log.info("   ...setting error status for active diagnosis entries for final diagnosis: %s..." % (finalDiagnosis))
                ids.append(finalDiagnosisId)
                _setDiagnosisEntryErrorStatus(finalDiagnosisId, database)

    def _setDiagnosisEntryErrorStatus(finalDiagnosisId, database):
        '''
        Update the diagnosis entry and the final diagnosis for an unexpected error.
        '''
        log.info("   ...setting error status for active diagnosis entries for final diagnosis: %i..." % (finalDiagnosisId))
        SQL = "update dtDiagnosisEntry set RecommendationStatus = '%s', status = 'InActive' where FinalDiagnosisId = %i "\
            " and status = 'Active'" % (RECOMMENDATION_ERROR, finalDiagnosisId)
        logSQL.trace(SQL)
        rows=system.db.runUpdateQuery(SQL, database)
        log.info("      ...updated %i diagnosis entries!" % (rows))
                
        SQL = "update DtFinalDiagnosis set Active = 0 where FinalDiagnosisId = %i" % (finalDiagnosisId)
        logSQL.trace(SQL)
        rows=system.db.runUpdateQuery(SQL, database)
        log.info("      ...updated %i final diagnosis!" % (rows))
    
    def resetMultipliers(applicationName):
        log.info("Resetting the multipliers...")
        SQL = "UPDATE DtDiagnosisEntry "\
            " SET Multiplier = 1.0 "\
            " WHERE Status = 'Active' and FinalDiagnosisId in (select FD.FinalDiagnosisId "\
            " from DtFinalDiagnosis FD, DtFamily F, DtApplication A "\
            " where Fd.FamilyId = F.FamilyId "\
            " and F.ApplicationId = A.ApplicationId "\
            " and A.ApplicationName = '%s')" % (applicationName)
        rows = system.db.runUpdateQuery(SQL)
        log.info("...reset %i final diagnosis" % (rows))
        
    #--------------------------------------------------------------------
    # This is the start of manage()
    #--------------------------------------------------------------------
    
    numSignificantRecommendations = 0
    postTextRecommendation = False
    explanation = ""
    diagnosisEntryId = -1
    noChange = False
    zeroChangeThreshold = system.tag.read("[%s]Configuration/DiagnosticToolkit/zeroChangeThreshold" % (provider)).value
    
    # Fetch the list of final diagnosis that were most important the last time we managed
    oldList=fetchPreviousHighestPriorityDiagnosis(application, database)
    
    if recalcRequested:
        resetMultipliers(application)
         
    from ils.diagToolkit.common import fetchActiveDiagnosis
    pds = fetchActiveDiagnosis(application, database)
    
    # If there are no active diagnosis then there is nothing to manage, but that does not mean that there as not a change.  There may have been
    # active FDs and now they have cleared which means we need to notify clients.
    if len(pds) == 0:
        log.info("Exiting the diagnosis manager because there are no active diagnosis for %s!" % (application))
        rescindActiveDiagnosis(application, database)
        return "", numSignificantRecommendations, postTextRecommendation, noChange

    log.info("The active diagnosis are: ")
    for record in pds:
        log.info("  Family: %s, Final Diagnosis: %s, Constant: %s, Family Priority: %s, FD Priority: %s, Diagnosis Entry id: %s" % 
                  (record["FamilyName"], record["FinalDiagnosisName"], str(record["Constant"]), str(record["FamilyPriority"]), 
                   str(record["FinalDiagnosisPriority"]), str(record["DiagnosisEntryId"]) ))
    
    # Sort out the families with the highest family priorities - this works because the records are fetched in 
    # descending order.
    from ils.common.database import toDict
    list0 = toDict(pds)
    list1 = selectHighestPriorityFamilies(list0)

    # Sort out diagnosis where there are multiple diagnosis for the same family
    list2 = selectHighestPriorityDiagnosisForEachFamily(list1)
    
    # Calculate the recommendations for each final diagnosis
    log.info("The families / final diagnosis with the highest priorities are: ")
    for record in list2:
        log.info("  Family: %s, Final Diagnosis: %s (%i), Constant: %s, Family Priority: %s, FD Priority: %s, Diagnosis Entry id: %s" % 
                  (record["FamilyName"], record["FinalDiagnosisName"],record["FinalDiagnosisId"], str(record["Constant"]), 
                   str(record["FamilyPriority"]), str(record["FinalDiagnosisPriority"]), str(record["DiagnosisEntryId"])))
    
    log.info("Checking if there has been a change in the highest priority final diagnosis...")
    changed,lowPriorityList=compareFinalDiagnosisState(oldList, list2)
    
    if not(changed) and not(recalcRequested):
        log.info("There has been no change in the most important diagnosis, nothing new to manage, so exiting!")
        noChange = True
        return "", numSignificantRecommendations, postTextRecommendation, noChange

    # There has been a change in what the most important diagnosis is so set the active flag
    if recalcRequested:
        log.info("Continuing to make recommendations because a recalc was requested...")
    else:
        log.info("Continuing to make recommendations because there was a change in the highest priority active final diagnosis...")

    log.info("...deleting existing recommendations for %s..." % (application))
    resetRecommendations(application, log, database)
    
    log.info("...resetting the QuantOutput active flag for %s..." % (application))
    resetOutputs(application, log, database)
    
    rescindLowPriorityDiagnosis(lowPriorityList, database)
    setActiveDiagnosisFlag(list2, database)

    log.info("--- Calculating recommendations ---")
    quantOutputs = []   # A list of quantOutput dictionaries
    explanations = []   # A list of text recommendations
    for record in list2:
        applicationName = record['ApplicationName']
        post=fetchPostForApplication(applicationName, database)
        familyName = record['FamilyName']
        finalDiagnosisName = record['FinalDiagnosisName']
        finalDiagnosisId = record['FinalDiagnosisId']
        diagnosisEntryId = record["DiagnosisEntryId"]
        constantFD = record["Constant"]
        postTextRecommendation = record["PostTextRecommendation"]
        postProcessingCallback = record["PostProcessingCallback"]
        calculationMethod = record["CalculationMethod"]
        textRecommendation = record["TextRecommendation"]
        staticExplanation = record["Explanation"]
        showExplanationWithRecommendation = record["ShowExplanationWithRecommendation"]
        
        log.info("Making a recommendation for application: %s, family: %s, final diagnosis:%s (%i), Constant: %s" % (applicationName, familyName, finalDiagnosisName, finalDiagnosisId, str(constantFD)))

        # There could be multiple Final Diagnosis that are of equal priority, so we can't just bail if the first one is constant or a text recommendation

        if constantFD:
            # Update the Diagnosis Entry status to be posted
            log.info("Setting diagnosis entry recommendation status to POSTED for a contant FD")
            SQL = "Update DtDiagnosisEntry set RecommendationStatus = '%s' where DiagnosisEntryId = %i" % (RECOMMENDATION_POSTED, diagnosisEntryId)
            system.db.runUpdateQuery(SQL)

        else:
            from ils.diagToolkit.recommendation import makeRecommendation
            recommendations, explanation, recommendationStatus = makeRecommendation(applicationName, familyName, finalDiagnosisName, finalDiagnosisId,
                diagnosisEntryId, constantFD, calculationMethod, postTextRecommendation, textRecommendation, zeroChangeThreshold, database, provider)
        
            # Fetch all of the quant outputs for the final diagnosis
            from ils.diagToolkit.common import fetchOutputsForFinalDiagnosis
            pds, fdQuantOutputs = fetchOutputsForFinalDiagnosis(applicationName, familyName, finalDiagnosisName, database)
            quantOutputs = mergeOutputs(quantOutputs, fdQuantOutputs)

            log.infof("-----------------")
            log.infof( "Recommendations: %s", str(recommendations))
            log.infof( "    Explanation: %s", explanation)
            log.infof( "         Status: %s", recommendationStatus)
            log.infof( "-----------------")

            # If there were numeric recommendations then make a concise message and post it to the application queue.
            if len(quantOutputs) > 0:
                postRecommendationMessage(applicationName, finalDiagnosisName, finalDiagnosisId, diagnosisEntryId, recommendations, quantOutputs, database)
                
            if recommendationStatus == "ERROR":
                log.error("The calculation method had an error")
                # Not sure if I need to reset the quant outputs here...
                resetApplication(post=post, application=applicationName, families=[familyName], finalDiagnosisIds=[finalDiagnosisId], quantOutputIds=[], 
                                     actionMessage=AUTO_NO_DOWNLOAD, recommendationStatus=RECOMMENDATION_ERROR, database=database, provider=provider)
                insertApplicationQueueMessage(applicationName, explanation, "error", database)
    
                requestToManage(applicationName, database, provider)
                return "Error", numSignificantRecommendations, False, noChange
    
            elif recommendationStatus == RECOMMENDATION_NONE_MADE:
                log.warn("No recommendations were made")
                diagnosisEntryId=record['DiagnosisEntryId']
                SQL = "Update DtDiagnosisEntry set RecommendationStatus = '%s' where DiagnosisEntryId = %i " % (RECOMMENDATION_NONE_MADE, diagnosisEntryId)
                logSQL.trace(SQL)
                system.db.runUpdateQuery(SQL, database)
                return "None Made", numSignificantRecommendations, False, noChange
    
            quantOutputs = mergeRecommendations(quantOutputs, recommendations)
            log.infof( "-----------------")
            log.infof( "Quant Outputs: ", str(quantOutputs))
            log.infof( "-----------------")
            
            if postTextRecommendation and explanation != "":
                originalExplanation = explanation
                if showExplanationWithRecommendation and len(staticExplanation) > 0:
                    explanation = "<HTML>" + staticExplanation + "<br><br>" + explanation
                else:
                    explanation = "<HTML>" + explanation
    
                explanations.append({"explanation": explanation, "diagnosisEntryId": diagnosisEntryId})
                writeToLogbook = system.tag.read("[%s]Configuration/DiagnosticToolkit/writeTextRecommendationsToLogbook" % provider)
                if writeToLogbook:
                    writeTextRecommendationsToLogbook(applicationName, post, staticExplanation, originalExplanation, database)

    log.info("--- Recommendations have been made, now calculating the final recommendations ---")
    finalQuantOutputs = []
    
    for quantOutput in quantOutputs:
        from ils.diagToolkit.recommendation import calculateFinalRecommendation
        quantOutputName = quantOutput.get("QuantOutput", "Unknown")
        quantOutput = calculateFinalRecommendation(quantOutput)
        if quantOutput == None:
            # The case where a FD has 5 quant outputs defined but there are only recommendations to change 3 of them is not an error
            pass
        else:
            quantOutput, madeSignificantRecommendation = checkBounds(applicationName, quantOutput, quantOutputName, database, provider)
            if madeSignificantRecommendation:
                numSignificantRecommendations=numSignificantRecommendations + 1
                
            if quantOutput == None:
                # If there was an error checking bounds, specifically if the current value could not be read, the we can't make any valid recommendations
                # Remember that the change is really a vector, and if we lose one dimension then we will twist the plant.
#                finalQuantOutputs = []
#                setDiagnosisEntryErrorStatus(list2, database)
                log.info("Performing an automatic NO-DOWNLOAD because there was an error reading current values during bounds checking for %s..." % (quantOutputName)) 
                resetApplication(post=post, application=applicationName, families=[familyName], finalDiagnosisIds=[finalDiagnosisId], 
                         quantOutputIds=[], actionMessage=AUTO_NO_DOWNLOAD, recommendationStatus=RECOMMENDATION_ERROR, database=database, provider=provider)

                '''
                If we auto-nodownload on the highest priority problem, we should do another manage just to check if there is an active lower priority problem.
                '''
                requestToManage(applicationName, database, provider)
        
                # I just added this - 5/9/16, this used to continue on.
                return RECOMMENDATION_ERROR, 0, False, noChange
         
            finalQuantOutputs.append(quantOutput)

    finalQuantOutputs, notificationText = calculateVectorClamps(finalQuantOutputs, provider)
    
    # Store the results in the database 
    log.info("Done managing, the final outputs are: %s" % (str(finalQuantOutputs)))
    updateApplicationDownloadStatus(application, 'ACTIVE', database)
    quantOutputIds=[]
    for quantOutput in finalQuantOutputs:
        quantOutputIds.append(quantOutput.get("QuantOutputId", -1))
        updateQuantOutput(quantOutput, database, provider)
    
    postTextRecommendation = False
    if constantFD:
        log.info(" --- handling a constant final diagnosis (by doing nothing) ---")
    elif len(explanations) > 0:
        log.infof(" --- handling %d text recommendation(s) ---", len(explanations))
        log.infof("%s", str(explanations))
        postTextRecommendation = True

        for explanationDictionary in explanations:
            SQL = "Insert into DtTextRecommendation (DiagnosisEntryId, TextRecommendation) values (%i, '%s')" % (explanationDictionary['diagnosisEntryId'], explanationDictionary['explanation'])
            system.db.runUpdateQuery(SQL, database=database)

        # Let whoever initiated the manage deal with the notification 
#        projectName = system.util.getProjectName()
#        notifyClientsOfTextRecommendation(projectName, post, application, explanation, diagnosisEntryId, database, provider)
    elif numSignificantRecommendations == 0:
        log.info("There are no significant recommendations - Performing an automatic NO-DOWNLOAD because there are no significant recommendations for final diagnosis %s - %s..." % (str(finalDiagnosisId), finalDiagnosisName)) 
        resetApplication(post=post, application=applicationName, families=[familyName], finalDiagnosisIds=[finalDiagnosisId], 
                         quantOutputIds=quantOutputIds, actionMessage=AUTO_NO_DOWNLOAD, recommendationStatus=AUTO_NO_DOWNLOAD, 
                         database=database, provider=provider)
        notificationText = RECOMMENDATION_NO_SIGNIFICANT_RECOMMENDATIONS
        
        '''
        If we auto-nodownload on the highest priority problem, we should do another manage just to check if there is an active lower priority problem.
        '''
        requestToManage(applicationName, database, provider)
    else:
        log.info("Finished managing recommendations - there are %i significant Quant Outputs (There are %i quantOutputs)" % (numSignificantRecommendations, len(finalQuantOutputs)))
    
    return notificationText, numSignificantRecommendations, postTextRecommendation, noChange

# Check that recommendation against the bounds configured for the output
def checkBounds(applicationName, quantOutput, quantOutputName, database, provider):

    log.info("   ...checking Bounds...")
    madeSignificantRecommendation=True
    # The feedbackOutput can be incremental or absolute
    feedbackOutput = quantOutput.get('FeedbackOutput', 0.0)
    feedbackOutputManual = quantOutput.get('FeedbackOutputManual', 0.0)
    manualOverride = quantOutput.get('ManualOverride', False)
    incrementalOutput=quantOutput.get('IncrementalOutput')
    mostNegativeIncrement = quantOutput.get('MostNegativeIncrement', -1000.0)
    mostPositiveIncrement = quantOutput.get('MostPositiveIncrement', 1000.0)
    
    # Read the current setpoint - the tagpath in the QuantOutput does not have the provider
    tagpath = '[' + provider + ']' + quantOutput.get('TagPath','unknown')
    outputTagPath = getOutputForTagPath(tagpath, "sp")
    log.info("   ...reading the current value of tag: %s" % (outputTagPath))
    qv=system.tag.read(outputTagPath)
    if not(qv.quality.isGood()):
        txt = "Error reading the current setpoint for %s from (%s), tag quality is: (%s)" % (quantOutputName, outputTagPath, str(qv.quality))
        log.error(txt)
        insertApplicationQueueMessage(applicationName, txt, "error", database)
 
        # Make this quant-output inactive since we can't make an intelligent recommendation without the current setpoint;
        # moreover, we don't want t to make any recommendations related to this problem / FD
        # Note: I'm not sure how to sort out this output from a situation where multiple FDs may be active - but I think that is rare
        madeSignificantRecommendation=False
        return None, madeSignificantRecommendation

    # This tests the somewhat rare (hopefully) where the tag quality is good but the value isn't.  I'm not sure if this is 
    # possible with OPC tags in production, but it is with memory tags in isolation, we can have a good tag with a value of None.
    # There is no "default value" that can be used for a tag that has a value of None - and we don't want to process other outputs
    # for the same FD - this effectively invalidates all of the recommendations for this problem.
    if qv.value == None:
        txt = "Error reading the current setpoint for %s from (%s), the value is: (%s)" % (quantOutputName, outputTagPath, str(qv.value))
        log.error(txt)
        insertApplicationQueueMessage(applicationName, txt, "error", database)
        
        madeSignificantRecommendation=False
        return None, madeSignificantRecommendation

    quantOutput['CurrentValue'] = qv.value
    quantOutput['CurrentValueIsGood'] = True
    log.info("   ...the current value is: %s" % (str(qv.value)))

    # If the recommendation was absolute, then convert it to incremental for the may be absolute or incremental, but we always display incremental    
    if not(incrementalOutput):
        log.info("      ...calculating an incremental change for an absolute recommendation...")
        feedbackOutput = feedbackOutput - qv.value

    # If the operator manually change the recommendation then use it - manual overrides are always incremental
    if manualOverride:
        feedbackOutput = feedbackOutputManual
        log.info("      ...using *manual* value: %f ..." % (feedbackOutput))

    # Compare the recommendation to the **incremental** limits
    log.info("      ...comparing the feedback output (%f) to most positive increment (%f) and most negative increment (%f)..." % (feedbackOutput, mostPositiveIncrement, mostNegativeIncrement))
    if feedbackOutput >= mostNegativeIncrement and feedbackOutput <= mostPositiveIncrement:
        log.info("      ...the output is not incremental bound...")
        quantOutput['OutputLimited'] = False
        quantOutput['OutputLimitedStatus'] = 'Not Bound'
        feedbackOutputConditioned=feedbackOutput
    elif feedbackOutput > mostPositiveIncrement:
        log.info("      ...the output IS positive incremental bound...")
        quantOutput['OutputLimited'] = True
        quantOutput['OutputLimitedStatus'] = 'Positive Incremental Bound'
        feedbackOutputConditioned=mostPositiveIncrement
    else:
        log.info("      ...the output IS negative incremental bound...")
        quantOutput['OutputLimited'] = True
        quantOutput['OutputLimitedStatus'] = 'Negative Incremental Bound'
        feedbackOutputConditioned=mostNegativeIncrement
        
    # Compare the final setpoint to the **absolute** limits
    setpointHighLimit = quantOutput.get('SetpointHighLimit', -1000.0)
    setpointLowLimit = quantOutput.get('SetpointLowLimit', 1000.0)
    log.info("      ...comparing the proposed setpoint (%f) to high limit (%f) and low limit (%f)..." % ((qv.value + feedbackOutputConditioned), setpointHighLimit, setpointLowLimit))

    # For the absolute limits we need to add the current value to the incremental change before comparing to the absolute limits
    if qv.value + feedbackOutputConditioned > setpointHighLimit:
        log.info("      ...the output IS Positive Absolute Bound...")
        quantOutput['OutputLimited'] = True
        quantOutput['OutputLimitedStatus'] = 'Positive Absolute Bound'
        feedbackOutputConditioned=setpointHighLimit - qv.value
    elif qv.value + feedbackOutputConditioned < setpointLowLimit:
        log.info("      ...the output IS Negative Absolute Bound...")
        quantOutput['OutputLimited'] = True
        quantOutput['OutputLimitedStatus'] = 'Negative Absolute Bound'
        feedbackOutputConditioned=setpointLowLimit - qv.value

    # Now check the minimum increment requirement
    minimumIncrement = quantOutput.get('MinimumIncrement', 1000.0)
    ignoreMinimumIncrement = quantOutput.get('IgnoreMinimumIncrement', False)
    log.info("Ignore Minimum Increment: %s" % (str(ignoreMinimumIncrement)))
    if not(ignoreMinimumIncrement) and abs(feedbackOutputConditioned) < minimumIncrement:
        log.info("      ...the output IS Minimum change bound because the change (%f) is less then the minimum change amount (%f)..." % (feedbackOutputConditioned, minimumIncrement))
        quantOutput['OutputLimited'] = True
        quantOutput['OutputLimitedStatus'] = 'Minimum Change Bound'
        feedbackOutputConditioned=0.0
        quantOutput['FeedbackOutputConditioned']=feedbackOutputConditioned
        madeSignificantRecommendation=False

    finalIncrementalValue = feedbackOutputConditioned
    
    # If the recommendation was absolute, then convert it back to absolute
    if not(incrementalOutput) and not(manualOverride):
        log.info("      ...converting an incremental change (%s) back to an absolute recommendation (%s)..." % (str(feedbackOutputConditioned), str(qv.value + feedbackOutputConditioned)))
        feedbackOutputConditioned = qv.value + feedbackOutputConditioned

    quantOutput['FeedbackOutputConditioned'] = feedbackOutputConditioned
    
    # Calculate the percent of the original recommendation that we are using if the output is limited 
    if quantOutput['OutputLimited'] == True:
        # I'm not sure how the feedback output can be 0.0 AND be output limited, unless something is misconfigured
        # on the quant output, but just be extra careful to avoid a divide by zero error.
        if feedbackOutput == 0.0:
            outputPercent = 0.0
        else:
            outputPercent = finalIncrementalValue / feedbackOutput * 100.0
        
        log.info("   ...the output is bound - taking %f percent of the recommended change..." % (outputPercent))
        quantOutput['OutputPercent'] = outputPercent
        from ils.diagToolkit.common import updateBoundRecommendationPercent
        updateBoundRecommendationPercent(quantOutput['QuantOutputId'], outputPercent, database)
    
    log.info("   The recommendation after bounds checking is:")
    log.info("          Feedback Output Conditioned: %f" % (feedbackOutputConditioned))
    log.info("                       Output limited: %s" % (str(quantOutput['OutputLimited'])))
    log.info("                Output limited status: %s" % (quantOutput['OutputLimitedStatus']))
    log.info("                       Output percent: %f" % (quantOutput['OutputPercent']))
    return quantOutput, madeSignificantRecommendation

def calculateVectorClamps(quantOutputs, provider):
    log.info("Checking vector clamping with tag provider: %s..." % (provider))
    tagName="[%s]Configuration/DiagnosticToolkit/vectorClampMode" % (provider)
    
    tagExists=system.tag.exists(tagName)
    if tagExists:
        qv=system.tag.read(tagName)
        vectorClampMode = string.upper(qv.value)
    else:
        vectorClampMode = "DISABLED"
        log.error("Unable to read vector clamp configuration from %s because it does not exist - setting clamp mode to DISABLED" % (tagName))
    
    if vectorClampMode == "DISABLED":
        log.info("...Vector Clamps are NOT enabled")
        return quantOutputs, ""
    
    log.infof("...Vector clamp mode: %s", vectorClampMode)

    # There needs to be at least two outputs that are not minimum change bound for vector clamps to be appropriate
    i = 0
    for quantOutput in quantOutputs:
        if quantOutput['OutputLimitedStatus'] != 'Minimum Change Bound':
            i = i + 1

    if i < 2:
        log.info("Vector clamps do not apply when there is only one output")
        return quantOutputs, ""

    # The first step is to find the most restrictive clamp
    minOutputRatio=100.0
    for quantOutput in quantOutputs:
        if quantOutput['OutputLimitedStatus'] != 'Minimum Change Bound':
            if quantOutput['OutputPercent'] < minOutputRatio:
                boundOutput=quantOutput
                minOutputRatio = quantOutput['OutputPercent']
        else:
            log.info("...not considering %s which is minimum change bound..." % (quantOutput['QuantOutput']))
            
    if minOutputRatio == 100.0:
        log.info("No outputs are clamped, therefore there is not a vector clamp")
        return quantOutputs, ""

    log.info("All outputs will be clamped at %f pct" % (minOutputRatio))

    finalQuantOutputs = []
    txt = "The most bound output is %s, %.2f pct of the total recommendation of %.4f, which equals %.4f, will be implemented." % \
        (boundOutput['QuantOutput'], minOutputRatio, boundOutput['FeedbackOutput'], boundOutput['FeedbackOutputConditioned'])
        
    for quantOutput in quantOutputs:
        
        # Look for an output that isn't bound but needs to be Vector clamped
        if quantOutput['OutputPercent'] > minOutputRatio and quantOutput['OutputLimitedStatus'] != 'Minimum Change Bound':
            outputPercent = minOutputRatio
            feedbackOutputConditioned = quantOutput['FeedbackOutput'] * minOutputRatio / 100.0
            txt = "%s\n%s should be reduced from %.4f to %.4f" % (txt, quantOutput['QuantOutput'], quantOutput['FeedbackOutput'], 
                                                              feedbackOutputConditioned)

            # Now check if the new conditioned output is less than the minimum change amount
            minimumIncrement = quantOutput.get('MinimumIncrement', 1000.0)
            ignoreMinimumIncrement = quantOutput.get('IgnoreMinimumIncrement', False)
            if not(ignoreMinimumIncrement) and abs(feedbackOutputConditioned) < minimumIncrement:
                feedbackOutputConditioned = 0.0
                outputPercent = 0.0
                txt = "%s which is an insignificant value value and should be set to 0.0." % (txt)
                    
            if vectorClampMode == 'IMPLEMENT':
                log.info('Implementing a vector clamp on %s' % (quantOutput['QuantOutput']))
                quantOutput['OutputPercent'] = outputPercent
                quantOutput['FeedbackOutputConditioned'] = feedbackOutputConditioned
                quantOutput['OutputLimitedStatus'] = 'Vector'
                quantOutput['OutputLimited']=True

        finalQuantOutputs.append(quantOutput)
            
    log.info(txt)
    
    if vectorClampMode == 'ADVISE':
        notificationText=txt
    else:
        notificationText=""
        
    return finalQuantOutputs, notificationText

def updateApplicationDownloadStatus(applicationName, downloadAction, database):
    log.tracef("Setting the downloadAction of application %s to %s", applicationName, downloadAction)
    SQL = "update DtApplication set DownloadAction = '%s' where ApplicationName = '%s'" % (downloadAction, applicationName)
    system.db.runUpdateQuery(SQL, database=database)

# Store the updated quantOutput in the database so that it will show up in the setpoint spreadsheet
def updateQuantOutput(quantOutput, database='', provider=''):
    from ils.common.cast import toBool
    
    log.info("Updating the database with the recommendations made to QuantOutput: %s" % (str(quantOutput)))
    feedbackOutput = quantOutput.get('FeedbackOutput', 0.0)
    feedbackOutputConditioned = quantOutput.get('FeedbackOutputConditioned', 0.0)
    quantOutputId = quantOutput.get('QuantOutputId', 0)
    outputLimitedStatus = quantOutput.get('OutputLimitedStatus', '')
    outputLimited = quantOutput.get('OutputLimited', False)
    outputLimited = toBool(outputLimited)
    outputPercent = quantOutput.get('OutputPercent', 0.0)
    manualOverride = quantOutput.get('ManualOverride', False)
    manualOverride = toBool(manualOverride)
    feedbackOutputManual = quantOutput.get('FeedbackOutputManual', 0.0)
    
    '''
    Do some work to support ramps.  We need to support writing a setpoint directly to a ramp controller or to ramp the setpoint to a ramp controller.  
    The IO layer also supports ramping of a plain old controller or evenramping a OPC variable or memory tag.  The key that determines if an output
    is ramped is if the recommendation contains a "rampTime" property.  A QuantOutput may be used one time to write an output directly or a ramp setpoint.
    '''

    recommendations = quantOutput.get("Recommendations", [])
    rampTime = None
    for recommendation in recommendations:
        rampTime = recommendation.get("RampTime", None)
        if rampTime <> None:
            print "*** Found a ramp time ***"
        
    # The current setpoint was read when we checked the bounds.
    isGood = quantOutput.get('CurrentValueIsGood',False)
    if not(isGood):
        # Make this quant-output inactive since we can't make an intelligent recommendation without the current setpoint
        SQL = "update DtQuantOutput set Active = 0 where QuantOutputId = %i " % (quantOutputId)
        logSQL.trace(SQL)
        system.db.runUpdateQuery(SQL, database)
        return

    currentSetpoint=quantOutput.get('CurrentValue',None)
    log.info("     ...using current setpoint value: %s" % (str(currentSetpoint)))
    
    if manualOverride:
        # Manual values are always incremental
        log.infof("     ...using the validated manually entered value: %s (raw: %s)... ", str(feedbackOutputConditioned), str(feedbackOutputManual))
        finalSetpoint = currentSetpoint + feedbackOutputConditioned
        displayedRecommendation = feedbackOutputConditioned
    else:
        log.info("     ...using the AUTO recommendations... ")
        # The recommendation may be absolute or incremental, but we always display incremental    
        incrementalOutput=quantOutput.get('IncrementalOutput')
        if incrementalOutput:
            finalSetpoint = currentSetpoint + feedbackOutputConditioned
            displayedRecommendation = feedbackOutputConditioned
        else:
            finalSetpoint = feedbackOutputConditioned
            displayedRecommendation = finalSetpoint-currentSetpoint

    log.info("   ...the final setpoint is %f, the displayed recommendation is %f" % (finalSetpoint, displayedRecommendation))

    # Active is hard-coded to True here because these are the final active quantOutputs
    SQL = "update DtQuantOutput set FeedbackOutput = %s, OutputLimitedStatus = '%s', OutputLimited = %i, "\
        " OutputPercent = %s, FeedbackOutputManual = %s, FeedbackOutputConditioned = %s, DownloadAction = 'GO', DownloadStatus = '', "\
        " ManualOverride = %i, Active = 1, CurrentSetpoint = %s, FinalSetpoint = %s, DisplayedRecommendation = %s "\
        " where QuantOutputId = %i "\
        % (str(feedbackOutput), outputLimitedStatus, outputLimited, str(outputPercent), str(feedbackOutputManual), str(feedbackOutputConditioned), \
           manualOverride, str(currentSetpoint), str(finalSetpoint), str(displayedRecommendation), quantOutputId)
    
    logSQL.trace(SQL)
    system.db.runUpdateQuery(SQL, database)
    
    '''
    If this quant output is for a ramp controller, then the recommendation MUST contain a Ramp time 
    (Due to some confusion, when I move the rampTime into the quant output I change the name to Ramp to match the database)
    '''
    ramp = quantOutput.get('Ramp', None)
    if ramp != None:
        SQL = "update DtQuantOutputRamp set Ramp = %s where QuantOutputId = %i " % (str(ramp), quantOutputId)
        logSQL.trace(SQL)
        rows = system.db.runUpdateQuery(SQL, database)
        if rows > 0:
            log.infof("   ...updated a quantOutputRamp record...")
        else:
            rampTypeId = lookup("RampType", "Time")
            SQL = "insert into DtQuantOutputRamp (QuantOutputId, Ramp, RampTypeId) values (%d, %f, %d)" % (quantOutputId, ramp, rampTypeId)
            logSQL.trace(SQL)
            system.db.runUpdateQuery(SQL, database)
            log.infof("   ...inserted a quantOutputRamp record...")
    else:
        ''' If there isn't a ramp time in the recommendation then make sure that there isn't a ramp record for the quant output '''
        SQL = "delete from DtQuantOutputRamp where QuantOutputId = %d" % (quantOutputId)
        rows = system.db.runUpdateQuery(SQL, database)
        if rows > 0:
            log.infof("Deleted a DtQuantOutputRamp record for a non-ramp recommendation")

# Set the flag for all of the outputs used by this FD to ignore the minimumIncrement specifications.  This MUST
# be called in the FDs calculation method and only lasts until another FinalDiagnosis using the same QusantOutput becomes active 
def bypassOutputLimits(finalDiagnosisId, database=""):
    print "Bypassing output limits..."
    rows = setOutputLimits(finalDiagnosisId, 1, database)
    print "...bypassed %i rows!" % (rows)
    
# Reset the flag that enforces the minimumIncrement specifications.  This is called for a FD every time it becomes active.
def resetOutputLimits(finalDiagnosisId, database=""):
    print "Resetting output limits..."
    rows = setOutputLimits(finalDiagnosisId, 0, database)
    print "...reset %i rows!" % (rows)

def setOutputLimits(finalDiagnosisId, state, database=""):
    SQL = "Update DtQuantOutput set IgnoreMinimumIncrement = %i "\
        " where QuantOutputId in ("\
        " select QuantOutputId "\
        " from DtFinalDiagnosis FD, DtRecommendationDefinition RD "\
        " where FD.FinalDiagnosisId = %i "\
        " and FD.FinalDiagnosisId = RD.FinalDiagnosisId)" % (state, finalDiagnosisId)
    rows = system.db.runUpdateQuery(SQL, database)
    return rows

def writeTextRecommendationsToLogbook(applicationName, post, staticExplanation, explanation, db):
    log.infof("Writing a text recommendation to the logbook: %s  %s", staticExplanation, explanation)

    if staticExplanation not in ("", None):
        txt = staticExplanation + "  " + explanation
    else:
        txt = explanation
        
    ''' Write the text recommendation to the application Queue '''
    insertApplicationQueueMessage(applicationName, txt, QUEUE_INFO, db)
    
    ''' Write the text recommendation to the operator logbook '''
    txt = addHTML(txt)
    insertForPost(post, txt, db)