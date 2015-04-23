'''
Created on Sep 12, 2014

@author: Pete
'''

import system, string
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.diagToolkit.recommendation")
logSQL = LogUtil.getLogger("com.ils.diagToolkit.SQL")

def notifyClients(project, console, notificationText):
    print "Notifying %s clients" % (console)
    print "Notification Text: <%s>" % (notificationText)
    system.util.sendMessage(project=project, messageHandler="consoleManager", 
                            payload={'type':'setpointSpreadsheet', 'console':console, 'notificationText':notificationText}, scope="C")

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

# Insert a record into the diagnosis queue
def postDiagnosisEntry(application, family, finalDiagnosis, UUID, diagramUUID, database=""):
    log.trace("Post a diagnosis entry for application: %s, family: %s, final diagnosis: %s" % (application, family, finalDiagnosis))

    # TODO - need to look this up somehow
    grade = 28
    
    # Lookup the application Id
    from ils.diagToolkit.common import fetchFinalDiagnosis
    record = fetchFinalDiagnosis(application, family, finalDiagnosis, database)
    finalDiagnosisId=record.get('FinalDiagnosisId', None)
    if finalDiagnosisId == None:
        log.error("ERROR posting a diagnosis entry for %s - %s - %s because the final diagnosis was not found!" % (application, family, finalDiagnosis))
        return
       
    textRecommendation = record.get('TextRecommendation', 'Unknown Text')
    
    # Insert an entry into the diagnosis queue
    SQL = "insert into DtDiagnosisEntry (FinalDiagnosisId, Status, Timestamp, Grade, TextRecommendation, "\
        "RecommendationStatus, UUID, DiagramUUID, ManualMove, ManualMoveValue, RecommendationMultiplier) "\
        "values (%i, 'Active', getdate(), '%s', '%s', 'NONE-MADE', '%s', '%s', 0, 0.0, 1.0)" \
        % (finalDiagnosisId, grade, textRecommendation, UUID, diagramUUID)
    logSQL.trace(SQL)
    
    system.db.runUpdateQuery(SQL, database)

    log.info("Starting to manage diagnosis...")
    notificationText=manage(application, database)
    log.info("...back from manage!")
    
    #TODO Need to look these up somehow
    project="XOM"
    console="VFU"
    notifyClients(project, console, notificationText)
    
# Clear the final diagnosis (make the status = 'InActive') 
def clearDiagnosisEntry(application, family, finalDiagnosis, database=""):
    print "Clearing..."

    from ils.diagToolkit.common import fetchFinalDiagnosis
    record = fetchFinalDiagnosis(application, family, finalDiagnosis, database)
    finalDiagnosisId=record.get('FinalDiagnosisId', None)
    if finalDiagnosisId == None:
        log.error("ERROR clearing a diagnosis entry for %s - %s - %s because the final diagnosis was not found!" % (application, family, finalDiagnosis))
        return    

    # Insert an entry into the diagnosis queue
    SQL = "update DtDiagnosisEntry set Status = 'InActive' where FinalDiagnosisId = %i and Status = 'Active'" % (finalDiagnosisId)
    logSQL.trace(SQL)
    system.db.runUpdateQuery(SQL, database)
    
    print "Starting to manage as a result of a cleared Final Diagnosis..."
    notificationText=manage(application, database)
    print "...back from manage!"
    
    #TODO Need to look these up somehow
    project="XOM"
    console="VFU"
    notifyClients(project, console, notificationText)

# This replaces _em-manage-diagnosis().  Its job is to prioritize the active diagnosis for an application diagnosis queue.
def manage(application, database=""):
    log.trace("Managing diagnosis for application: %s" % (application))

    #---------------------------------------------------------------------
    # Merge the list of output dictionaries for a final diagnosis into the list of all outputs
    def mergeOutputs(quantOutputs, fdQuantOutputs):
        log.trace("Merging outputs %s into %s" % (str(fdQuantOutputs), str(quantOutputs)))
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
    # descending order.
    def selectHighestPriorityFamilies(pds):
        
        aList = []
        highestPriority = pds[0]['FamilyPriority']
        for record in records:
            if record['FamilyPriority'] == highestPriority:
                print record['FamilyName'], record['FamilyPriority'], record['FinalDiagnosisName'], record['FinalDiagnosisPriority']
                aList.append(record)
        print "The families with the highest priorities are: ", aList
        return aList
    
    #---------------------------------------------------------------------
    # Filter out low priority diagnosis where there are multiple active diagnosis within the same family
    def selectHighestPriorityDiagnosisForEachFamily(aList):
        print "\nFiltering out low priority diagnosis for families with multiple active diagnosis..."
        lastFamily = ''
        highestPriority = -1
        bList = []
        for record in aList:
            print record
            family = record['FamilyName']
            finalDiagnosisPriority = record['FinalDiagnosisPriority']
            if family != lastFamily:
                lastFamily = family
                highestPriority = finalDiagnosisPriority
                bList.append(record)
            elif finalDiagnosisPriority >= highestPriority:
                bList.append(record)
            else:
                print "Filtering out: ", record
        return bList
    
    #---------------------------------------------------------------------
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
            log.trace("The *PREVIOUS* Highest priority diagnosis are: %s" % (str(aList)))
        
        return aList

    #---------------------------------------------------------------------
    def setActiveDiagnosisFlag(alist):
        log.trace("Setting the active diagnosis flag...")
        # First clear all of the active flags in 
        families = []   # A list of quantOutput dictionaries
        for record in alist:
            familyId = record['FamilyId']
            if familyId not in families:
                log.trace("   .. clearing diagnosis in family %s " % str(familyId))
                families.append(familyId)
                SQL = "update dtFinalDiagnosis set Active = 0 where FamilyId = %i" % (familyId)
                logSQL.trace(SQL)
                system.db.runUpdateQuery(SQL)

        for record in alist:
            finalDiagnosisId = record['FinalDiagnosisId']
            log.trace("  ...setting %i to active..." % (finalDiagnosisId))
            SQL = "update dtFinalDiagnosis set Active = 1 where FinalDiagnosisId = %i" % (finalDiagnosisId)
            logSQL.trace(SQL)
            system.db.runUpdateQuery(SQL)
    
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
        
        # If the lengths of the lists are different then they must be different!
        if len(oldList) != len(newList):
            changed=True
        
        lowPriorityList=[]
        for fdId in oldList:
            if fdId not in newList:
                changed=True
                lowPriorityList.append(fdId)

        return changed, lowPriorityList

    #-------------------------------------------------------------------
    def rescindLowPriorityDiagnosis(lowPriorityList):
        for fdId in lowPriorityList:
            print ">>>>>>>>>>>>>>>>>>>Need to rescind: ", fdId
#            SQL = "delete from DtRecommendation where DiagnosisEntryId in "\
#                " (select DiagnosisEntryId from DtDiagnosisEntry "\
#                " where Status = 'Active' and RecommendationStatus = 'REC-Made' "\
#                " and FinalDiagnosisId = %i)" % (fdId)
#            logSQL.trace(SQL)
#            system.db.runUpdateQuery(SQL)
            
            SQL = "update DtDiagnosisEntry set RecommendationStatus = 'Rescinded'"\
                "where Status = 'Active' and RecommendationStatus = 'REC-Made' "\
                " and FinalDiagnosisId = %i" % (fdId)
            logSQL.trace(SQL)
            system.db.runUpdateQuery(SQL)
             
    #--------------------------------------------------------------------
    # This is the start of manage()
    
    # Fetch the list of final diagnosis that were most important the last time we managed
    oldList=fetchPreviousHighestPriorityDiagnosis(application, database)
         
    from ils.diagToolkit.common import fetchActiveDiagnosis
    pds = fetchActiveDiagnosis(application, database)
    from ils.common.database import toDict
    records=toDict(pds)
    
    # If there are no active diagnosis then there is nothing to manage
    if len(records) == 0:
        log.info("Exiting the diagnosis manager because there are no active diagnosis!")
        # TODO we may need to clear something!
        return ""
    
    # Sort out the families with the highest family priorities - this works because the records are fetched in 
    # descending order.
    list1 = selectHighestPriorityFamilies(pds)

    # Sort out diagnosis where there are multiple diagnosis for the same family
    list2 = selectHighestPriorityDiagnosisForEachFamily(list1)
    
    # Calculate the recommendations for each final diagnosis
    print "The families / final diagnosis with the highest priorities are: ", list2
    
    log.trace("Checking if there has been a change in the highest priority final diagnosis...")
    changed,lowPriorityList=compareFinalDiagnosisState(oldList, list2)
    
    if not(changed):
        log.trace("There has been no change in the most important diagnosis, leaving!")
        return ""

    # There has been a change in what the most important diagnosis is so set the active flag
    log.info("There was a change in the highest priority active final diagnosis, updating the database...")
    from ils.diagToolkit.common import deleteRecommendations      
    deleteRecommendations(application, database)
    
    rescindLowPriorityDiagnosis(lowPriorityList)
    setActiveDiagnosisFlag(list2)

    log.info("Making recommendations...")
    quantOutputs = []   # A list of quantOutput dictionaries
    for record in list2:
        application = record['ApplicationName']
        family = record['FamilyName']
        finalDiagnosis = record['FinalDiagnosisName']
        log.trace("Making a recommendation for: %s - %s - %s" % (application, family, finalDiagnosis))
        
        # Fetch all of the quant outputs for the final diagnosis
        from ils.diagToolkit.common import fetchOutputsForFinalDiagnosis
        pds, fdQuantOutputs = fetchOutputsForFinalDiagnosis(application, family, finalDiagnosis, database)
        quantOutputs = mergeOutputs(quantOutputs, fdQuantOutputs)
        
        from ils.diagToolkit.recommendation import makeRecommendation
        textRecommendation, recommendations = makeRecommendation(
                record['ApplicationName'], record['FamilyName'], record['FinalDiagnosisName'], 
                record['FinalDiagnosisId'], record['DiagnosisEntryId'], database)
        quantOutputs = mergeRecommendations(quantOutputs, recommendations)

    log.info("Recommendations have been made, now calculating the final recommendations")
    finalQuantOutputs = []
    for quantOutput in quantOutputs:
        from ils.diagToolkit.recommendation import calculateFinalRecommendation
        quantOutput = calculateFinalRecommendation(quantOutput)
        quantOutput = checkBounds(quantOutput, database)
        finalQuantOutputs.append(quantOutput)

    finalQuantOutputs, notificationText = calculateVectorClamps(finalQuantOutputs)
    
    # Store the results in the database
    log.trace("Done managing, the final outputs are: %s" % (str(finalQuantOutputs)))
    for quantOutput in finalQuantOutputs:
        updateQuantOutput(quantOutput, database)
        
    log.info("Finished managing recommendations")
    return notificationText

# Check that recommendation against the bounds configured for the output
def checkBounds(quantOutput, database):
    
    log.trace("Checking Bounds for %s" % (str(quantOutput)))
    feedbackOutput = quantOutput.get('FeedbackOutput', 0.0)
    mostNegativeIncrement = quantOutput.get('MostNegativeIncrement', -1000.0)
    mostPositiveIncrement = quantOutput.get('MostPositiveIncrement', 1000.0)

    # Compare the incremental recommendation to the **incremental** limits
    if feedbackOutput >= mostNegativeIncrement and feedbackOutput <= mostPositiveIncrement:
        quantOutput['OutputLimited'] = False
        quantOutput['OutputLimitedStatus'] = 'Not Bound'
        feedbackOutputConditioned=feedbackOutput
    elif feedbackOutput > mostPositiveIncrement:
        quantOutput['OutputLimited'] = True
        quantOutput['OutputLimitedStatus'] = 'Positive Incremental Bound'
        feedbackOutputConditioned=mostPositiveIncrement
    else:
        quantOutput['OutputLimited'] = True
        quantOutput['OutputLimitedStatus'] = 'Negative Incremental Bound'
        feedbackOutputConditioned=mostNegativeIncrement

    # Compare the final setpoint to the **absolute** limits
    setpointHighLimit = quantOutput.get('SetpointHighLimit', -1000.0)
    setpointLowLimit = quantOutput.get('SetpointLowLimit', 1000.0)
    
    if feedbackOutputConditioned > setpointHighLimit:
        quantOutput['OutputLimited'] = True
        quantOutput['OutputLimitedStatus'] = 'Positive Absolute Bound'
        feedbackOutputConditioned=setpointHighLimit
    elif feedbackOutputConditioned < setpointLowLimit:
        quantOutput['OutputLimited'] = True
        quantOutput['OutputLimitedStatus'] = 'Negative Absolute Bound'
        feedbackOutputConditioned=setpointLowLimit    

    quantOutput['FeedbackOutputConditioned'] = feedbackOutputConditioned
    
    minimumIncrement = quantOutput.get('MinimumIncrement', 1000.0)
    if abs(feedbackOutputConditioned) < minimumIncrement:
        quantOutput['OutputLimited'] = True
        quantOutput['OutputLimitedStatus'] = 'Minimum Change Bound'
        feedbackOutputConditioned=0.0
    
    # Calculate the percent of the original recommendation that we are using if the output is limited 
    if quantOutput['OutputLimited'] == True:
        outputPercent = feedbackOutputConditioned / feedbackOutput * 100.0
        quantOutput['OutputPercent'] = outputPercent
        from ils.diagToolkit.common import updateBoundRecommendationPercent
        updateBoundRecommendationPercent(quantOutput['QuantOutputId'], outputPercent, database)
    
    return quantOutput


def calculateVectorClamps(quantOutputs):
    #TODO XOM is hard coded
    qv=system.tag.read("[XOM]Configuration/DiagnosticToolkit/vectorClampMode")
    vectorClampMode = string.upper(qv.value)
    
    if vectorClampMode == "DISABLED":
        log.trace("Vector Clamps are NOT enabled")
        return quantOutputs, ""
    
    log.trace("Vector clamping is enabled")
    
    if len(quantOutputs) < 2:
        log.trace("Vector clamps do not apply when there is only one output")
        return quantOutputs, ""

    # The first step is to find the most restrictive clamp
    minOutputRatio=100.0
    for quantOutput in quantOutputs:
        if quantOutput['OutputPercent'] < minOutputRatio:
            boundOutput=quantOutput
            minOutputRatio = quantOutput['OutputPercent']
    
    if minOutputRatio == 100.0:
        log.trace("No outputs are clamped, therefore there is not a vector clamp")
        return quantOutputs, ""

    log.trace("All outputs will be clamped at %f" % (minOutputRatio))

    finalQuantOutputs = []
    txt = "The most bound output is %s, %.0f%% of the total recommendation of %.4f, which equals %.4f, will be implemented." % \
        (boundOutput['QuantOutput'], minOutputRatio, boundOutput['FeedbackOutput'], boundOutput['FeedbackOutputConditioned'])
        
    for quantOutput in quantOutputs:
        
        # Look for an output that isn't bound but needs to be Vector clamped
        if quantOutput['OutputPercent'] > minOutputRatio:
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
            
    print txt
    
    if vectorClampMode == 'ADVISE':
        notificationText=txt
    else:
        notificationText=""
        
    return finalQuantOutputs, notificationText

# Store the updated quantOutput in the database so that it will show up in the setpoint spreadsheet
def updateQuantOutput(quantOutput, database=''):
    from ils.common.cast import toBool
    
    log.trace("Updating the database with the recommondations made to QuantOutput: %s" % (str(quantOutput)))
    feedbackOutput = quantOutput.get('FeedbackOutput', 0.0)
    feedbackOutputConditioned = quantOutput.get('FeedbackOutputConditioned', 0.0)
    quantOutputId = quantOutput.get('QuantOutputId', 0)
    outputLimitedStatus = quantOutput.get('OutputLimitedStatus', '')
    outputLimited = quantOutput.get('OutputLimited', False)
    outputLimited = toBool(outputLimited)
    outputPercent = quantOutput.get('OutputPercent', 0.0)
    
    # Read the current setpoint
    tagpath = quantOutput.get('TagPath','unknown')
    log.trace("Reading Tag: %s" % (tagpath))
    qv=system.tag.read(tagpath)
    log.trace("  read tag values: %s - %s" % (str(qv.value), str(qv.quality)))
    currentSetpoint=qv.value

    # The recommendation may be absolute or incremental, but we always display incremental    
    incrementalOutput=quantOutput.get('IncrementalOutput')
    if incrementalOutput:
        finalSetpoint=currentSetpoint+feedbackOutputConditioned
        displayedRecommendation=feedbackOutputConditioned
    else:
        finalSetpoint=feedbackOutputConditioned
        displayedRecommendation=finalSetpoint-currentSetpoint

    # Active is hard-coded to True here because these are the final active quantOutputs
    SQL = "update DtQuantOutput set FeedbackOutput = %s, OutputLimitedStatus = '%s', OutputLimited = %i, "\
        " OutputPercent = %s, FeedbackOutputManual = 0.0, FeedbackOutputConditioned = %s, "\
        " ManualOverride = 0, Active = 1, CurrentSetpoint = %s, FinalSetpoint = %s, DisplayedRecommendation = %s "\
        " where QuantOutputId = %i "\
        % (str(feedbackOutput), outputLimitedStatus, outputLimited, str(outputPercent), str(feedbackOutputConditioned), \
           str(currentSetpoint), str(finalSetpoint), str(displayedRecommendation), quantOutputId)
    logSQL.trace(SQL)
    system.db.runUpdateQuery(SQL, database)
    

# Initialize the diagnosis 
def initializeView(rootContainer):
    console = rootContainer.getPropertyValue("console")
    title = console + ' Console Diagnosis Message Queue'
    rootContainer.setPropertyValue('title', title) 
    print "Done initializing!    Yookoo"

