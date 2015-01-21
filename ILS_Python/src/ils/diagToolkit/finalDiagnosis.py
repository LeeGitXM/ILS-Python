'''
Created on Sep 12, 2014

@author: Pete
'''

import system, string
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.diagToolkit.finalDiagnosis")


def notifyClients(project, console):
    print "Notifying %s clients" % (console)
    system.util.sendMessage(project=project, messageHandler="consoleManager", payload={'type':'setpointSpreadsheet', 'console':console}, scope="C")

# The purpose of this notification handler is to open the setpoint spreadsheet on the appropriate client when there is a 
# change in a FD / Recommendation.  The idea is that the gateway will send a message to all clients.  The payload of the 
# message includes the console name.  If the client is responsible for the console and the setpoint spreadsheet is not 
# already displayed, then display it.  There are a number of stratagies that could be used to determine if a client is 
# responsible for / interested in a certain console.  The first one I will try is to check to see if the console window
# is open.  (This depends on a reliable policy for keeping the console displayed)
def handleNotification(payload):
    print "Handling a notification", payload
    
    console=payload.get('console', '')
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
            return
    
    # Now check if this client is interested in the console     
    for window in windows:
        windowPath=window.getPath()
        pos = windowPath.find(console)
        if pos >= 0:
            print "Found an interested window - post the setpoint spreadsheet"
            system.nav.openWindow('DiagToolkit/Setpoint Spreadsheet', {'console': console})
            system.nav.centerWindow('DiagToolkit/Setpoint Spreadsheet')
            return

# Insert a record into the diagnosis queue
def postDiagnosisEntry(application, family, finalDiagnosis, UUID, diagramUUID, database=""):
    print "Post a diagnosis entry, using database: ", database

    # TODO - need to look this up somehow
    grade = 28
    
    # Lookup the application Id
    from ils.diagToolkit.common import fetchFinalDiagnosis
    record = fetchFinalDiagnosis(application, family, finalDiagnosis, database)
    finalDiagnosisId=record.get('FinalDiagnosisId', None)
    if finalDiagnosisId == None:
        log.error("ERROR posting a diagnosis entry for %s - %s - %s because the final diagnosis was not found!" % (application, family, finalDiagnosis))
        return
    
    print "Fetched Final Diagnosis ID: ", finalDiagnosisId
    
    textRecommendation = record.get('TextRecommendation', 'Unknown Text')
    
    # Insert an entry into the diagnosis queue
    SQL = "insert into DtDiagnosisEntry (FinalDiagnosisId, Status, Timestamp, Grade, TextRecommendation, "\
        "RecommendationStatus, UUID, DiagramUUID, ManualMove, ManualMoveValue, RecommendationMultiplier) "\
        "values (%i, 'Active', getdate(), '%s', '%s', 'NONE-MADE', '%s', '%s', 0, 0.0, 1.0)" \
        % (finalDiagnosisId, grade, textRecommendation, UUID, diagramUUID)

    print SQL
    system.db.runUpdateQuery(SQL, database)
    print "Inserted the diagnosis entry..."

    print "Starting to manage..."
    manage(application, database)
    print "...back from manage!"
    
    #TODO Need to look these up somehow
    project="XOM"
    console="VFU"
    print "Starting to notify..."
    notifyClients(project, console)
    print "...back from Notify!"
    
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
    print SQL

    system.db.runUpdateQuery(SQL, database)
    
    print "Starting to manage as a result of a cleared Final Diagnosis..."
    manage(application, database)
    print "...back from manage!"
    
    #TODO Need to look these up somehow
    project="XOM"
    console="VFU"
    print "Starting to notify..."
    notifyClients(project, console)
    print "...back from Notify!"

# This replaces _em-manage-diagnosis().  Its job is to prioritize the active diagnosis for an application diagnosis queue.
def manage(application, database=""):
    log.trace("Managing diagnosis for application: %s" % (application))

    # -------------------------------------------------------
    # Merge the list of output dictionaries for a final diagnosis into the list of all outputs
    def mergeOutputs(quantOutputs, fdQuantOutputs):
        print "Merging ", fdQuantOutputs, "\n\ninto\n\n", quantOutputs
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
    # -------------------------------------------------------
    # There are two lists.  The first is a list of all quant outputs and the second is the list of all recommendations.
    # Merge the lists into one so the recommendations are with the appropriate output
    def mergeRecommendations(quantOutputs, recommendations):
#        print "Merging Outputs: ", quantOutputs
#        print "With recommendations: ", recommendations
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
 #       print "The outputs merged with recommendations are: ", quantOutputs
        return quantOutputs
    # -------------------------------------------------------  
    
    from ils.diagToolkit.common import clearQuantOutputRecommendations
    clearQuantOutputRecommendations(application, database)
    
    from ils.diagToolkit.common import deleteRecommendations      
    deleteRecommendations(application, database)
          
    from ils.diagToolkit.common import fetchActiveDiagnosis
    pds = fetchActiveDiagnosis(application, database)
    from ils.common.database import toDict
    records=toDict(pds)
    
    # If there are no active diagnosis then there is nothing to manage
    if len(records) == 0:
        print "Exiting the diagnosis manager because there are no active diagnosis!"
        # TODO we may need to clear something!
        return
    
    print "In manage(), using database:  ", database
    
    # Sort out the families with the highest family priorities - this works because the records are fetched in 
    # descending order.
    list1 = []
    highestPriority = pds[0]['FamilyPriority']
    for record in records:
        if record['FamilyPriority'] == highestPriority:
            print record['Family'], record['FamilyPriority'], record['FinalDiagnosis'], record['FinalDiagnosisPriority']
            list1.append(record)
    print "The families with the highest priorities are: ", list1

    # Sort out diagnosis where there are multiple diagnosis for the same family
    print "\nSorting diagnosis with highest diagnosis priorities..."
    lastFamily = ''
    highestPriority = -1
    list2 = []
    for record in list1:
        print record
        family = record['Family']
        finalDiagnosisPriority = record['FinalDiagnosisPriority']
        if family != lastFamily:
            lastFamily = family
            highestPriority = finalDiagnosisPriority
            list2.append(record)
        elif finalDiagnosisPriority >= highestPriority:
            list2.append(record)
        else:
            print "Filtering out: ", record
    
    # Calculate the recommendations for each final diagnosis
    print "The families / final diagnosis with the highest priorities are: ", list2
    print "\nMaking recommendations..."
    
    quantOutputs = []   # A list of quantOutput dictionaries
    for record in list2:
        application = record['Application']
        family = record['Family']
        finalDiagnosis = record['FinalDiagnosis']
        log.trace("Making a recommendation for: %s - %s - %s" % (application, family, finalDiagnosis))
        
        # Fetch all of the quant outputs for the final diagnosis
        from ils.diagToolkit.common import fetchOutputsForFinalDiagnosis
        pds, fdQuantOutputs = fetchOutputsForFinalDiagnosis(application, family, finalDiagnosis, database)
        quantOutputs = mergeOutputs(quantOutputs, fdQuantOutputs)
        
        from ils.diagToolkit.recommendation import makeRecommendation
        textRecommendation, recommendations = makeRecommendation(
                record['Application'], record['Family'], record['FinalDiagnosis'], 
                record['FinalDiagnosisId'], record['DiagnosisEntryId'], database)
        quantOutputs = mergeRecommendations(quantOutputs, recommendations)

    print "Recommendations have been made, now calculating the final recommendations"
    finalQuantOutputs = []
    for quantOutput in quantOutputs:
        from ils.diagToolkit.recommendation import calculateFinalRecommendation
        quantOutput = calculateFinalRecommendation(quantOutput)
        quantOutput = checkBounds(quantOutput)
        finalQuantOutputs.append(quantOutput)

    # Store the results in the database
    print "Done managing, the final outputs are: ", finalQuantOutputs
    for quantOutput in finalQuantOutputs:
        updateQuantOutput(quantOutput, database)
        
    print "Finished"

# Check that recommendation against the bounds configured for the output
def checkBounds(quantOutput):
    from ils.common.cast import toBool
    
    print "\n\nChecking Bounds: ", quantOutput
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

    # TODO Need to update the descriptions 
    # TODO Do I need to convert these to incremental - if so, then move the conversion from below up here
    
    if feedbackOutputConditioned > setpointHighLimit:
        quantOutput['OutputLimited'] = True
        quantOutput['OutputLimitedStatus'] = 'Positive Absolute Bound'
        feedbackOutputConditioned=setpointHighLimit
    elif feedbackOutputConditioned < setpointLowLimit:
        quantOutput['OutputLimited'] = True
        quantOutput['OutputLimitedStatus'] = 'Negative Absolute Bound'
        feedbackOutputConditioned=setpointLowLimit    

    quantOutput['FeedbackOutputConditioned'] = feedbackOutputConditioned
      
    return quantOutput
        
# Store the updated quantOutput in the database so that it will show up in the setpoint spreadsheet
def updateQuantOutput(quantOutput, database=''):
    from ils.common.cast import toBool
    
    print "\n\nUpdating QuantOutput: ", quantOutput
    feedbackOutput = quantOutput.get('FeedbackOutput', 0.0)
    feedbackOutputConditioned = quantOutput.get('FeedbackOutputConditioned', 0.0)
    quantOutputId = quantOutput.get('QuantOutputId', 0)
    outputLimitedStatus = quantOutput.get('OutputLimitedStatus', '')
    outputLimited = quantOutput.get('OutputLimited', False)
    outputLimited = toBool(outputLimited)
    outputPercent = quantOutput.get('OutputPercent', 0.0)
    
    # Read the current setpoint
    tagpath = quantOutput.get('TagPath','unknown')
    print "Tag:",tagpath
    qv=system.tag.read(tagpath)
    print qv.value, qv.quality
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
    SQL = "update DtQuantOutput set FeedbackOutput = %f, OutputLimitedStatus = '%s', OutputLimited = %i, "\
        " OutputPercent = %f, FeedbackOutputManual = 0.0, FeedbackOutputConditioned = %f, "\
        " ManualOverride = 0, Active = 1, CurrentSetpoint = %f, FinalSetpoint = %f, DisplayedRecommendation = %f "\
        " where QuantOutputId = %i "\
        % (feedbackOutput, outputLimitedStatus, outputLimited, outputPercent, feedbackOutputConditioned, \
           currentSetpoint, finalSetpoint, displayedRecommendation, quantOutputId)

    log.trace(SQL)
    system.db.runUpdateQuery(SQL, database)
    

# Initialize the diagnosis 
def initializeView(rootContainer):
    console = rootContainer.getPropertyValue("console")
    title = console + ' Console Diagnosis Message Queue'
    rootContainer.setPropertyValue('title', title) 
    print "Done initializing!    Yookoo"
