'''
Created on Sep 12, 2014

@author: Pete
'''

#
# Everywhere provider is used here, assume it does not have square brackets
#

import system, string
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
from ils.diagToolkit.common import fetchPostForApplication

log = LogUtil.getLogger("com.ils.diagToolkit.recommendation")
logSQL = LogUtil.getLogger("com.ils.diagToolkit.SQL")

def notifyClients(project, console, notificationText):
    log.trace("Notifying %s-%s client to open/update the setpoint spreadsheet..." % (project, console))
    log.trace("   ...notification text: <%s>" % (notificationText))
    system.util.sendMessage(project=project, messageHandler="consoleManager", 
                            payload={'type':'setpointSpreadsheet', 'console':console, 'notificationText':notificationText}, scope="C")

# Unpack the payload into arguments and call the method that posts a diagnosis entry.  
# This only runs in the gateway.  I'm not sure who calls this - this might be to facilitate testing, but I'm not sure
def postDiagnosisEntryMessageHandler(payload):
    print "The payload is: ", payload

    application=payload["application"]
    family=payload["family"]
    finalDiagnosis=payload["finalDiagnosis"]
    UUID=payload["UUID"]
    diagramUUID=payload["diagramUUID"]
    database=payload["database"]
    
    postDiagnosisEntry(application, family, finalDiagnosis, UUID, diagramUUID, database)

# Insert a record into the diagnosis queue
def postDiagnosisEntry(application, family, finalDiagnosis, UUID, diagramUUID, database="", provider=""):
    log.trace("Post a diagnosis entry for application: %s, family: %s, final diagnosis: %s" % (application, family, finalDiagnosis))
    
    # Lookup the application Id
    from ils.diagToolkit.common import fetchFinalDiagnosis
    record = fetchFinalDiagnosis(application, family, finalDiagnosis, database)
    finalDiagnosisId=record.get('FinalDiagnosisId', None)
    if finalDiagnosisId == None:
        log.error("ERROR posting a diagnosis entry for %s - %s - %s because the final diagnosis was not found!" % (application, family, finalDiagnosis))
        return
    
    unit=record.get('UnitName',None)
    if unit == None:
        log.error("ERROR posting a diagnosis entry for %s - %s - %s because we were unable to locate a unit!" % (application, family, finalDiagnosis))
        return

    grade=system.tag.read("[%s]Site/%s/Grade/Grade" % (provider,unit)).value
    print "The grade is: ", grade
    textRecommendation = record.get('TextRecommendation', 'Unknown Text')
    
    # Insert an entry into the diagnosis queue
    SQL = "insert into DtDiagnosisEntry (FinalDiagnosisId, Status, Timestamp, Grade, TextRecommendation, "\
        "RecommendationStatus, UUID, DiagramUUID, ManualMove, ManualMoveValue, RecommendationMultiplier) "\
        "values (%i, 'Active', getdate(), '%s', '%s', 'NONE-MADE', '%s', '%s', 0, 0.0, 1.0)" \
        % (finalDiagnosisId, grade, textRecommendation, UUID, diagramUUID)
    logSQL.trace(SQL)
    
    try:
        system.db.runUpdateQuery(SQL, database)
    except:
        log.errorf("postDiagnosisEntry. Failed ... update to %s (%s)",database,SQL)

    log.info("Starting to manage diagnosis...")
    notificationText=manage(application, recalcRequested=False, database=database, provider=provider)
    log.info("...back from manage!")
    
    post=fetchPostForApplication(application)
    # This runs in the gateway, but it should work 
    projectName = system.util.getProjectName()
    notifyClients(projectName, post, notificationText)
    
# Clear the final diagnosis (make the status = 'InActive') 
def clearDiagnosisEntry(application, family, finalDiagnosis, database="", provider=""):
    print "Clearing*..."

    from ils.diagToolkit.common import fetchFinalDiagnosis
    record = fetchFinalDiagnosis(application, family, finalDiagnosis, database)
    finalDiagnosisId=record.get('FinalDiagnosisId', None)
    if finalDiagnosisId == None:
        log.error("ERROR clearing a diagnosis entry for %s - %s - %s because the final diagnosis was not found!" % (application, family, finalDiagnosis))
        return    

    # Set the state of the diagnosis entry to InActive
    SQL = "update DtDiagnosisEntry set Status = 'InActive' where FinalDiagnosisId = %i and Status = 'Active'" % (finalDiagnosisId)
    logSQL.trace(SQL)
    rows = system.db.runUpdateQuery(SQL, database)
    print "Cleared %i diagnosis entries" % (rows)
    
    # Set the state of the Final Diagnosis to InActive
    SQL = "update DtFinalDiagnosis set Active = 0 where FinalDiagnosisId = %i" % (finalDiagnosisId)
    logSQL.trace(SQL)
    rows = system.db.runUpdateQuery(SQL, database)
    print "Cleared %i final diagnosis" % (rows)
    
    print "Starting to manage as a result of a cleared Final Diagnosis..."
    notificationText=manage(application, recalcRequested=False, database=database, provider=provider)
    print "...back from manage!"
    
    # This runs in the gateway, but it should work 
    projectName = system.util.getProjectName()
    SQL = "select post "\
        "from TkPost P, TkUnit U, DtApplication A "\
        "where A.UnitId = U.UnitId "\
        "and U.PostId = P.postId "\
        "and A.ApplicationName = '%s'" % (application)
    console = system.db.runScalarQuery(SQL, database)
    print "The console is: ", console
    notifyClients(projectName, console, notificationText)

# Unpack the payload into arguments and call the method that posts a diagnosis entry.  
# This only runs in the gateway.  I'm not sure who calls this - this might be to facilitate testing, but I'm not sure
def recalcMessageHandler(payload):
    post=payload["post"]
    log.info("Handling message to manage an recommendations for post %s" % (post))
    database=payload["database"]
    provider=payload["provider"]

    from ils.diagToolkit.common import fetchApplicationsForPost
    pds=fetchApplicationsForPost(post, database)

    for record in pds:
        applicationName=record["ApplicationName"]
        manage(applicationName, recalcRequested=True, database=database, provider=provider)

# This is based on the original G2 procedure outout-msg-core()
# I think this updates the diagnosis entry with the results of the recommendation.
def updateOutputMessage(finalDiagnosisId, diagnosisEntryId, textRecommendation, recommendations, quantOutputs, database):

    if len(recommendations) == 0:
        textRecommendation = textRecommendation + "\nNo Outputs Calculated"
    else:
        textRecommendation = textRecommendation + "\nOutputs are:"
        
    for recommendation in recommendations:
        autoOrManual=recommendation.get('AutoOrManual', None)
        outputName = recommendation.get('QuantOutput','')
        if autoOrManual == 'Auto':
            val = recommendation.get('AutoRecommendation', None)
            textRecommendation = "%s\n%s = %s" % (textRecommendation, outputName, str(val))
            
        elif autoOrManual == 'Manual':
            textRecommendation = "%s\nManual move for %s = %s" % (textRecommendation, outputName, str(val))

    SQL = "update DtDiagnosisEntry set TextRecommendation = '%s' where DiagnosisEntryId = %i" % (textRecommendation, diagnosisEntryId)
    system.db.runUpdateQuery(SQL, database)
    return textRecommendation

# This replaces _em-manage-diagnosis().  Its job is to prioritize the active diagnosis for an application diagnosis queue.
def manage(application, recalcRequested=False, database="", provider=""):
    log.info("Managing diagnosis for application: %s using database %s and tag provider %s" % (application, database, provider))

    #---------------------------------------------------------------------
    # Merge the list of output dictionaries for a final diagnosis into the list of all outputs
    def mergeOutputs(quantOutputs, fdQuantOutputs):
 #       log.trace("Merging outputs %s into %s" % (str(fdQuantOutputs), str(quantOutputs)))
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
        log.trace("Merging Outputs: %s with %s " % (str(quantOutputs), str(recommendations)))
        for recommendation in recommendations:
            output1 = recommendation.get('QuantOutput', None)
#            print "Merge: ", output1
            if output1 != None:
                newQuantOutputs=[]
                for quantOutput in quantOutputs:
                    output2 = quantOutput.get('QuantOutput',None)
#                    print "  checking: ", output2
                    if output1 == output2:
                        currentRecommendations=quantOutput.get('Recommendations', [])
                        currentRecommendations.append(recommendation)
                        quantOutput['Recommendations'] = currentRecommendations
                    newQuantOutputs.append(quantOutput)
                quantOutputs=newQuantOutputs
        log.trace("The outputs merged with recommendations are: %s" % (str(quantOutputs)))
        return quantOutputs

    #---------------------------------------------------------------------
    # Sort out the families with the highest family priorities - this works because the records are fetched in 
    # descending order.  Remember that the highest priority is the lowest number (i.e. priority 1 is more important 
    # than priority 10.
    def selectHighestPriorityFamilies(pds):
        
        aList = []
        log.trace("The families with the highest priorities are: ")
        highestPriority = pds[0]['FamilyPriority']
        for record in pds:
            if record['FamilyPriority'] == highestPriority:
                log.trace("  Family: %s, Family Priority: %f, Final Diagnosis: %s, Final Diagnosis Priority: %f" % (record['FamilyName'], record['FamilyPriority'], record['FinalDiagnosisName'], record['FinalDiagnosisPriority']))
                aList.append(record)
        
        return aList
    
    #---------------------------------------------------------------------
    # Filter out low priority diagnosis where there are multiple active diagnosis within the same family
    def selectHighestPriorityDiagnosisForEachFamily(aList):
        log.trace("Filtering out low priority diagnosis for families with multiple active diagnosis...")
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
                log.trace("   ...removing %s because it's priority %f is greater than the most important priority %f" % (record["FinalDiagnosisName"], finalDiagnosisPriority, mostImportantPriority))
        return bList
    
    #---------------------------------------------------------------------
    # Whatever is Active must have been the highest priority
    def fetchPreviousHighestPriorityDiagnosis(applicationName, database):
        log.trace("Fetching the previous highest priority diagnosis...")
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
            log.trace("There were NO previous active priorities!")
        else:
            for record in pds:
                aList.append(record["FinalDiagnosisId"])
                log.trace("   %s - %i" % (record["FinalDiagnosisName"], record["FinalDiagnosisId"]))

        return aList

    #---------------------------------------------------------------------
    def setActiveDiagnosisFlag(alist, database):
        log.trace("Updating the 'active' flag for FinalDiagnosis...")
        # First clear all of the active flags in 
        families = []   # A list of quantOutput dictionaries
        for record in alist:
            familyId = record['FamilyId']
            if familyId not in families:
                log.trace("   ...clearing all FinalDiagnosis in family %s..." % str(familyId))
                families.append(familyId)
                SQL = "update dtFinalDiagnosis set Active = 0 where FamilyId = %i" % (familyId)
                logSQL.trace(SQL)
                rows=system.db.runUpdateQuery(SQL, database)
                log.trace("      updated %i rows!" % (rows))

        # Now set the ones that are active...
        for record in alist:
            finalDiagnosisId = record['FinalDiagnosisId']
            log.trace("   ...setting Final Diagnosis %i to active..." % (finalDiagnosisId))
            SQL = "update dtFinalDiagnosis set Active = 1, LastRecommendationTime = getdate() where FinalDiagnosisId = %i" % (finalDiagnosisId)
            logSQL.trace(SQL)
            rows = system.db.runUpdateQuery(SQL, database)
            log.trace("      updated %i rows!" % (rows))
    
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
        log.trace("...rescinding low priority diagnosis...")
        for fdId in lowPriorityList:
            log.trace("   ...rescinding recommendations for final diagnosis id: %i..." % (fdId))
            SQL = "delete from DtRecommendation where DiagnosisEntryId in "\
                " (select DiagnosisEntryId from DtDiagnosisEntry "\
                " where Status = 'Active' and RecommendationStatus = 'REC-Made' "\
                " and FinalDiagnosisId = %i)" % (fdId)
            logSQL.trace(SQL)
            rows=system.db.runUpdateQuery(SQL, database)
            log.trace("      deleted %i recommendations..." % (rows))

            SQL = "update DtDiagnosisEntry set RecommendationStatus = 'Rescinded'"\
                "where Status = 'Active' and RecommendationStatus = 'REC-Made' "\
                " and FinalDiagnosisId = %i" % (fdId)
            logSQL.trace(SQL)
            rows = system.db.runUpdateQuery(SQL, database)
            log.trace("      updated %i diagnosis entries..." % (rows))
    
    #----------------------------------------------------------------------
    def setDiagnosisEntryErrorStatus(alist, database):
        log.trace("Updating the diagnosis entries to indicate an error...")
        # First clear all of the active flags in 
        ids = []   # A list of quantOutput dictionaries
        for record in alist:
            finalDiagnosisId = record['FinalDiagnosisId']
            finalDiagnosis = record['FinalDiagnosisName']
            if finalDiagnosisId not in ids:
                log.trace("   ...setting error status for active diagnosis entries for final diagnosis: %s..." % (finalDiagnosis))
                ids.append(finalDiagnosisId)
                SQL = "update dtDiagnosisEntry set RecommendationStatus = 'ERROR' where FinalDiagnosisId = %i and status = 'Active'" % (finalDiagnosisId)
                logSQL.trace(SQL)
                rows=system.db.runUpdateQuery(SQL, database)
                log.trace("      updated %i rows!" % (rows))
    
          
    #--------------------------------------------------------------------
    # This is the start of manage()
    
    # Fetch the list of final diagnosis that were most important the last time we managed
    oldList=fetchPreviousHighestPriorityDiagnosis(application, database)
         
    from ils.diagToolkit.common import fetchActiveDiagnosis
    pds = fetchActiveDiagnosis(application, database)
    
    # If there are no active diagnosis then there is nothing to manage
    if len(pds) == 0:
        log.info("Exiting the diagnosis manager because there are no active diagnosis for %s!" % (application))
        # TODO we may need to clear something
        return ""

    log.trace("The active diagnosis are: ")
    for record in pds:
        log.trace("  Family: %s, Final Diagnosis: %s, Family Priority: %s, FD Priority: %s, Diagnosis Entry id: %s" % 
                  (record["FamilyName"], record["FinalDiagnosisName"], str(record["FamilyPriority"]), 
                   str(record["FinalDiagnosisPriority"]), str(record["DiagnosisEntryId"]) ))
    
    # Sort out the families with the highest family priorities - this works because the records are fetched in 
    # descending order.
    from ils.common.database import toDict
    list0 = toDict(pds)
    list1 = selectHighestPriorityFamilies(list0)

    # Sort out diagnosis where there are multiple diagnosis for the same family
    list2 = selectHighestPriorityDiagnosisForEachFamily(list1)
    
    # Calculate the recommendations for each final diagnosis
    log.trace("The families / final diagnosis with the highest priorities are: ")
    for record in list2:
        log.trace("  Family: %s, Final Diagnosis: %s (%i), Family Priority: %s, FD Priority: %s, Diagnosis Entry id: %s" % 
                  (record["FamilyName"], record["FinalDiagnosisName"],record["FinalDiagnosisId"], 
                   str(record["FamilyPriority"]), str(record["FinalDiagnosisPriority"]), str(record["DiagnosisEntryId"])))
    
    log.trace("Checking if there has been a change in the highest priority final diagnosis...")
    changed,lowPriorityList=compareFinalDiagnosisState(oldList, list2)
    
    if not(changed) and not(recalcRequested):
        log.trace("There has been no change in the most important diagnosis, nothing new to manage, so exiting!")
        return ""

    # There has been a change in what the most important diagnosis is so set the active flag
    if recalcRequested:
        log.trace("Continuing to make recommendations because a recalc was requested...")
    else:
        log.trace("Continuing to make recommendations because there was a change in the highest priority active final diagnosis...")

    from ils.diagToolkit.common import deleteRecommendations
    log.trace("...deleting existing recommendations for %s..." % (application))
    deleteRecommendations(application, log, database)
    
    from ils.diagToolkit.common import resetOutputs
    log.trace("...resetting the QuantOutput active flag for %s..." % (application))
    resetOutputs(application, log, database)
    
    rescindLowPriorityDiagnosis(lowPriorityList, database)
    setActiveDiagnosisFlag(list2, database)

    log.info("--- Calculating recommendations ---")
    quantOutputs = []   # A list of quantOutput dictionaries
    for record in list2:
        application = record['ApplicationName']
        family = record['FamilyName']
        finalDiagnosis = record['FinalDiagnosisName']
        finalDiagnosisId = record['FinalDiagnosisId']
        diagnosisEntryId = record["DiagnosisEntryId"]
        log.trace("Making a recommendation for application: %s, family: %s, final diagnosis:%s (%i)" % (application, family, finalDiagnosis, finalDiagnosisId))
        
        # Fetch all of the quant outputs for the final diagnosis
        from ils.diagToolkit.common import fetchOutputsForFinalDiagnosis
        pds, fdQuantOutputs = fetchOutputsForFinalDiagnosis(application, family, finalDiagnosis, database)
        quantOutputs = mergeOutputs(quantOutputs, fdQuantOutputs)
        
        from ils.diagToolkit.recommendation import makeRecommendation
        textRecommendation, recommendations, recommendationStatus = makeRecommendation(
                record['ApplicationName'], record['FamilyName'], record['FinalDiagnosisName'], 
                record['FinalDiagnosisId'], record['DiagnosisEntryId'], database, provider)
        
        textRecommendation = updateOutputMessage(finalDiagnosisId, diagnosisEntryId, textRecommendation, recommendations, quantOutputs, database)
        print "-----------------"
        print "Text Recommendation: ", textRecommendation
        print "Recommendations: ", recommendations
        print "Status: ", recommendationStatus
        print "-----------------"
        
        if recommendationStatus == "ERROR":
            log.error("The calculation method had an error")
            diagnosisEntryId=record['DiagnosisEntryId']
            SQL = "Update DtDiagnosisEntry set RecommendationStatus = 'ERROR' where DiagnosisEntryId = %i " % (diagnosisEntryId)
            logSQL.trace(SQL)
            system.db.runUpdateQuery(SQL, database)
            return "Error"
        elif recommendationStatus == "NO-RECOMMENDATIONS":
            log.warn("No recommendations were made")
            diagnosisEntryId=record['DiagnosisEntryId']
            SQL = "Update DtDiagnosisEntry set RecommendationStatus = 'No-Recs' where DiagnosisEntryId = %i " % (diagnosisEntryId)
            logSQL.trace(SQL)
            system.db.runUpdateQuery(SQL, database)
            return "None Made"
        
        quantOutputs = mergeRecommendations(quantOutputs, recommendations)
        print "-----------------"
        print "Quant Outputs: ", quantOutputs
        print "-----------------"

    log.info("--- Recommendations have been made, now calculating the final recommendations ---")
    finalQuantOutputs = []
    for quantOutput in quantOutputs:
        from ils.diagToolkit.recommendation import calculateFinalRecommendation
        quantOutput = calculateFinalRecommendation(quantOutput)
        if quantOutput == None:
            # The case where a FD has 5 quant outputs defined but there are only recommendations to change 3 of them is not an error
            pass
        else:
            quantOutput = checkBounds(quantOutput, database, provider)
            if quantOutput == None:
                # If there was an error checking bounds, specifically if the current value could not be read, the we can't make any valid recommendations
                # Remember that the change is really a vector, and if we lose one dimension then we will twist the plant.
                finalQuantOutputs = []
                setDiagnosisEntryErrorStatus(list2, database)
                break
         
            finalQuantOutputs.append(quantOutput)

    finalQuantOutputs, notificationText = calculateVectorClamps(finalQuantOutputs, provider)
    
    # Store the results in the database
    log.trace("Done managing, the final outputs are: %s" % (str(finalQuantOutputs)))
    for quantOutput in finalQuantOutputs:
        updateQuantOutput(quantOutput, database, provider)
        
    log.info("Finished managing recommendations")
    return notificationText

# Check that recommendation against the bounds configured for the output
def checkBounds(quantOutput, database, provider):

    log.trace("   ...checking Bounds...")
    
    # The feedbackOutput can be incremental or absolute
    feedbackOutput = quantOutput.get('FeedbackOutput', 0.0)
    incrementalOutput=quantOutput.get('IncrementalOutput')
    mostNegativeIncrement = quantOutput.get('MostNegativeIncrement', -1000.0)
    mostPositiveIncrement = quantOutput.get('MostPositiveIncrement', 1000.0)
    
    # Read the current setpoint - the tagpath in the QuantOutput does not have the provider
    tagpath = '[' + provider + ']' + quantOutput.get('TagPath','unknown')
    log.trace("   ...reading the current value of tag: %s" % (tagpath))
    qv=system.tag.read(tagpath)
    if not(qv.quality.isGood()):
        log.error("Error reading the current setpoint from (%s), tag quality is: (%s)" % (tagpath, str(qv.quality)))
 
        # Make this quant-output inactive since we can't make an intelligent recommendation without the current setpoint;
        # moreover, we don't want t to make any recommendations related to this problem / FD
        # Note: I'm not sure how to sort out this output from a situation where multiple FDs may be active - but I think that is rare
#        quantOutput['CurrentValue'] = None
#        quantOutput['CurrentValueIsGood'] = False
#        quantOutput['OutputLimited'] = False
#        quantOutput['OutputLimitedStatus'] = 'Not Bound'
        return None

    quantOutput['CurrentValue'] = qv.value
    quantOutput['CurrentValueIsGood'] = True

    # If the recommendation was absolute, then convert it to incremental for the may be absolute or incremental, but we always display incremental    
    if not(incrementalOutput):
        log.trace("      ...calculating an incremental change for an absolute recommendation...")
        feedbackOutput = feedbackOutput - qv.value

    # Compare the recommendation to the **incremental** limits
    log.trace("      ...comparing the feedback output (%f) to most positive increment (%f) and most negative increment (%f)..." % (feedbackOutput, mostPositiveIncrement, mostNegativeIncrement))
    if feedbackOutput >= mostNegativeIncrement and feedbackOutput <= mostPositiveIncrement:
        log.trace("      ...the output is not incremental bound...")
        quantOutput['OutputLimited'] = False
        quantOutput['OutputLimitedStatus'] = 'Not Bound'
        feedbackOutputConditioned=feedbackOutput
    elif feedbackOutput > mostPositiveIncrement:
        log.trace("      ...the output IS positive incremental bound...")
        quantOutput['OutputLimited'] = True
        quantOutput['OutputLimitedStatus'] = 'Positive Incremental Bound'
        feedbackOutputConditioned=mostPositiveIncrement
    else:
        log.trace("      ...the output IS negative incremental bound...")
        quantOutput['OutputLimited'] = True
        quantOutput['OutputLimitedStatus'] = 'Negative Incremental Bound'
        feedbackOutputConditioned=mostNegativeIncrement
        
    # Compare the final setpoint to the **absolute** limits
    setpointHighLimit = quantOutput.get('SetpointHighLimit', -1000.0)
    setpointLowLimit = quantOutput.get('SetpointLowLimit', 1000.0)
    log.trace("      ...comparing the proposed setpoint (%f) to high limit (%f) and low limit (%f)..." % ((qv.value + feedbackOutputConditioned), setpointHighLimit, setpointLowLimit))

    # For the absolute limits we need to add the current value to the incremental change before comparing to the absolute limits
    if qv.value + feedbackOutputConditioned > setpointHighLimit:
        log.trace("      ...the output IS Positive Absolute Bound...")
        quantOutput['OutputLimited'] = True
        quantOutput['OutputLimitedStatus'] = 'Positive Absolute Bound'
        feedbackOutputConditioned=setpointHighLimit - qv.value
    elif qv.value + feedbackOutputConditioned < setpointLowLimit:
        log.trace("      ...the output IS Negative Absolute Bound...")
        quantOutput['OutputLimited'] = True
        quantOutput['OutputLimitedStatus'] = 'Negative Absolute Bound'
        feedbackOutputConditioned=setpointLowLimit - qv.value

    # Now check the minimum increment requirement
    minimumIncrement = quantOutput.get('MinimumIncrement', 1000.0)
    if abs(feedbackOutputConditioned) < minimumIncrement:
        log.trace("      ...the output IS Minimum change bound because the change (%f) is less then the minimum change amount (%f)..." % (feedbackOutputConditioned, minimumIncrement))
        quantOutput['OutputLimited'] = True
        quantOutput['OutputLimitedStatus'] = 'Minimum Change Bound'
        feedbackOutputConditioned=0.0
        quantOutput['FeedbackOutputConditioned']=feedbackOutputConditioned

    finalIncrementalValue = feedbackOutputConditioned
    
    # If the recommendation was absolute, then convert it back to absolute
    if not(incrementalOutput):
        log.trace("      ...converting an incremental change (%s) back to an absolute recommendation (%s)..." % (str(feedbackOutputConditioned), str(qv.value + feedbackOutputConditioned)))
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
        
        log.trace("   ...the output is bound - taking %f percent of the recommended change..." % (outputPercent))
        quantOutput['OutputPercent'] = outputPercent
        from ils.diagToolkit.common import updateBoundRecommendationPercent
        updateBoundRecommendationPercent(quantOutput['QuantOutputId'], outputPercent, database)
    
    log.trace("   The recommendation after bounds checking is:")
    log.trace("          Feedback Output Conditioned: %f" % (feedbackOutputConditioned))
    log.trace("                       Output limited: %s" % (str(quantOutput['OutputLimited'])))
    log.trace("                Output limited status: %s" % (quantOutput['OutputLimitedStatus']))
    log.trace("                       Output percent: %f" % (quantOutput['OutputPercent']))
    return quantOutput

def calculateVectorClamps(quantOutputs, provider):
    log.trace("Checking vector clamping with tag provider: %s..." % (provider))
    tagName="[%s]Configuration/DiagnosticToolkit/vectorClampMode" % (provider)
    qv=system.tag.read(tagName)
    vectorClampMode = string.upper(qv.value)
    
    if vectorClampMode == "DISABLED":
        log.trace("...Vector Clamps are NOT enabled")
        return quantOutputs, ""
    
    log.trace("...Vector clamping is enabled")

    # There needs to be at least two outputs that are not minimum change bound for vector clamps to be appropriate
    i = 0
    for quantOutput in quantOutputs:
        if quantOutput['OutputLimitedStatus'] != 'Minimum Change Bound':
            i = i + 1

    if i < 2:
        log.trace("Vector clamps do not apply when there is only one output")
        return quantOutputs, ""

    # The first step is to find the most restrictive clamp
    minOutputRatio=100.0
    for quantOutput in quantOutputs:
        if quantOutput['OutputLimitedStatus'] != 'Minimum Change Bound':
            if quantOutput['OutputPercent'] < minOutputRatio:
                boundOutput=quantOutput
                minOutputRatio = quantOutput['OutputPercent']
        else:
            log.trace("...not considering %s which is minimum change bound..." % (quantOutput['QuantOutput']))
            
    if minOutputRatio == 100.0:
        log.trace("No outputs are clamped, therefore there is not a vector clamp")
        return quantOutputs, ""

    log.trace("All outputs will be clamped at %f" % (minOutputRatio))

    finalQuantOutputs = []
    txt = "The most bound output is %s, %.0f%% of the total recommendation of %.4f, which equals %.4f, will be implemented." % \
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
            if abs(feedbackOutputConditioned) < minimumIncrement:
                feedbackOutputConditioned = 0.0
                outputPercent = 0.0
                txt = "%s which is an insignificant value value and should be set to 0.0." % (txt)
                    
            if vectorClampMode == 'IMPLEMENT':
                log.trace('Implementing a vector clamp on %s' % (quantOutput['QuantOutput']))
                quantOutput['OutputPercent'] = outputPercent
                quantOutput['FeedbackOutputConditioned'] = feedbackOutputConditioned
                quantOutput['OutputLimitedStatus'] = 'Vector'
                quantOutput['OutputLimited']=True

        finalQuantOutputs.append(quantOutput)
            
    log.trace(txt)
    
    if vectorClampMode == 'ADVISE':
        notificationText=txt
    else:
        notificationText=""
        
    return finalQuantOutputs, notificationText

# Store the updated quantOutput in the database so that it will show up in the setpoint spreadsheet
def updateQuantOutput(quantOutput, database='', provider=''):
    from ils.common.cast import toBool
    
    log.trace("Updating the database with the recommendations made to QuantOutput: %s" % (str(quantOutput)))
    feedbackOutput = quantOutput.get('FeedbackOutput', 0.0)
    feedbackOutputConditioned = quantOutput.get('FeedbackOutputConditioned', 0.0)
    quantOutputId = quantOutput.get('QuantOutputId', 0)
    outputLimitedStatus = quantOutput.get('OutputLimitedStatus', '')
    outputLimited = quantOutput.get('OutputLimited', False)
    outputLimited = toBool(outputLimited)
    outputPercent = quantOutput.get('OutputPercent', 0.0)
    
    # The current setpoint was read when we checked the bounds.
    isGood = quantOutput.get('CurrentValueIsGood',False)
    if not(isGood):
        # Make this quant-output inactive since we can't make an intelligent recommendation without the current setpoint
        SQL = "update DtQuantOutput set Active = 0 where QuantOutputId = %i " % (quantOutputId)
        logSQL.trace(SQL)
        system.db.runUpdateQuery(SQL, database)
        return

    currentSetpoint=quantOutput.get('CurrentValue',None)
    log.trace("     ...using current setpoint value: %s" % (str(currentSetpoint)))
    

    # The recommendation may be absolute or incremental, but we always display incremental    
    incrementalOutput=quantOutput.get('IncrementalOutput')
    if incrementalOutput:
        finalSetpoint=currentSetpoint+feedbackOutputConditioned
        displayedRecommendation=feedbackOutputConditioned
    else:
        finalSetpoint=feedbackOutputConditioned
        displayedRecommendation=finalSetpoint-currentSetpoint

    log.trace("   ...the final setpoint is %f, the displayed recommendation is %f" % (finalSetpoint, displayedRecommendation))

    # Active is hard-coded to True here because these are the final active quantOutputs
    SQL = "update DtQuantOutput set FeedbackOutput = %s, OutputLimitedStatus = '%s', OutputLimited = %i, "\
        " OutputPercent = %s, FeedbackOutputManual = 0.0, FeedbackOutputConditioned = %s, "\
        " ManualOverride = 0, Active = 1, CurrentSetpoint = %s, FinalSetpoint = %s, DisplayedRecommendation = %s "\
        " where QuantOutputId = %i "\
        % (str(feedbackOutput), outputLimitedStatus, outputLimited, str(outputPercent), str(feedbackOutputConditioned), \
           str(currentSetpoint), str(finalSetpoint), str(displayedRecommendation), quantOutputId)
    logSQL.trace(SQL)
    system.db.runUpdateQuery(SQL, database)
    