'''
Created on Sep 12, 2014

@author: Pete
'''

import system, string
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.diagToolkit.finalDiagnosis")

# Insert a record into the diagnosis queue
def postDiagnosisEntry(application, family, finalDiagnosis, UUID, diagramUUID, database=""):
    print "Post a diagnosis entry"

    # TODO - need to look this up somehow
    grade = 28
    # Lookup the application Id
    from ils.diagToolkit.common import fetchFinalDiagnosisId
    finalDiagnosisId = fetchFinalDiagnosisId(application, family, finalDiagnosis, database)
    if finalDiagnosisId == None:
        log.error("ERROR posting a diagnosis entry for %s - %s - %s because the final diagnosis was not found!" % (application, family, finalDiagnosis))
        return
    
    print "Fetched Final Diagnosis ID: ", finalDiagnosisId
    textRecommendation = "What is going on here?"
    
    # Insert an entry into the diagnosis queue
    SQL = "insert into DtDiagnosisEntry (FinalDiagnosisId, Status, Timestamp, Grade, TextRecommendation, RecommendationStatus, UUID, DiagramUUID) "\
        "values (%i, 'Active', getdate(), '%s', '%s', 'NONE-MADE', '%s', '%s')" \
        % (finalDiagnosisId, grade, textRecommendation, UUID, diagramUUID)

    print SQL
    system.db.runUpdateQuery(SQL, database)

# Clear the final diagnosis (make the status = 'InActive') 
def clearDiagnosisEntry(application, family, finalDiagnosis, database=""):
    print "Clearing..."

    from ils.diagToolkit.common import fetchFinalDiagnosisId
    finalDiagnosisId = fetchFinalDiagnosisId(application, family, finalDiagnosis, database)
    if finalDiagnosisId == None:
        log.error("ERROR posting a diagnosis entry for %s - %s - %s because the final diagnosis was not found!" % (application, family, finalDiagnosis))
        return

    # Insert an entry into the diagnosis queue
    SQL = "update DtDiagnosisEntry set Status = 'InActive' where FinalDiagnosisId = %i and Status = 'Active'" % (finalDiagnosisId)
    print SQL

    system.db.runUpdateQuery(SQL, database)

# This replaces _em-manage-diagnosis().  Its job is to prioritize the active diagnosis for an application diagnosis queue.
def manage(application, database=""):
    log.trace("Managing diagnosis for application: %s" % (application))

    # -------------------------------------------------------
    # Merge the list of output dictionaries for a final diagnosis with the list for all final diagnosis
    def mergeOutputs(quantOutputs, fdQuantOutputs):
        print "**** TODO finalDiagnosis.mergeOutputs() *****"
        quantOutputs = fdQuantOutputs
        print "The merged outputs are: ", quantOutputs
        return quantOutputs
    # -------------------------------------------------------
    # There are two lists.  The first is a list of all quant outputs and the send is the list of all recommendations.
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
    clearQuantOutputRecommendations(application)
          
    from ils.diagToolkit.common import fetchActiveDiagnosis
    pds = fetchActiveDiagnosis(application)
    
    # If there are no active diagnosis then there is nothing to manage
    if len(pds) == 0:
        print "Exiting the diagnosis manager because there are no active diagnosis!"
        # TODO we may need to clear something!
        return
    
    list1 = []
    highestPriority = pds[0]['FamilyPriority']
    for record in pds:
        if record['FamilyPriority'] == highestPriority:
            print record['Family'], record['FamilyPriority'], record['FinalDiagnosis'], record['FinalDiagnosisPriority']
            list1.append(record)

    # Sort out diagnosis where there are multiple diagnosis for the same family
    family = ''
    list2 = []
    for record in list1:
        if record['Family'] != family:
            family = record['Family']
            finalDiagnosisPriority = record['FinalDiagnosisPriority']
            list2.append(record)
        elif finalDiagnosisPriority == record['FinalDiagnosisPriority']:
            list2.append(record)
    
    # Calculate the recommendations for each final diagnosis
    print "The final diagnosis that must be acted upon has been determined, now calculating preliminary recommendations..."
    
    quantOutputs = []   # A list of quantOutput dictionaries
    for record in list2:
        application = record['Application']
        family = record['Family']
        finalDiagnosis = record['FinalDiagnosis']
        log.trace("Making a recommendation for: %s - %s - %s" % (application, family, finalDiagnosis))
        
        # Fetch all of the quant outputs for the final diagnosis
        from ils.diagToolkit.common import fetchOutputsForFinalDiagnosis
        pds, fdQuantOutputs = fetchOutputsForFinalDiagnosis(application, family, finalDiagnosis)
        quantOutputs = mergeOutputs(quantOutputs, fdQuantOutputs)
        
        from ils.diagToolkit.recommendation import makeRecommendation
        textRecommendation, recommendations = makeRecommendation(record['Application'], record['Family'], record['FinalDiagnosis'], 
                                                                 record['FinalDiagnosisId'], record['DiagnosisEntryId'])
        quantOutputs = mergeRecommendations(quantOutputs, recommendations)

    print "Recommendations have been made, now calculating the final recommendations"
    finalQuantOutputs = []
    for quantOutput in quantOutputs:
        from ils.diagToolkit.recommendation import calculateFinalRecommendation
        quantOutput = calculateFinalRecommendation(quantOutput)
        finalQuantOutputs.append(quantOutput)

    # Store the results in the database
    print "Done managing, the final outputs are: ", finalQuantOutputs
    for quantOutput in finalQuantOutputs:
        updateQuantOutput(quantOutput, database)
        
    print "Finished"

# Store the updated quantOutput in the database so that it will show up in the setpoint spreadsheet
def updateQuantOutput(quantOutput, database=''):
    from ils.common.cast import toBool
    
    print "\n\nUpdating QuantOutput: ", quantOutput
    feedbackOutput = quantOutput.get('FeedbackOutput', 0.0)
    quantOutputId = quantOutput.get('QuantOutputId', 0)
    outputLimitedStatus = quantOutput.get('OutputLimitedStatus', '')
    outputLimited = quantOutput.get('OutputLimited', False)
    outputLimited = toBool(outputLimited)
    outputPercent = quantOutput.get('OutputPercent', 0.0)
    
    # Active is hard-coded to True here because these are the final active quantOutputs
    SQL = "update DtQuantOutput set FeedbackOutput = %f, OutputLimitedStatus = '%s', OutputLimited = %i, "\
        " OutputPercent = %f, FeedbackOutputManual = 0.0, FeedbackOutputConditioned = 0.0, "\
        " ManualOverride = 0, Active = 1 "\
        " where QuantOutputId = %i "\
        % (feedbackOutput, outputLimitedStatus, outputLimited, outputPercent, quantOutputId)

    log.trace(SQL)
    system.db.runUpdateQuery(SQL, database)
    

# Initialize the diagnosis 
def initializeView(rootContainer):
    console = rootContainer.getPropertyValue("console")
    title = console + ' Console Diagnosis Message Queue'
    rootContainer.setPropertyValue('title', title) 
    print "Done initializing!    Yookoo"
