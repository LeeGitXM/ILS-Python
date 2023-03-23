'''
Created on Sep 12, 2014

@author: Pete
'''

import system, string
from ils.diagToolkit.common import fetchPostForApplication, fetchNotificationStrategy,fetchApplicationManaged, fetchActiveOutputsForPost
from ils.diagToolkit.setpointSpreadsheet import resetApplication
from ils.diagToolkit.api import insertApplicationQueueMessage
from ils.diagToolkit.constants import RECOMMENDATION_RESCINDED, RECOMMENDATION_NONE_MADE, RECOMMENDATION_NO_SIGNIFICANT_RECOMMENDATIONS, \
    RECOMMENDATION_REC_MADE, RECOMMENDATION_ERROR, RECOMMENDATION_POSTED, AUTO_NO_DOWNLOAD
from ils.io.util import getOutputForTagPath
from ils.config.common import getProductionDatabase, getProductionTagProvider, getIsolationDatabase, getIsolationTagProvider, getProductionDatabaseFromInternalDatabase
from ils.queue.constants import QUEUE_INFO
from ils.common.operatorLogbook import insertForPost
from ils.common.util import addHTML, escapeSqlQuotes
from ils.common.database import lookup
from ils.io.util import readTag

from ils.log import getLogger
log = getLogger(__name__)
logSQL = getLogger(__name__ + ".SQL")


def manageFinalDiagnosisGlobally(projectName, applicationName, familyName, finalDiagnosisName, textRecommendation, database="", provider = ""):
    '''
    This is called from any global resource, either a SFC or a tag change script.  This runs in the gateway and must contain a project name 
    which is use to send a message for notification.
    '''
    log.infof("In %s.manageFinalDiagnosisGlobally()", __name__)
    _manageFinalDiagnosis(projectName, applicationName, familyName, finalDiagnosisName, textRecommendation, database, provider)


def manageFinalDiagnosis(applicationName, familyName, finalDiagnosisName, textRecommendation, database="", provider="", projectName=""):
    '''
    This is called from a client (and runs in a client) to directly manage a final diagnosis.
    Because this runs in a client we can get the project automatically.
    This may also be called from an SFC in which case the project MUST be supplied or it won't notify the client, but the FD will be managed and make recommendations.
    '''
    log.infof("In %s.manageFinalDiagnosis()", __name__)

    if projectName == "":
        projectName = system.util.getProjectName()        
        log.tracef("...fetched project: %s", projectName)

    _manageFinalDiagnosis(projectName, applicationName, familyName, finalDiagnosisName, textRecommendation, database, provider)


def _manageFinalDiagnosis(projectName, applicationName, familyName, finalDiagnosisName, textRecommendation, database, provider):
    '''
    This directly manages a final diagnosis.  It can be called from a client or in gateway scope from a tag or SFC.
    '''
    
    log.tracef("In %s._manageFinalDiagnosis()", __name__)
 
    ''' Lookup the diagram - this is not guaranteed to be unique, but it should be '''
    from ils.diagToolkit.common import fetchDiagramForFinalDiagnosis
    diagramName = fetchDiagramForFinalDiagnosis(applicationName, familyName, finalDiagnosisName, database)
    log.infof("Fetched the diagram named: %s", str(diagramName))
    
    from ils.diagToolkit.common import fetchFinalDiagnosis
    record = fetchFinalDiagnosis(applicationName, familyName, diagramName, finalDiagnosisName, database)
    
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
    
    grade=readTag("[%s]Site/%s/Grade/Grade" % (provider,unit)).value

    ''' Insert an entry into the diagnosis queue '''
    log.info("Posting a diagnosis entry (from _manageFinalDiagnosis) for project: %s, application: %s, family: %s, final diagnosis: %s, grade: %s" % (projectName, applicationName, familyName, finalDiagnosisName, str(grade)))
    SQL = "insert into DtDiagnosisEntry (FinalDiagnosisId, Status, Timestamp, Grade, TextRecommendation, "\
        "RecommendationStatus, Multiplier) "\
        "values (%d, 'Active', getdate(), '%s', '%s', '%s', 1.0)" \
        % (finalDiagnosisId, grade, textRecommendation, RECOMMENDATION_NONE_MADE)
    
    SQL2 = "update dtFinalDiagnosis set State = 1 where FinalDiagnosisId = %d" % (finalDiagnosisId)
    
    try:
        print "***", SQL
        system.db.runUpdateQuery(SQL, database)
        
        SQL = SQL2
        print "***", SQL
        system.db.runUpdateQuery(SQL, database)
    except:
        log.errorf("postDiagnosisEntry. Failed ... update to %s (%s)",database,SQL)
    
    ''' Set the output state of the Final diagnosis and propagate its value '''
    from ils.blt.api import setBlockState
    setBlockState(diagramName, finalDiagnosisName, "TRUE")
    

    # I think that with the Ignition 8 migration that teh block state automatically propagates - Pete 9/8/22 
    # system.ils.blt.diagram.propagateBlockState(diagramUUID, finalDiagnosisUUID)

    
    notificationText, activeOutputs, postTextRecommendation, noChange = manage(applicationName, recalcRequested=False, database=database, provider=provider)
    log.tracef("...back from manage!")
    
    ''' This specifically handles the case where a FD that is not the highest priority clears which should not disturb the client. '''
    if noChange:
        log.tracef("Nothing has changed so don't notify the clients")
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
    log.tracef("Using notification strategy <%s> for a directly managed final diagnosis.", notificationStrategy)

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
    log.tracef("Notifying %s-%s client %s to open/update the setpoint spreadsheet, numOutputs: <%s>, notificationText: %s, database: %s, mode: %s...", project, post, str(clientId), str(numOutputs), notificationText, database, notificationMode)
    messageHandler="consoleManager"
    payload={'type':'setpointSpreadsheet', 'post':post, 'notificationText':notificationText, 'numOutputs':numOutputs, 'clientId':clientId, 'notificationMode':notificationMode, 'gatewayDatabase':database}
    notifier(project, post, messageHandler, payload, database)

    # If we are going to notify client to update their spreadsheet then maybe they should also update their recommendation maps...    
    from ils.diagToolkit.recommendationMap import notifyRecommendationMapClients
    notifyRecommendationMapClients(project, post, clientId)

# Send a message to clients to update their setpoint spreadsheet, or display it if they are an interested
# console and the spreadsheet isn't displayed.
def notifyClientsOfTextRecommendation(project, post, application, database, provider):
    log.tracef("Notifying %s-%s-%s client of a Text Recommendation...", project, post, application)
    messageHandler="consoleManager"
    payload={'type':'textRecommendation', 'post':post, 'application':application, 'database':database, 'provider':provider, 'gatewayDatabase':database}
    notifier(project, post, messageHandler, payload, database)

# The notification escalation is as follows:
#   1) Notify every client logged in as the console operator
#   2) If #1 is not found then notify every client displaying the console window
#   3) If #2 is not found then notify every client
def notifier(project, post, messageHandler, payload, database):
    log.tracef("In %s.notifier() - Notifying...", __name__)
    productionDatabase = getProductionDatabaseFromInternalDatabase(project)
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


def notififySpecificClientToOpenSpreadsheet(project, post, applicationName, clientId, database, provider):
    '''
    The notifies a specific client to open the setpoint spreadsheet.  It was implemented specifically for Rate Change where the user presses a button on the 
    Review Data window to trigger the download, and then we want the Setpoint spredsheet to come up on that window as fast as possible without the loud workspace.
    '''
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
    log.tracef("In %s.postDiagnosisEntryMessageHandler(), the payload is: %s", __name__, str(payload))

    projectName=payload["projectName"]
    diagramPath=payload["diagram"]
    finalDiagnosisName=payload["finalDiagnosis"]
    UUID=payload["UUID"]
    database=payload["database"]
    provider=payload["provider"]
    
    postDiagnosisEntry(projectName, diagramPath, finalDiagnosisName, UUID, database, provider)
    
    
def postDiagnosisEntry(projectName, diagramPath, finalDiagnosisName, UUID, database, provider):
    #applicationName, family, diagram, finalDiagnosis, UUID, diagramUUID, database="", provider=""):
    '''
    This is called from the finalDiagnosis method acceptValue when the value is True.  This should only happen after we receive a False and have 
    cleared the previous diagnosis entry.  However, on a gateway restart, we may become True again.  There are two possibilities of how this could 
    be handled: 1) I could ignore the Insert a record into the diagnosis queue
    '''
    log.infof("In %s.postDiagnosisEntry() for %s on diagram %s in project: %s (database: %s / provider: %s)", 
              __name__, finalDiagnosisName, diagramPath, projectName, database, provider)
    
    from ils.diagToolkit.common import fetchApplicationNameForDiagram
    applicationName = fetchApplicationNameForDiagram(diagramPath, database)
    if applicationName == None:
        log.errorf("ERROR posting a diagnosis entry for %s - %s because an application could not be found!", diagramPath, finalDiagnosisName)
        return
        
    managed = fetchApplicationManaged(applicationName, database)
    
    if not(managed):
        log.warnf("Exiting postDiagnosisEntry() because %s is not a managed application!", applicationName)
        return
    
    log.tracef("Posting a diagnosis entry for %s on diagram %s in project: %s", finalDiagnosisName, diagramPath, projectName)
    
    from ils.diagToolkit.common import fetchFinalDiagnosisId
    finalDiagnosisId = fetchFinalDiagnosisId(diagramPath, finalDiagnosisName, database)
    if finalDiagnosisId == None:
        log.errorf("ERROR posting a diagnosis entry for %s - %s because the final diagnosis was not found!", diagramPath, finalDiagnosisName)
        return 
    
    # Lookup the application and family
    from ils.diagToolkit.common import fetchApplicationAndFamilyForDiagram
    applicationName, familyName = fetchApplicationAndFamilyForDiagram(diagramPath, database)
    if applicationName == None or familyName == None:
        log.errorf("ERROR posting a diagnosis entry for %s - %s because the application and family were not found!", diagramPath, finalDiagnosisName)
        return
    
    from ils.diagToolkit.common import fetchFinalDiagnosis
    record = fetchFinalDiagnosis(applicationName, familyName, diagramPath, finalDiagnosisName, database)
    
    unit=record.get('UnitName',None)
    if unit == None:
        log.errorf("ERROR posting a diagnosis entry for %s - %s - %s because we were unable to locate a unit!", applicationName, familyName, finalDiagnosisName)
        return
    
    # Reset the flag that indicates that minimum change requirements should be ignored.
    resetOutputLimits(finalDiagnosisId, database)
    
    finalDiagnosisName=record.get('FinalDiagnosisName','Unknown Final Diagnosis')
    finalDiagnosisExplanation=record.get('Explanation','')

    grade=readTag("[%s]Site/%s/Grade/Grade" % (provider,unit)).value
    log.tracef("The grade is: %s", str(grade))
    
    txt = mineExplanationFromDiagram(finalDiagnosisName, diagramPath, UUID, finalDiagnosisExplanation)

    log.tracef("The raw text of the diagnosis entry is: %s", txt)
    from ils.common.util import substituteScopeReferences
    txt = substituteScopeReferences(txt, provider)
    log.tracef("The updated text of the diagnosis entry is: %s", txt)
      
    # Insert an entry into the diagnosis queue
    SQL = "insert into DtDiagnosisEntry (FinalDiagnosisId, Status, Timestamp, Grade, TextRecommendation, "\
        "RecommendationStatus, Multiplier) "\
        "values (%d, 'Active', getdate(), '%s', '%s', '%s', 1.0)" \
        % (finalDiagnosisId, grade, txt, RECOMMENDATION_NONE_MADE)
    
    SQL2 = "update dtFinalDiagnosis set State = 1 where FinalDiagnosisId = %d" % (finalDiagnosisId)
    
    try:
        system.db.runUpdateQuery(SQL, database)
        
        # Use the same variable so the log statement will show which one threw the error.
        SQL = SQL2
        system.db.runUpdateQuery(SQL, database)
    except:
        log.errorf("postDiagnosisEntry. Failed ... update to %s (%s)",database,SQL)

    # Update the UUID and DiagramUUID of the final diagnosis
    #
    # PETE - DO I NEED THIS????
    #
    '''
    SQL = "update DtFinalDiagnosis set FinalDiagnosisUUID = '%s', DiagramUUID = '%s' "\
        " where FinalDiagnosisId = %d "\
        % (UUID, diagramUUID, finalDiagnosisId)
    logSQL.tracef(SQL)
    
    try:
        system.db.runUpdateQuery(SQL, database)
    except:
        log.errorf("postDiagnosisEntry. Failed ... update to %s (%s)",database,SQL)
    '''

    requestToManage(applicationName, database, provider)
    
def requestToManage(applicationName, database, provider):
    log.infof("In %s.requestToManage()...", __name__)
    SQL = "select count(*) from DtApplicationManageQueue where applicationName = '%s'" % (applicationName)
    cnt = system.db.runScalarQuery(SQL, database=database)
    if cnt > 0:
        log.tracef("Updating the timestamp for an existing record in DtApplicationManageQueue...")
        SQL = "update DtApplicationManageQueue set timestamp = getdate() where applicationName = '%s'" % (applicationName)
        system.db.runUpdateQuery(SQL, database)
    else:
        log.tracef("Inserting a new record into DtApplicationManageQueue for %s...", applicationName)
        SQL = "Insert into DtApplicationManageQueue (applicationName, provider, timestamp) values ('%s', '%s', getdate())" % (applicationName, provider)
        rows = system.db.runUpdateQuery(SQL, database=database)
        log.tracef("...inserted %d rows...", rows)


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
    _scanner(getProductionDatabase(projectName), getProductionTagProvider(projectName), projectName)
    _scanner(getIsolationDatabase(projectName), getIsolationTagProvider(projectName), projectName)

        
def _scanner(database, tagProvider, projectName):
    log.tracef("Checking to see if there are applications to manage using database: %s...", database)

    SQL = "select AMQ.ApplicationName, Provider, Timestamp "\
        " from DtApplicationManageQueue AMQ, DtApplication A"\
        " where AMQ.ApplicationName = A.ApplicationName "\
        " and A.Managed = 1"

    pds = system.db.runQuery(SQL, database)
    log.tracef("Fetched %d records...", len(pds))
    
    ageInterval = readTag("[%s]Configuration/DiagnosticToolkit/diagnosticAgeInterval" % (tagProvider)).value

    for record in pds:  
        applicationName = record["ApplicationName"]  
        timestamp = record["Timestamp"]
        secondsSince = system.date.secondsBetween(timestamp, system.date.now())
        log.tracef("...%s - %s seconds since a diagnosis became true...", applicationName, str(secondsSince))
        if secondsSince < ageInterval:
            log.tracef("There is an application to be managed, but it needs to age...")
        else:
            SQL = "delete from DtApplicationManageQueue where applicationName = '%s'" % (applicationName)
            system.db.runUpdateQuery(SQL, database)
            
            provider = record["Provider"]
            log.tracef("Calling Manage...")
            notificationText, activeOutputs, postTextRecommendation, noChange = manage(applicationName, recalcRequested=False, database=database, provider=provider)
            log.tracef("...back from manage for application <%s>: activeOutputs: %s, postTextRecommendation: %s, notificationText: %s!", applicationName, str(activeOutputs), str(postTextRecommendation), notificationText)
            
            # This specifically handles the case where a FD that is not the highest priority clears which should not disturb the client.
            if noChange:
                log.tracef("Nothing has changed so don't notify the clients")
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
            log.tracef("There are still %d active outputs for %s", activeOutputs, post)
            
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


def mineExplanationFromDiagram(finalDiagnosisName, diagramPath, UUID, finalDiagnosisExplanation):
    log.tracef("Mining explanation for <%s> on <%s> (Final Diagnosis Explanation: <%s>)", finalDiagnosisName, diagramPath, finalDiagnosisExplanation)

    try:
        from ils.blt.api import getExplanation
        explanation=getExplanation(diagramPath, finalDiagnosisName)

        if finalDiagnosisExplanation in ["", None]:
            if explanation in ["", None]:
                txt = "%s is TRUE for an unknown reason (explanation mining failed)" % (finalDiagnosisName)
            else:
                txt = "%s is TRUE because %s" % (finalDiagnosisName, explanation)
        else:
            if explanation in ["", None]:
                txt = finalDiagnosisExplanation
            else:
                txt = "%s because %s" % (finalDiagnosisExplanation, explanation)

    except:
        txt = "%s is TRUE for an unknown reason (explanation mining failed)" % (finalDiagnosisName)
    return txt
    

def clearDiagnosisEntry(projectName, diagramPath, finalDiagnosisName, database, provider):
    #applicationName, family, finalDiagnosis, database="", provider=""):
    '''  
    Clear the final diagnosis (make the status = 'InActive')
    This is called from the BLT module when a Final Diagnosis becomes false.
    '''
    log.tracef("Clearing the diagnosis entry for %s on diagram %s in project %s...", finalDiagnosisName, diagramPath, projectName)

    from ils.diagToolkit.common import fetchApplicationNameForDiagram
    applicationName = fetchApplicationNameForDiagram(diagramPath, database)
    if applicationName == None:
        log.error("ERROR clearing a diagnosis entry for %s - %s because an application could not be found!" % (diagramPath, finalDiagnosisName))
        return
    
    from ils.diagToolkit.common import fetchFinalDiagnosisId
    finalDiagnosisId = fetchFinalDiagnosisId(diagramPath, finalDiagnosisName, database)
    if finalDiagnosisId == None:
        log.error("ERROR clearing a diagnosis entry for %s - %s because the final diagnosis was not found!" % (diagramPath, finalDiagnosisName))
        return    

    # If there was an active diagnosis entry then set its recommendation status to RESCINDED and its state to INACTIVE
    SQL = "update DtDiagnosisEntry set RecommendationStatus = '%s', Status = 'InActive' where FinalDiagnosisId = %d and Status = 'Active'" % (RECOMMENDATION_RESCINDED, finalDiagnosisId)
    logSQL.tracef(SQL)
    rows = system.db.runUpdateQuery(SQL, database)
    log.tracef("Cleared %d diagnosis entries", rows)

    # PAH 1/22/17 consolidated this SQL with the one above that had the same where clause...
#    SQL = "update DtDiagnosisEntry set Status = 'InActive' where FinalDiagnosisId = %d and Status = 'Active'" % (finalDiagnosisId)
#    logSQL.tracef(SQL)
#    rows = system.db.runUpdateQuery(SQL, database)
#   log.info("...cleared %d diagnosis entries" % (rows))
    
    # Set the state of the Final Diagnosis to InActive
    SQL = "update DtFinalDiagnosis set State = 0, Active = 0 where FinalDiagnosisId = %d" % (finalDiagnosisId)
    logSQL.tracef(SQL)
    rows = system.db.runUpdateQuery(SQL, database)
    log.tracef("...cleared %d final diagnosis", rows)
    
    requestToManage(applicationName, database, provider)


def recalcMessageHandler(payload):
    '''
    Unpack the payload into arguments and call the method that posts a diagnosis entry.
    This only runs in the gateway.  I'm not sure who calls this - this might be to facilitate testing, but I'm not sure.
    '''
    log.infof("In %s.recalcMessageHandler, the payload is: %s", __name__, str(payload))
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
        log.tracef("Handling recalc message for project: %s, post: %s, application: %s", project, post, applicationName)
        
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
    log.tracef("In postRecommendationMessage(), the recommendations are: %s", str(recommendations))

    fdTextRecommendation = fetchTextRecommendation(finalDiagnosisId, database)
    textRecommendation = "The %s has detected %s. %s." % (application, finalDiagnosis, fdTextRecommendation)

    if len(recommendations) == 0:
        textRecommendation = textRecommendation + "\nNo Outputs Calculated"
    else:
        textRecommendation = textRecommendation + "\nOutputs are:"
    
    for recommendation in recommendations:
        autoOrManual=recommendation.get('AutoOrManual', None)
        outputName = recommendation.get('QuantOutput','')
        
        SQL = "Select MinimumIncrement, IgnoreMinimumIncrement, FD.TrapInsignificantRecommendations "\
            " from DtQuantOutput QO, DtRecommendationDefinition RD, DtFinalDiagnosis FD "\
            " where QO.QuantOutputId = RD.QuantOutputId "\
            " and RD.FinalDiagnosisId = FD.FinalDiagnosisId "\
            " and QO.QuantOutputName = '%s' "\
            " and RD.FinalDiagnosisId = %s" % (outputName, str(finalDiagnosisId))
        pds=system.db.runQuery(SQL, database)
        if len(pds) != 1:
            return "Error fetching QuantOutput configuration: %s" % (SQL)
        record = pds[0]
        minimumIncrement=record["MinimumIncrement"]
        ignoreMinimumIncrement=record["IgnoreMinimumIncrement"]
        trapInsignificantRecommendationsQuantOutput = not(ignoreMinimumIncrement)
        trapInsignificantRecommendations = record["TrapInsignificantRecommendations"]
        
        if autoOrManual == 'Auto':
            val = recommendation.get('AutoRecommendation', None)
            if trapInsignificantRecommendationsQuantOutput:
                textRecommendation = "%s\n%s = %s" % (textRecommendation, outputName, str(val))
            elif trapInsignificantRecommendations:
                textRecommendation = "%s\n%s = %s (min output = %s)" % (textRecommendation, outputName, str(val), str(minimumIncrement))
            else:
                textRecommendation = "%s\n%s = %s" % (textRecommendation, outputName, str(val))

        elif autoOrManual == 'Manual':
            if trapInsignificantRecommendationsQuantOutput:
                textRecommendation = "%s\nManual move for %s = %s" % (textRecommendation, outputName, str(val))
            elif trapInsignificantRecommendations:
                textRecommendation = "%s\nManual move for %s = %s (min output = %s)" % (textRecommendation, outputName, str(val), str(minimumIncrement))
            else:
                textRecommendation = "%s\nManual move for %s = %s" % (textRecommendation, outputName, str(val))

    from ils.queue.message import insert
    insert("RECOMMENDATIONS", "Info", textRecommendation, database)
    return textRecommendation


def fetchTextRecommendation(finalDiagnosisId, database):
    '''
    Fetch the text recommendation for a final diagnosis from the database.  For FDs that have 
    static text this is easy, but we might need to call a callback that will return dynamic text.
    '''
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


def resetRecommendations(applicationName, log, database):
    ''' 
    Delete all of the recommendations for an Application.  This is in response to a change in the status of a final diagnosis
    and is the first step in evaluating the active FDs and calculating new recommendations.
    '''
    log.tracef("Deleting recommendations for %s", applicationName)
    
    SQL = "delete from DtRecommendation " \
        " where DiagnosisEntryId in (select DE.DiagnosisEntryId "\
        " from DtDiagnosisEntry DE, DtFinalDiagnosis FD, DtDiagram D, DtFamily F, DtApplication A"\
        " where A.ApplicationId = F.ApplicationId "\
        " and F.FamilyId = D.FamilyId "\
        " and D.DiagramId = FD.DiagramId "\
        " and FD.FinalDiagnosisId = DE.FinalDiagnosisId "\
        " and A.ApplicationName = '%s')" % (applicationName)
    log.tracef(SQL)
    rows=system.db.runUpdateQuery(SQL, database)
    log.tracef("...deleted %d quantitative recommendations...", rows)
    
    SQL = "delete from DtTextRecommendation " \
        " where DiagnosisEntryId in (select DE.DiagnosisEntryId "\
        " from DtDiagnosisEntry DE, DtFinalDiagnosis FD, DtDiagram D, DtFamily F, DtApplication A"\
        " where A.ApplicationId = F.ApplicationId "\
        " and F.FamilyId = D.FamilyId "\
        " and D.DiagramId = FD.DiagramId "\
        " and FD.FinalDiagnosisId = DE.FinalDiagnosisId "\
        " and A.ApplicationName = '%s')" % (applicationName)
    log.tracef(SQL)
    rows=system.db.runUpdateQuery(SQL, database)
    log.tracef("...deleted %d text recommendations...", rows)


# Update the quant outputs for an applicatuon.
def resetOutputs(applicationName, log, database):
    log.tracef("Resetting QuantOutputs for application %s", applicationName)
    
    SQL = "update DtQuantOutput " \
        " set Active = 0, FeedbackOutputManual = 0.0, ManualOverride = 0 where ApplicationId in (select ApplicationId "\
        " from DtApplication where ApplicationName = '%s') and Active = 1" % (applicationName)
    
    ''' 8/12/2020 - PAH - removed constraint to only reset active quantOutputs '''
    SQL = "update DtQuantOutput " \
        " set Active = 0, FeedbackOutputManual = 0.0, ManualOverride = 0 where ApplicationId in (select ApplicationId "\
        " from DtApplication where ApplicationName = '%s')" % (applicationName)
        
    log.tracef(SQL)
    rows=system.db.runUpdateQuery(SQL, database)
    log.tracef("...reset %d QuantOutputs...", rows)
        
        
# This replaces _em-manage-diagnosis().  Its job is to prioritize the active diagnosis for an application diagnosis queue.
def manage(application, recalcRequested=False, database="", provider=""):
    log.info("Managing diagnosis for application: %s using database %s and tag provider %s" % (application, database, provider))

    #---------------------------------------------------------------------
    # Merge the list of output dictionaries for a final diagnosis into the list of all outputs
    def mergeOutputs(quantOutputs, fdQuantOutputs):
        log.tracef("Merging outputs %s into %s" % (str(fdQuantOutputs), str(quantOutputs)))
        for fdQuantOutput in fdQuantOutputs:
            fdId = fdQuantOutput.get('QuantOutputId', -1)
            found = False
            for quantOutput in quantOutputs:
                qoId = quantOutput.get('QuantOutputId', -1)
                if fdId == qoId:
                    '''
                    The quant output already exists in the list so don't overwrite it
                    Some explanation is needed here.  TrapInsignificantRecommendations is defined on a Final Diagnosis, but at this point
                    we have combining quant outputs from multiple FDs.  So what do we do if one is set to trap and the other isn't.
                    I'm not sure there is a right answer, plenty of opinions...
                    This is only a problem if multiple FDs are active at the dsame time AND have the same priorities - so I think this is a small
                    subset of all of the use of the toolkit - so even if I get the answer wrong here, it's impact should be small.
                    '''
                    trapInsignificantRecommendations1 = fdQuantOutput.get('TrapInsignificantRecommendations', False)
                    trapInsignificantRecommendations2 = quantOutput.get('TrapInsignificantRecommendations', False)
                    trapInsignificantRecommendations = trapInsignificantRecommendations1  or trapInsignificantRecommendations2
                    fdQuantOutput['TrapInsignificantRecommendations'] = trapInsignificantRecommendations
                    
                    found = True
            if not(found):
                quantOutputs.append(fdQuantOutput)
        return quantOutputs

    #---------------------------------------------------------------------    
    # There are two lists.  The first is a list of all quant outputs and the second is the list of all recommendations.
    # Merge the lists into one so the recommendations are with the appropriate output
    def mergeRecommendations(quantOutputs, recommendations):
        log.tracef("Merging recommendation: %s into outputs %s ", str(recommendations), str(quantOutputs))
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
        log.tracef("...outputs merged with recommendations are: %s", str(quantOutputs))
        return quantOutputs

    #---------------------------------------------------------------------
    # Sort out the families with the highest family priorities - this works because the records are fetched in 
    # descending order.  Remember that the highest priority is the lowest number (i.e. priority 1 is more important 
    # than priority 10.
    def selectHighestPriorityFamilies(pds):
        
        aList = []
        log.tracef("The families with the highest priorities are: ")
        highestPriority = pds[0]['FamilyPriority']
        for record in pds:
            if record['FamilyPriority'] == highestPriority:
                log.tracef("  Family: %s, Family Priority: %f, Final Diagnosis: %s, Final Diagnosis Priority: %f", record['FamilyName'], record['FamilyPriority'], record['FinalDiagnosisName'], record['FinalDiagnosisPriority'])
                aList.append(record)
        
        return aList
    
    #---------------------------------------------------------------------
    # Filter out low priority diagnosis where there are multiple active diagnosis within the same family
    def selectHighestPriorityDiagnosisForEachFamily(aList):
        log.tracef("Filtering out low priority diagnosis for families with multiple active diagnosis...")
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
                log.tracef("   ...removing %s because it's priority %f is greater than the most important priority %f", record["FinalDiagnosisName"], finalDiagnosisPriority, mostImportantPriority)
        return bList
    
    #---------------------------------------------------------------------
    # Whatever is Active must have been the highest priority
    def fetchPreviousHighestPriorityDiagnosis(applicationName, database):
        log.tracef("Fetching the previous highest priority diagnosis...")
        SQL = "Select FinalDiagnosisName, FinalDiagnosisId "\
            " from DtApplication A, DtFamily F, DtDiagram D, DtFinalDiagnosis FD "\
            " where A.ApplicationName = '%s' " \
            " and A.ApplicationId = F.ApplicationId "\
            " and F.FamilyId = D.FamilyId "\
            " and D.DiagramId = FD.DiagramId "\
            " and FD.Active = 1"\
            % (applicationName)
        logSQL.tracef(SQL)
        pds = system.db.runQuery(SQL, database)
        aList=[]
        
        if len(pds) == 0:
            log.tracef("There were NO previous active priorities!")
        else:
            for record in pds:
                aList.append(record["FinalDiagnosisId"])
                log.tracef("   %s - %d", record["FinalDiagnosisName"], record["FinalDiagnosisId"])

        return aList

    #---------------------------------------------------------------------
    def setActiveDiagnosisFlag(alist, database):
        log.tracef("Updating the 'active' flag for FinalDiagnosis...")
        # First clear all of the active flags in 
        families = []   # A list of quantOutput dictionaries
        for record in alist:
            familyId = record['FamilyId']
            if familyId not in families:
                log.tracef("   ...clearing all FinalDiagnosis in family %s...", str(familyId))
                families.append(familyId)
                SQL = "update dtFinalDiagnosis set Active = 0 where DiagramId in (select DiagramId from DtDiagram where FamilyId = %d)" % (familyId)
                logSQL.tracef(SQL)
                rows=system.db.runUpdateQuery(SQL, database)
                log.tracef("      updated %d rows!", rows)

        # Now set the ones that are active...
        for record in alist:
            finalDiagnosisId = record['FinalDiagnosisId']
            log.tracef("   ...setting Final Diagnosis %d to active...", finalDiagnosisId)
            SQL = "update dtFinalDiagnosis set Active = 1, LastRecommendationTime = getdate() where FinalDiagnosisId = %d" % (finalDiagnosisId)
            logSQL.tracef(SQL)
            rows = system.db.runUpdateQuery(SQL, database)
            log.tracef("      updated %d rows!", rows)
    
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
        log.tracef("   old list: %s", str(oldList))
        log.tracef("   new list: %s", str(newList))
        
        # If the lengths of the lists are different then they must be different!
        if len(oldList) != len(newList):
            changed=True
        
        lowPriorityList=[]
        for fdId in oldList:
            if fdId not in newList:
                changed=True
                lowPriorityList.append(fdId)

        if changed:
            log.tracef("   the low priority final diagnosis are: %s", str(lowPriorityList))

        return changed, lowPriorityList

    #-------------------------------------------------------------------
    def rescindLowPriorityDiagnosis(lowPriorityList, database):
        log.tracef("...rescinding low priority diagnosis...")
        for fdId in lowPriorityList:
            log.tracef("   ...rescinding recommendations for final diagnosis id: %d...", fdId)
            SQL = "delete from DtRecommendation where DiagnosisEntryId in "\
                " (select DiagnosisEntryId from DtDiagnosisEntry "\
                " where Status = 'Active' and RecommendationStatus = '%s' "\
                " and FinalDiagnosisId = %d)" % (RECOMMENDATION_REC_MADE, fdId)
            logSQL.tracef("      %s", SQL)
            rows=system.db.runUpdateQuery(SQL, database)
            log.tracef("      ... deleted %d quantitative recommendations...", rows)
            
            SQL = "delete from DtTextRecommendation where DiagnosisEntryId in "\
                " (select DiagnosisEntryId from DtDiagnosisEntry "\
                " where Status = 'Active' and RecommendationStatus = '%s' "\
                " and FinalDiagnosisId = %d)" % (RECOMMENDATION_REC_MADE, fdId)
            logSQL.tracef("      %s", SQL)
            rows=system.db.runUpdateQuery(SQL, database)
            log.tracef("      ... deleted %d text recommendations...", rows)

            SQL = "update DtFinalDiagnosis set Active = 0 "\
                "where FinalDiagnosisId = %d" % (fdId)
            logSQL.tracef(SQL)
            rows = system.db.runUpdateQuery(SQL, database)
            log.tracef("      ...updated %d final diagnosis Active flag to False", rows)

            SQL = "update DtDiagnosisEntry set RecommendationStatus = '%s'"\
                "where Status = 'Active' and RecommendationStatus = '%s' "\
                " and FinalDiagnosisId = %d" % (RECOMMENDATION_RESCINDED, RECOMMENDATION_REC_MADE, fdId)
            logSQL.tracef(SQL)
            rows = system.db.runUpdateQuery(SQL, database)
            log.tracef("      ...updated %d diagnosis entries recommendation state to %s...", rows, RECOMMENDATION_REC_MADE)

    #-------------------------------------------------------------------
    def rescindActiveDiagnosis(application, database):
        log.tracef("...rescinding **active** diagnosis and deleting recommendations for application %s...", application)

        SQL = "select R.RecommendationId "\
            "from DtRecommendation R, DtDiagnosisEntry DE, DtFinalDiagnosis FD, DtDiagram D, DtFamily F, DtApplication A"\
              " where R.DiagnosisEntryId = DE.DiagnosisEntryId "\
              " and DE.FinalDiagnosisId = FD.FinalDiagnosisId "\
              " and FD.DiagramId = D.DiagramId "\
              " and D.FamilyId = F.FamilyId "\
              " and F.ApplicationId = A.applicationId "\
              " and A.applicationName = '%s'" % (application)
        
        pds = system.db.runQuery(SQL, database)
        totalRows=0
        for record in pds:
            recommendationId=record["RecommendationId"]
            SQL = "delete from DtRecommendation where RecommendationId = %d" % (recommendationId)
            rows=system.db.runUpdateQuery(SQL)
            totalRows=totalRows+rows
        log.tracef("     ...deleted %d quantitative recommendations...", totalRows)
        
        # Delete active text recommendations
        SQL = "select DE.DiagnosisEntryId "\
            " from DtTextRecommendation TR, DtDiagnosisEntry DE, DtFinalDiagnosis FD, DtDiagram D, DtFamily F, DtApplication A"\
            " where TR.DiagnosisEntryId = DE.DiagnosisEntryId "\
            " and DE.FinalDiagnosisId = FD.FinalDiagnosisId "\
            " and FD.DiagramId = D.DiagramId "\
            " and D.FamilyId = F.FamilyId "\
            " and F.ApplicationId = A.applicationId "\
            " and A.applicationName = '%s' " % (application)

        pds = system.db.runQuery(SQL, database)
        totalRows=0
        for record in pds:
            diagnosisEntryId=record["DiagnosisEntryId"]
            SQL = "delete from DtTextRecommendation where DiagnosisEntryId = %d" % (diagnosisEntryId)
            rows=system.db.runUpdateQuery(SQL)
            totalRows=totalRows+rows
        log.tracef("     ...deleted %d text recommendations...", totalRows)

        # Update the Quant Outputs 
        log.tracef("...rescinding active recommendations for %s...", application)
        resetOutputs(application, log, database)

        SQL = "update DtDiagnosisEntry set RecommendationStatus = '%s'"\
            "where Status = 'Active' and RecommendationStatus = '%s' "\
            " and FinalDiagnosisId in "\
            "(select FD.FinalDiagnosisId "\
            " from DtDiagnosisEntry DE, DtFinalDiagnosis FD, DtDiagram D, DtFamily F, DtApplication A "\
            " where DE.Status = 'Active' "\
            " and DE.FinalDiagnosisId = FD.FinalDiagnosisId "\
            " and FD.DiagramId = D.DiagramId "\
            " and D.FamilyId = F.FamilyId "\
            " and F.ApplicationId = A.applicationId "\
            " and A.ApplicationName = '%s')" % (RECOMMENDATION_RESCINDED, RECOMMENDATION_REC_MADE, application)
        logSQL.tracef(SQL)
        rows = system.db.runUpdateQuery(SQL, database)
        log.tracef("      ...rescinded %d diagnosis entries!", rows)

    #----------------------------------------------------------------------
    # Is this needed / called??? Why not just call reset application??
    def setDiagnosisEntryErrorStatus(alist, database):
        # Somewhere an error should be logged, but not here
        log.error("Updating the diagnosis entries to indicate an error...")
        
        # First clear all of the active flags in 
        ids = []   # A list of quantOutput dictionaries
        for record in alist:
            finalDiagnosisId = record['FinalDiagnosisId']
            finalDiagnosis = record['FinalDiagnosisName']
            if finalDiagnosisId not in ids:
                log.error("   ...setting error status for active diagnosis entries for final diagnosis: %s..." % (finalDiagnosis))
                ids.append(finalDiagnosisId)
                _setDiagnosisEntryErrorStatus(finalDiagnosisId, database)

    def _setDiagnosisEntryErrorStatus(finalDiagnosisId, database):
        '''
        Update the diagnosis entry and the final diagnosis for an unexpected error.
        '''
        log.error("   ...setting error status for active diagnosis entries for final diagnosis: %d..." % (finalDiagnosisId))
        SQL = "update dtDiagnosisEntry set RecommendationStatus = '%s', status = 'InActive' where FinalDiagnosisId = %d "\
            " and status = 'Active'" % (RECOMMENDATION_ERROR, finalDiagnosisId)
        logSQL.tracef(SQL)
        rows=system.db.runUpdateQuery(SQL, database)
        log.error("      ...updated %d diagnosis entries!" % (rows))
                
        SQL = "update DtFinalDiagnosis set Active = 0 where FinalDiagnosisId = %d" % (finalDiagnosisId)
        logSQL.tracef(SQL)
        rows=system.db.runUpdateQuery(SQL, database)
        log.error("      ...updated %d final diagnosis!" % (rows))
    
    def resetMultipliers(applicationName):
        log.tracef("Resetting the multipliers...")
        SQL = "UPDATE DtDiagnosisEntry "\
            " SET Multiplier = 1.0 "\
            " WHERE Status = 'Active' and FinalDiagnosisId in (select FD.FinalDiagnosisId "\
            " from DtFinalDiagnosis FD, DtDiagram D, DtFamily F, DtApplication A "\
            " where FD.DiagramId = D.DiagramId "\
            " and D.FamilyId = F.familyId "\
            " and F.ApplicationId = A.ApplicationId "\
            " and A.ApplicationName = '%s')" % (applicationName)
        rows = system.db.runUpdateQuery(SQL)
        log.tracef("...reset %d final diagnosis", rows)
        
    #--------------------------------------------------------------------
    # This is the start of manage()
    #--------------------------------------------------------------------
    
    numSignificantRecommendations = 0
    postTextRecommendation = False
    explanation = ""
    diagnosisEntryId = -1
    noChange = False
    zeroChangeThreshold = readTag("[%s]Configuration/DiagnosticToolkit/zeroChangeThreshold" % (provider)).value
    
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

    log.tracef("The active diagnosis are: ")
    for record in pds:
        log.tracef("  Family: %s, Diagram: %s, Final Diagnosis: %s, Constant: %s, Family Priority: %s, FD Priority: %s, Diagnosis Entry id: %s, Group Ramp Method: %s", 
                  record["FamilyName"], record["DiagramName"], record["FinalDiagnosisName"], str(record["Constant"]), str(record["FamilyPriority"]), 
                   str(record["FinalDiagnosisPriority"]), str(record["DiagnosisEntryId"]), record['GroupRampMethod'] )
    
    # Sort out the families with the highest family priorities - this works because the records are fetched in 
    # descending order.
    from ils.common.database import toDict
    list0 = toDict(pds)
    list1 = selectHighestPriorityFamilies(list0)

    # Sort out diagnosis where there are multiple diagnosis for the same family
    list2 = selectHighestPriorityDiagnosisForEachFamily(list1)
    
    # Calculate the recommendations for each final diagnosis
    log.tracef("The families / final diagnosis with the highest priorities are: ")
    for record in list2:
        log.tracef("  Family: %s, Diagram: %s, Final Diagnosis: %s (%d), Constant: %s, Family Priority: %s, FD Priority: %s, Diagnosis Entry id: %s, Group Ramp Method: %s",
                  record["FamilyName"], record["DiagramName"], record["FinalDiagnosisName"],record["FinalDiagnosisId"], str(record["Constant"]), 
                   str(record["FamilyPriority"]), str(record["FinalDiagnosisPriority"]), str(record["DiagnosisEntryId"]), record['GroupRampMethod'] )
    
    log.tracef("Checking if there has been a change in the highest priority final diagnosis...")
    changed,lowPriorityList=compareFinalDiagnosisState(oldList, list2)
    
    if not(changed) and not(recalcRequested):
        log.tracef("There has been no change in the most important diagnosis, nothing new to manage, so exiting!")
        noChange = True
        return "", numSignificantRecommendations, postTextRecommendation, noChange

    # There has been a change in what the most important diagnosis is so set the active flag
    if recalcRequested:
        log.tracef("Continuing to make recommendations because a recalc was requested...")
    else:
        log.tracef("Continuing to make recommendations because there was a change in the highest priority active final diagnosis...")

    log.tracef("...deleting existing recommendations for %s...", application)
    resetRecommendations(application, log, database)
    
    log.tracef("...resetting the QuantOutput active flag for %s...", application)
    resetOutputs(application, log, database)
    
    rescindLowPriorityDiagnosis(lowPriorityList, database)
    setActiveDiagnosisFlag(list2, database)

    log.tracef("--- Calculating recommendations ---")
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
        groupRampMethod = record["GroupRampMethod"]
        
        log.tracef("Making a recommendation for application: %s, family: %s, final diagnosis:%s (%d), Constant: %s, Group Ramp Method: %s", applicationName, familyName, finalDiagnosisName, finalDiagnosisId, str(constantFD), groupRampMethod)

        # There could be multiple Final Diagnosis that are of equal priority, so we can't just bail if the first one is constant or a text recommendation

        if constantFD:
            # Update the Diagnosis Entry status to be posted
            log.tracef("Setting diagnosis entry recommendation status to POSTED for a contant FD")
            SQL = "Update DtDiagnosisEntry set RecommendationStatus = '%s' where DiagnosisEntryId = %d" % (RECOMMENDATION_POSTED, diagnosisEntryId)
            system.db.runUpdateQuery(SQL)

        else:
            from ils.diagToolkit.recommendation import makeRecommendation
            recommendations, explanation, recommendationStatus = makeRecommendation(applicationName, familyName, finalDiagnosisName, finalDiagnosisId,
                diagnosisEntryId, constantFD, calculationMethod, postTextRecommendation, textRecommendation, zeroChangeThreshold, database, provider)
        
            # Fetch all of the quant outputs for the final diagnosis
            from ils.diagToolkit.common import fetchOutputsForFinalDiagnosis
            pds, fdQuantOutputs = fetchOutputsForFinalDiagnosis(applicationName, familyName, finalDiagnosisName, database)
            quantOutputs = mergeOutputs(quantOutputs, fdQuantOutputs)

            log.tracef("-----------------")
            log.tracef( "Recommendations: %s", str(recommendations))
            log.tracef( "    Explanation: %s", explanation)
            log.tracef( "         Status: %s", recommendationStatus)
            log.tracef( "      Outputs: %s", str(fdQuantOutputs))
            log.tracef( "-----------------")

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
                SQL = "Update DtDiagnosisEntry set RecommendationStatus = '%s' where DiagnosisEntryId = %d " % (RECOMMENDATION_NONE_MADE, diagnosisEntryId)
                logSQL.tracef(SQL)
                system.db.runUpdateQuery(SQL, database)
                return "None Made", numSignificantRecommendations, False, noChange
    
            quantOutputs = mergeRecommendations(quantOutputs, recommendations)
            log.tracef( "-----------------")
            log.tracef( "Quant Outputs (after merge): %s", str(quantOutputs))
            log.tracef( "-----------------")
            
            if postTextRecommendation and explanation != "":
                originalExplanation = explanation
                if showExplanationWithRecommendation and len(staticExplanation) > 0:
                    explanation = "<HTML>" + staticExplanation + "<br><br>" + explanation
                else:
                    explanation = "<HTML>" + explanation
    
                explanations.append({"explanation": explanation, "diagnosisEntryId": diagnosisEntryId})
                writeToLogbook = readTag("[%s]Configuration/DiagnosticToolkit/writeTextRecommendationsToLogbook" % provider)
                if writeToLogbook:
                    writeTextRecommendationsToLogbook(applicationName, post, staticExplanation, originalExplanation, database)

    log.tracef("--- Recommendations have been made, now calculating the final recommendations ---")
    finalQuantOutputs = []
    
    ''' Determine the ramptime if there are multiple ramp recommendations '''
    from ils.diagToolkit.recommendation import determineRampTime
    groupRampTime = determineRampTime(quantOutputs, groupRampMethod)
    
    for quantOutput in quantOutputs:
        from ils.diagToolkit.recommendation import calculateFinalRecommendation
        quantOutputName = quantOutput.get("QuantOutput", "Unknown")
        quantOutput = calculateFinalRecommendation(quantOutput, groupRampTime)
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
                log.tracef("Performing an automatic NO-DOWNLOAD because there was an error reading current values during bounds checking for %s...", quantOutputName) 
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
    log.tracef("Done managing, the final outputs are: %s", str(finalQuantOutputs))
    updateApplicationDownloadStatus(application, 'ACTIVE', database)
    quantOutputIds=[]
    for quantOutput in finalQuantOutputs:
        quantOutputIds.append(quantOutput.get("QuantOutputId", -1))
        updateQuantOutput(quantOutput, database, provider)
    
    log.tracef("...the explanations are: %s", str(explanations))
    
    postTextRecommendation = False
    if constantFD:
        log.tracef(" --- handling a constant final diagnosis (by doing nothing) ---")
    elif len(explanations) > 0:
        log.tracef(" --- handling %d text recommendation(s) ---", len(explanations))
        log.tracef("%s", str(explanations))
        postTextRecommendation = True

        for explanationDictionary in explanations:
            SQL = "Insert into DtTextRecommendation (DiagnosisEntryId, TextRecommendation) values (%d, '%s')" % (explanationDictionary['diagnosisEntryId'], escapeSqlQuotes(explanationDictionary['explanation']))
            system.db.runUpdateQuery(SQL, database=database)

        # Let whoever initiated the manage deal with the notification 
#        projectName = system.util.getProjectName()
#        notifyClientsOfTextRecommendation(projectName, post, application, explanation, diagnosisEntryId, database, provider)
    elif numSignificantRecommendations == 0:
        log.tracef("There are no significant recommendations - Performing an automatic NO-DOWNLOAD because there are no significant recommendations for final diagnosis %s - %s..." % (str(finalDiagnosisId), finalDiagnosisName)) 
        resetApplication(post=post, application=applicationName, families=[familyName], finalDiagnosisIds=[finalDiagnosisId], 
                         quantOutputIds=quantOutputIds, actionMessage=AUTO_NO_DOWNLOAD, recommendationStatus=AUTO_NO_DOWNLOAD, 
                         database=database, provider=provider)
        notificationText = RECOMMENDATION_NO_SIGNIFICANT_RECOMMENDATIONS
        
        '''
        If we auto-nodownload on the highest priority problem, we should do another manage just to check if there is an active lower priority problem.
        '''
        requestToManage(applicationName, database, provider)
    else:
        log.tracef("Finished managing recommendations - there are %d significant Quant Outputs (There are %d quantOutputs)", numSignificantRecommendations, len(finalQuantOutputs))
    
    return notificationText, numSignificantRecommendations, postTextRecommendation, noChange

# Check that recommendation against the bounds configured for the output
def checkBounds(applicationName, quantOutput, quantOutputName, database, provider):

    log.tracef("   ...checking Bounds...")
    log.tracef("    Quant Output: %s", str(quantOutput))
    madeSignificantRecommendation=True
    # The feedbackOutput can be incremental or absolute
    feedbackOutput = quantOutput.get('FeedbackOutput', 0.0)
    feedbackOutputManual = quantOutput.get('FeedbackOutputManual', 0.0)
    manualOverride = quantOutput.get('ManualOverride', False)
    incrementalOutput=quantOutput.get('IncrementalOutput')
    mostNegativeIncrement = quantOutput.get('MostNegativeIncrement', -1000.0)
    mostPositiveIncrement = quantOutput.get('MostPositiveIncrement', 1000.0)
    trapInsignificantRecommendations = quantOutput.get('TrapInsignificantRecommendations', True)
        
    # Read the current setpoint - the tagpath in the QuantOutput does not have the provider
    tagpath = '[' + provider + ']' + quantOutput.get('TagPath','unknown')
    outputTagPath = getOutputForTagPath(provider, tagpath, "sp")
    log.tracef("   ...reading the current value of tag: %s", outputTagPath)
    qv=readTag(outputTagPath)
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
    log.tracef("   ...the current value is: %s", str(qv.value))

    # If the recommendation was absolute, then convert it to incremental for the may be absolute or incremental, but we always display incremental    
    if not(incrementalOutput):
        originalAbsoluteRecommendation = feedbackOutput
        feedbackOutput = feedbackOutput - qv.value
        log.tracef("      ...calculating an incremental change for an absolute recommendation(absolute:%s, incremental: %s)...", str(originalAbsoluteRecommendation), str(feedbackOutput))

    # If the operator manually change the recommendation then use it - manual overrides are always incremental
    if manualOverride:
        feedbackOutput = feedbackOutputManual
        log.tracef("      ...using *manual* value: %f ...", feedbackOutput)

    # Compare the recommendation to the **incremental** limits
    log.tracef("      ...comparing the feedback output (%f) to most positive increment (%f) and most negative increment (%f)...", feedbackOutput, mostPositiveIncrement, mostNegativeIncrement)
    if feedbackOutput >= mostNegativeIncrement and feedbackOutput <= mostPositiveIncrement:
        log.tracef("      ...the output is not incremental bound...")
        quantOutput['OutputLimited'] = False
        quantOutput['OutputLimitedStatus'] = 'Not Bound'
        feedbackOutputConditioned=feedbackOutput
    elif feedbackOutput > mostPositiveIncrement:
        log.tracef("      ...the output IS positive incremental bound...")
        quantOutput['OutputLimited'] = True
        quantOutput['OutputLimitedStatus'] = 'Positive Incremental Bound'
        feedbackOutputConditioned=mostPositiveIncrement
    else:
        log.tracef("      ...the output IS negative incremental bound...")
        quantOutput['OutputLimited'] = True
        quantOutput['OutputLimitedStatus'] = 'Negative Incremental Bound'
        feedbackOutputConditioned=mostNegativeIncrement
        
    # Compare the final setpoint to the **absolute** limits
    setpointHighLimit = quantOutput.get('SetpointHighLimit', -1000.0)
    setpointLowLimit = quantOutput.get('SetpointLowLimit', 1000.0)
    log.tracef("      ...comparing the proposed setpoint (%f) to high limit (%f) and low limit (%f)...", (qv.value + feedbackOutputConditioned), setpointHighLimit, setpointLowLimit)

    # For the absolute limits we need to add the current value to the incremental change before comparing to the absolute limits
    if qv.value + feedbackOutputConditioned > setpointHighLimit:
        log.tracef("      ...the output IS Positive Absolute Bound...")
        quantOutput['OutputLimited'] = True
        quantOutput['OutputLimitedStatus'] = 'Positive Absolute Bound'
        feedbackOutputConditioned=setpointHighLimit - qv.value
    elif qv.value + feedbackOutputConditioned < setpointLowLimit:
        log.tracef("      ...the output IS Negative Absolute Bound...")
        quantOutput['OutputLimited'] = True
        quantOutput['OutputLimitedStatus'] = 'Negative Absolute Bound'
        feedbackOutputConditioned=setpointLowLimit - qv.value

    # Now check the minimum increment requirement
    minimumIncrement = quantOutput.get('MinimumIncrement', 1000.0)
    ignoreMinimumIncrement = quantOutput.get('IgnoreMinimumIncrement', False)
    log.tracef("Ignore Minimum Increment: %s", str(ignoreMinimumIncrement))
    trapInsignificantRecommendations = quantOutput.get('TrapInsignificantRecommendations', False)
    log.tracef("trapInsignificantRecommendations: %s", str(trapInsignificantRecommendations))

    if (trapInsignificantRecommendations and not(ignoreMinimumIncrement)) and abs(feedbackOutputConditioned) < minimumIncrement:
        log.tracef("      ...the output IS Minimum change bound because the change (%f) is less then the minimum change amount (%f)...", feedbackOutputConditioned, minimumIncrement)
        quantOutput['OutputLimited'] = True
        quantOutput['OutputLimitedStatus'] = 'Minimum Change Bound'
        feedbackOutputConditioned=0.0
        quantOutput['FeedbackOutputConditioned']=feedbackOutputConditioned
        madeSignificantRecommendation=False

    finalIncrementalValue = feedbackOutputConditioned
    
    # If the recommendation was absolute, then convert it back to absolute
    if not(incrementalOutput) and not(manualOverride):
        log.tracef("      ...converting an incremental change (%s) back to an absolute recommendation (%s)...", str(feedbackOutputConditioned), str(qv.value + feedbackOutputConditioned))
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
        
        log.tracef("   ...the output is bound - taking %f percent of the recommended change...", outputPercent)
        quantOutput['OutputPercent'] = outputPercent
        from ils.diagToolkit.common import updateBoundRecommendationPercent
        updateBoundRecommendationPercent(quantOutput['QuantOutputId'], outputPercent, database)
    
    log.tracef("   The recommendation after bounds checking is:")
    log.tracef("          Feedback Output Conditioned: %f", feedbackOutputConditioned)
    log.tracef("                       Output limited: %s", str(quantOutput['OutputLimited']))
    log.tracef("                Output limited status: %s", quantOutput['OutputLimitedStatus'])
    log.tracef("                       Output percent: %f", quantOutput['OutputPercent'])
    return quantOutput, madeSignificantRecommendation

def calculateVectorClamps(quantOutputs, provider):
    log.tracef("Checking vector clamping with tag provider: %s...", provider)
    tagName="[%s]Configuration/DiagnosticToolkit/vectorClampMode" % (provider)
    
    tagExists=system.tag.exists(tagName)
    if tagExists:
        qv=readTag(tagName)
        vectorClampMode = string.upper(qv.value)
    else:
        vectorClampMode = "DISABLED"
        log.error("Unable to read vector clamp configuration from %s because it does not exist - setting clamp mode to DISABLED" % (tagName))
    
    if vectorClampMode == "DISABLED":
        log.tracef("...Vector Clamps are NOT enabled")
        return quantOutputs, ""
    
    log.tracef("...Vector clamp mode: %s", vectorClampMode)

    # There needs to be at least two outputs that are not minimum change bound for vector clamps to be appropriate
    i = 0
    for quantOutput in quantOutputs:
        if quantOutput['OutputLimitedStatus'] != 'Minimum Change Bound':
            i = i + 1

    if i < 2:
        log.tracef("Vector clamps do not apply when there is only one output")
        return quantOutputs, ""

    # The first step is to find the most restrictive clamp
    minOutputRatio=100.0
    for quantOutput in quantOutputs:
        if quantOutput['OutputLimitedStatus'] != 'Minimum Change Bound':
            if quantOutput['OutputPercent'] < minOutputRatio:
                boundOutput=quantOutput
                minOutputRatio = quantOutput['OutputPercent']
        else:
            log.tracef("...not considering %s which is minimum change bound...", quantOutput['QuantOutput'])
            
    if minOutputRatio == 100.0:
        log.tracef("No outputs are clamped, therefore there is not a vector clamp")
        return quantOutputs, ""

    log.tracef("All outputs will be clamped at %f pct", minOutputRatio)

    finalQuantOutputs = []
    txt = "The most bound output is %s, %.2f pct of the total recommendation of %.4f, which equals %.4f, will be implemented." % \
        (boundOutput['QuantOutput'], minOutputRatio, boundOutput['FeedbackOutput'], boundOutput['FeedbackOutputConditioned'])
        
    for quantOutput in quantOutputs:
        
        # Look for an output that isn't bound but needs to be Vector clamped
        if quantOutput['OutputPercent'] > minOutputRatio and quantOutput['OutputLimitedStatus'] != 'Minimum Change Bound':
            outputPercent = minOutputRatio
            
            ''' Calculate the vector clamp but don't store it unless the vector clamp mode is implement! '''
            if  quantOutput.get('IncrementalOutput'):
                feedbackOutputConditioned = quantOutput['FeedbackOutput'] * minOutputRatio / 100.0
            else: 
                log.tracef("Adjusting an absolute  recommendation for a vector clamp!")
                SP = quantOutput.get('CurrentValue',None)
                feedbackOutputConditioned = SP + (quantOutput['FeedbackOutput'] - SP)  * (minOutputRatio / 100.0)
                
            txt = "%s\n%s should be reduced from %.4f to %.4f" % (txt, quantOutput['QuantOutput'], quantOutput['FeedbackOutput'], feedbackOutputConditioned)

            # Now check if the new conditioned output is less than the minimum change amount
            minimumIncrement = quantOutput.get('MinimumIncrement', 1000.0)
            ignoreMinimumIncrement = quantOutput.get('IgnoreMinimumIncrement', False)
            if not(ignoreMinimumIncrement) and abs(feedbackOutputConditioned) < minimumIncrement:
                feedbackOutputConditioned = 0.0
                outputPercent = 0.0
                txt = "%s which is an insignificant value value and should be set to 0.0." % (txt)
                    
            if vectorClampMode == 'IMPLEMENT':
                log.tracef('Implementing a vector clamp on %s', quantOutput['QuantOutput'])
                quantOutput['OutputPercent'] = outputPercent
                quantOutput['FeedbackOutputConditioned'] = feedbackOutputConditioned
                quantOutput['OutputLimitedStatus'] = 'Vector'
                quantOutput['OutputLimited']=True

        finalQuantOutputs.append(quantOutput)
            
    log.tracef(txt)
    
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
    
    log.tracef("Updating the database with the recommendations made to QuantOutput: %s", str(quantOutput))
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
    The IO layer also supports ramping of a plain old controller or even ramping an OPC variable or memory tag.  The key that determines if an output
    is ramped is if the recommendation contains a "rampTime" property.  A QuantOutput may be used one time to write an output directly or a ramp setpoint.
    '''

    recommendations = quantOutput.get("Recommendations", [])
    rampTime = None
    for recommendation in recommendations:
        rampTime = recommendation.get("RampTime", None)
        if rampTime <> None:
            log.tracef("*** Found a ramp time ***")
        
    # The current setpoint was read when we checked the bounds.
    isGood = quantOutput.get('CurrentValueIsGood',False)
    if not(isGood):
        # Make this quant-output inactive since we can't make an intelligent recommendation without the current setpoint
        SQL = "update DtQuantOutput set Active = 0 where QuantOutputId = %d " % (quantOutputId)
        logSQL.tracef(SQL)
        system.db.runUpdateQuery(SQL, database)
        return

    currentSetpoint=quantOutput.get('CurrentValue',None)
    log.tracef("     ...using current setpoint value: %s", str(currentSetpoint))
    
    if manualOverride:
        # Manual values are always incremental
        log.tracef("     ...using the validated manually entered value: %s (raw: %s)... ", str(feedbackOutputConditioned), str(feedbackOutputManual))
        finalSetpoint = currentSetpoint + feedbackOutputConditioned
        displayedRecommendation = feedbackOutputConditioned
    else:
        log.tracef("     ...using the AUTO recommendations... ")
        # The recommendation may be absolute or incremental, but we always display incremental    
        incrementalOutput=quantOutput.get('IncrementalOutput')
        if incrementalOutput:
            finalSetpoint = currentSetpoint + feedbackOutputConditioned
            displayedRecommendation = feedbackOutputConditioned
        else:
            finalSetpoint = feedbackOutputConditioned
            displayedRecommendation = finalSetpoint-currentSetpoint

    log.tracef("   ...the final setpoint is %f, the displayed recommendation is %f", finalSetpoint, displayedRecommendation)

    # Active is hard-coded to True here because these are the final active quantOutputs
    SQL = "update DtQuantOutput set FeedbackOutput = %s, OutputLimitedStatus = '%s', OutputLimited = %d, "\
        " OutputPercent = %s, FeedbackOutputManual = %s, FeedbackOutputConditioned = %s, DownloadAction = 'GO', DownloadStatus = '', "\
        " ManualOverride = %d, Active = 1, CurrentSetpoint = %s, FinalSetpoint = %s, DisplayedRecommendation = %s "\
        " where QuantOutputId = %d "\
        % (str(feedbackOutput), outputLimitedStatus, outputLimited, str(outputPercent), str(feedbackOutputManual), str(feedbackOutputConditioned), \
           manualOverride, str(currentSetpoint), str(finalSetpoint), str(displayedRecommendation), quantOutputId)
    
    logSQL.tracef(SQL)
    system.db.runUpdateQuery(SQL, database)
    
    '''
    If this quant output is for a ramp controller, then the recommendation MUST contain a Ramp time 
    (Due to some confusion, when I move the rampTime into the quant output I change the name to Ramp to match the database)
    '''
    ramp = quantOutput.get('Ramp', None)
    if ramp != None:
        SQL = "update DtQuantOutputRamp set Ramp = %s where QuantOutputId = %d " % (str(ramp), quantOutputId)
        logSQL.tracef(SQL)
        rows = system.db.runUpdateQuery(SQL, database)
        if rows > 0:
            log.tracef("   ...updated a quantOutputRamp record...")
        else:
            rampTypeId = lookup("RampType", "Time")
            SQL = "insert into DtQuantOutputRamp (QuantOutputId, Ramp, RampTypeId) values (%d, %f, %d)" % (quantOutputId, ramp, rampTypeId)
            logSQL.tracef(SQL)
            system.db.runUpdateQuery(SQL, database)
            log.tracef("   ...inserted a quantOutputRamp record...")
    else:
        ''' If there isn't a ramp time in the recommendation then make sure that there isn't a ramp record for the quant output '''
        SQL = "delete from DtQuantOutputRamp where QuantOutputId = %d" % (quantOutputId)
        rows = system.db.runUpdateQuery(SQL, database)
        if rows > 0:
            log.tracef("Deleted a DtQuantOutputRamp record for a non-ramp recommendation")

# Set the flag for all of the outputs used by this FD to ignore the minimumIncrement specifications.  This MUST
# be called in the FDs calculation method and only lasts until another FinalDiagnosis using the same QusantOutput becomes active 
def bypassOutputLimits(finalDiagnosisId, database=""):
    log.tracef("Bypassing output limits...")
    rows = setOutputLimits(finalDiagnosisId, 1, database)
    log.tracef("...bypassed %d rows!", rows)
    
# Reset the flag that enforces the minimumIncrement specifications.  This is called for a FD every time it becomes active.
def resetOutputLimits(finalDiagnosisId, database=""):
    log.tracef("Resetting output limits...")
    rows = setOutputLimits(finalDiagnosisId, 0, database)
    log.tracef("...reset %d rows!", rows)

def setOutputLimits(finalDiagnosisId, state, database=""):
    SQL = "Update DtQuantOutput set IgnoreMinimumIncrement = %d "\
        " where QuantOutputId in ("\
        " select QuantOutputId "\
        " from DtFinalDiagnosis FD, DtRecommendationDefinition RD "\
        " where FD.FinalDiagnosisId = %d "\
        " and FD.FinalDiagnosisId = RD.FinalDiagnosisId)" % (state, finalDiagnosisId)
    rows = system.db.runUpdateQuery(SQL, database)
    return rows

def writeTextRecommendationsToLogbook(applicationName, post, staticExplanation, explanation, db):
    log.tracef("Writing a text recommendation to the logbook: %s  %s", staticExplanation, explanation)

    if staticExplanation not in ("", None):
        txt = staticExplanation + "  " + explanation
    else:
        txt = explanation
        
    ''' Write the text recommendation to the application Queue '''
    insertApplicationQueueMessage(applicationName, txt, QUEUE_INFO, db)
    
    ''' Write the text recommendation to the operator logbook '''
    txt = addHTML(txt)
    insertForPost(post, txt, db)