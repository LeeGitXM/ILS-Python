'''
Created on Sep 13, 2016

@author: ils
'''

import system, time, string
from ils.diagToolkit.finalDiagnosisClient import postDiagnosisEntry
logger=system.util.getLogger("com.ils.test")

T1TagName='Sandbox/Diagnostic/T1'
T2TagName='Sandbox/Diagnostic/T2'
T3TagName='Sandbox/Diagnostic/T3'
TC100TagName='Sandbox/Diagnostic/TC100/sp/value'
TC101TagName='Sandbox/Diagnostic/TC101/sp/value'

    
# This is called from a button
def initLog():
    time.sleep(1.0)
    SQL = "delete from DtFinalDiagnosisLog"
    system.db.runUpdateQuery(SQL)        
    time.sleep(1.0)

# This is called from a button
def run():
    import os
    
    #-------------------------------------------
    def initializeDatabase(db):
        #TODO Do something smarter about DtRecommendationDefinition
        logger.trace("Initializing the database...")
        for SQL in [
            "delete from DtFinalDiagnosisLog",\
            "delete from DtRecommendation", \
            "delete from QueueDetail", \
            "delete from DtDiagnosisEntry", \
            "delete from DtRecommendationDefinition where FinalDiagnosisId in (select FinalDiagnosisId from DtFinalDiagnosis where FinalDiagnosisName like 'TEST%')", \
            "delete from DtQuantOutput where QuantOutputName like 'TEST%'",\
            "delete from DtFinalDiagnosis where FinalDiagnosisName like 'TEST%'", \
            "delete from DtFamily where FamilyName like 'TEST%'", \
            "delete from DtApplication where ApplicationName like 'TEST%'" ]:
            system.db.runUpdateQuery(SQL, db=db)
        
        logger.trace("...done initializing the database")
        
    #----------------
    # Fetch Recommendations
    def logRecommendations(post, filename, db):
        SQL = "select count(*) from DtRecommendation"
        rows = system.db.runScalarQuery(SQL)
        logger.trace("There are %i recommendations..." % (rows))
        
        SQL = "select F.FamilyName, F.FamilyPriority, FD.FinalDiagnosisName, FD.FinalDiagnosisPriority, DE.Status, "\
            " DE.RecommendationStatus, DE.TextRecommendation, QO.QuantOutputName, QO.TagPath, R.Recommendation, "\
            " R.AutoRecommendation, R.ManualRecommendation "\
            " from DtFamily F, DtFinalDiagnosis FD, DtDiagnosisEntry DE, DtRecommendationDefinition RD, "\
            "      DtQuantOutput QO, DtRecommendation R"\
            " where F.FamilyId = FD.FamilyId "\
            "   and FD.FinalDiagnosisId = DE.FinalDiagnosisId "\
            "   and DE.DiagnosisEntryId = R.DiagnosisEntryId "\
            "   and FD.FinalDiagnosisId = RD.FinalDiagnosisId "\
            "   and RD.QuantOutputId = QO.QuantOutputId "\
            "   and RD.RecommendationDefinitionId = R.RecommendationDefinitionId "\
            " order by FamilyName, FinalDiagnosisName"
        pds = system.db.runQuery(SQL, db=db)
        logger.trace("   fetched %i recommendation..." % (len(pds)))

        header = 'Family,FamilyPriority,FinalDiagnosis,FinalDiagnosisPriority,Status,'\
            'RecommendationStatus,TextRecommendation,QuantOutput, TagPath,Recommendation,'\
            'AutoRecommendation,ManualRecommendation,A,B,C,D,E,F,G,H,I'
        
        logger.trace("   writing results to filename: %s" % (filename))
        system.file.writeFile(filename, header, False)

        for record in pds:
            textRecommendation=record['TextRecommendation']
            textRecommendation=string.replace(textRecommendation, '\n',' ')
            txt = "\n%s,%s,%s, %s,%s,%s, %s,%s,%s, %s,%s,%s,0,0,0,0,0,0,0,0,0" % \
                (record['FamilyName'], str(record['FamilyPriority']), record['FinalDiagnosisName'], \
                str(record['FinalDiagnosisPriority']), record['Status'], record['RecommendationStatus'], \
                textRecommendation, record['QuantOutputName'], record['TagPath'],\
                str(record['Recommendation']), str(record['AutoRecommendation']), str(record['ManualRecommendation']))
            logger.trace("%s" % (txt))
            system.file.writeFile(filename, txt, True)
            
    #----------------------------------------------------
    # Fetch Quant Outputs
    def logQuantOutputs(application, filename, db):
    
        SQL = "select QuantOutputName, TagPath, MostNegativeIncrement, MostPositiveIncrement, "\
            " MinimumIncrement, SetpointHighLimit, SetpointLowLimit, L.LookupName FeedbackMethod, "\
            " OutputLimitedStatus, OutputLimited, OutputPercent, IncrementalOutput, "\
            " FeedbackOutput, FeedbackOutputManual, FeedbackOutputConditioned, "\
            " DisplayedRecommendation, ManualOverride, QO.Active, CurrentSetpoint,  "\
            " FinalSetpoint, DisplayedRecommendation"\
            " from DtQuantOutput QO, lookup L, DtApplication A "\
            " where QO.FeedbackMethodId = L.LookupId "\
            " and L.LookupTypeCode = 'FeedbackMethod' "\
            " and A.ApplicationId = QO.ApplicationId "\
            " and A.ApplicationName = '%s' "\
            " order by QuantOutputName" % (application)

        pds = system.db.runQuery(SQL, db=db)
        logger.trace("   fetched %i  QuantOutputs..." % (len(pds)))

        header = "\nQuantOutput,TagPath,MostNegativeIncrement,MostPositiveIncrement,"\
            "MinimumIncrement,SetpointHighLimit,SetpointLowLimit,FeedbackMethod,"\
            "OutputLimitedStatus,OutputLimited,OutputPercent,IncrementalOutput,"\
            "FeedbackOutput,FeedbackOutputManual,FeedbackOutputConditioned,"\
            "DisplayedRecommendation,ManualOverride,Active,CurrentSetpoint,"\
            "FinalSetpoint,DisplayedRecommendation"
#        print header
        system.file.writeFile(filename, header, True)

        for record in pds:
            txt = "\n%s,%s,%f, %f,%f,%f, %f,%s,%s, %s,%s,%s, %s,%s, %s,%s, %s,%s,%s,%s,%s" % \
                (record['QuantOutputName'], record['TagPath'], record['MostNegativeIncrement'], \
                record['MostPositiveIncrement'], record['MinimumIncrement'], record['SetpointHighLimit'], \
                record['SetpointLowLimit'], record['FeedbackMethod'], record['OutputLimitedStatus'], \
                str(record['OutputLimited']), str(record['OutputPercent']), str(record['IncrementalOutput']), \
                str(record['FeedbackOutput']), str(record['FeedbackOutputManual']), \
                str(record['FeedbackOutputConditioned']), str(record['DisplayedRecommendation']), \
                str(record['ManualOverride']), str(record['Active']), str(record['CurrentSetpoint']), \
                str(record['FinalSetpoint']),str(record['DisplayedRecommendation']) )

            logger.trace("%s" % (txt))
            system.file.writeFile(filename, txt, True)

    #----------------------------------------------------
    # Fetch Diagnosis
    def logDiagnosis(post, filename, db):
        SQL = "select FD.FinalDiagnosisName, DE.Status, DE.TextRecommendation, DE.RecommendationStatus, "\
            " DE.Multiplier, FD.Constant "\
            " from DtFinalDiagnosis FD, DtDiagnosisEntry DE "\
            " where FD.FinalDiagnosisId = DE.FinalDiagnosisId"\
            " order by FD.FinalDiagnosisName"

        pds = system.db.runQuery(SQL, db=db)
        logger.trace("   fetched %i Diagnosis..." % (len(pds)))

        header = "\nFinalDiagnosis,Status,TextRecommendation,RecommendationStatus, "\
            "Multiplier,Constant,A,B,C,D,E,F,G,H,I,J,K,L,M,N,O"
        system.file.writeFile(filename, header, True)

        for record in pds:
            textRecommendation=record['TextRecommendation']
            textRecommendation=string.replace(textRecommendation, '\n',' ')
            txt = "\n%s,%s,%s,%s,%s,%s,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0" % \
                (record['FinalDiagnosisName'], record['Status'], textRecommendation, \
                record['RecommendationStatus'], \
                str(record['Multiplier']),str(record['Constant']))

            logger.trace("%s" % (txt))
            system.file.writeFile(filename, txt, True)

    #-------------------------------------------
    def compareResults(outputFilename, goldFilename, ds, row):
        logger.trace("...analyzing the results...")
    
        # Check if the Gold file exists
        if not(system.file.fileExists(goldFilename)):
            logger.info("  The gold file <%s> does not exist!" % (goldFilename))
            logger.info("Complete ........................... FAILED")
            ds = system.dataset.setValue(ds, row, 'result', 'Failed')
            system.tag.write("Sandbox/Diagnostic/Final Test/Table", ds)
            return ds
        
        # Check if the output file exists
        if not(system.file.fileExists(outputFilename)):
            logger.info("  The output file <%s> does not exist!" % (outputFilename))
            logger.info("Complete ........................... FAILED")
            ds = system.dataset.setValue(ds, row, 'result', 'Failed')
            system.tag.write("Sandbox/Diagnostic/Final Test/Table", ds)
            return ds
    
        # Check if the two files are identical
        from ils.diagToolkit.test.diff import diff
        result, explanation = diff(outputFilename, goldFilename, logger)
                
        if result:
            txt = 'Passed'
            logger.info("Complete ........................... Passed")
        else:
            txt = 'Failed'
            logger.info("Complete ........................... FAILED")
                
        # Try to update the status row of the table
        ds = system.dataset.setValue(ds, row, 'result', txt)
        system.tag.write("Sandbox/Diagnostic/Final Test/Table", ds)
    
        logger.trace("Done analyzing results!")
        return ds
    #-------------------------------------------
    
    logger.trace("Running...")
    system.tag.write("Sandbox/Diagnostic/Final Test/State","Running")
    package="ils.diagToolkit.test.tests"
    tableTagPath="Sandbox/Diagnostic/Final Test/Table"
    path = system.tag.read("Sandbox/Diagnostic/Final Test/Path").value
    ds = system.tag.read(tableTagPath).value
    post = "XO1TEST"
    db = "XOM"

    # Clear the results column for selected rows
    cnt = 0
    for row in range(ds.rowCount):
        selected = ds.getValueAt(row, 'selected')
        if selected:
            cnt = cnt + 1
            ds = system.dataset.setValue(ds, row, 'result', 'Running')
            system.tag.write(tableTagPath, ds) 
                
            functionName = ds.getValueAt(row, 'function')

            # Start with a clean slate            
            initializeDatabase(db)
            time.sleep(2)
            
            # Run a specific test
            logger.trace("...calling %s..." % (functionName))

            from ils.diagToolkit.test import tests
            applicationName = eval("tests." + functionName)()
            
            logger.trace("...done! (application = %s)" % (applicationName))
            
            time.sleep(10)
            ds = system.dataset.setValue(ds, row, 'result', 'Analyzing')
            system.tag.write(tableTagPath, ds) 
            
            # Define the path to the results file in an O/S neutral way
            outputFilename = os.path.join(path, functionName + "-out.csv")
            goldFilename = os.path.join(path, functionName + "-gold.csv")
            
            # Fetch the results from the database
            logger.trace("...fetching results... (filename=%s, db=%s)" % (outputFilename, db))
            logRecommendations(post, outputFilename, db)
            logQuantOutputs(applicationName, outputFilename, db)
            logDiagnosis(post, outputFilename, db)
            logger.trace("...done fetching results!")
            time.sleep(1)
            
            # Compare the results of this run to the Master results
            logger.trace("Comparing results...")
            logger.info("Test: %s" % (functionName))
            ds=compareResults(outputFilename, goldFilename, ds, row)
            time.sleep(2)
            
        
    # If we get all of the way through, and there is nothing left to run, then stop the timer.
    logger.trace("...totally done!")
    system.tag.write("Sandbox/Diagnostic/Final Test/State","Done")


def scrubDatabase(applicationName):
    SQL = "select applicationId from DtApplication where ApplicationName = '%s'" % (applicationName)
    applicationId = system.db.runScalarQuery(SQL)
    
    if applicationId > 0:
        print "Deleting application with id: ", applicationId
        
        # Delete the diagnosis log
        SQL = "delete from DtFinalDiagnosisLog"
        rows=system.db.runUpdateQuery(SQL)
        print "   ...deleted %i rows from DtFinalDiagnosisLog..." % (rows)
        
        # Delete the text recommendations
        SQL = "delete from DtTextRecommendation"
        rows=system.db.runUpdateQuery(SQL)
        print "   ...deleted %i rows from DtTextRecommendation..." % (rows)
        
        # Delete recommendations
        SQL = "delete from DtRecommendation"
        rows=system.db.runUpdateQuery(SQL)
        print "   ...deleted %i rows from DtRecommendations..." % (rows)
        
        # Delete recommendationDefinitionss
        SQL = "select FinalDiagnosisId from DtFinalDiagnosis FD, DtFamily F "\
            " where F.ApplicationID = %i and FD.FamilyId = F.FamilyId " % applicationId
        pds = system.db.runQuery(SQL)
        cnt = 0
        for record in pds:
            finalDiagnosisId = record["FinalDiagnosisId"]
            SQL = "delete from DtRecommendationDefinition where FinalDiagnosisId = %i" % (finalDiagnosisId)
            rows=system.db.runUpdateQuery(SQL)
            cnt=cnt+rows
        print "   ...deleted %i rows from DtRecommendationDefinitions..." % (cnt)
    
        # Delete diagnosisEntries
        SQL = "delete from DtDiagnosisEntry"
        rows=system.db.runUpdateQuery(SQL)
        print "   ...deleted %i rows from DtDiagnosisEntry..." % (rows)
    
        # Delete QuantRecDefs
        SQL = "select QuantOutputId from DtQuantOutput where ApplicationID = %i" % applicationId
        pds = system.db.runQuery(SQL)
        cnt = 0
        for record in pds:
            quantOutputId = record["QuantOutputId"]
            SQL = "delete from DtRecommendationDefinition where QuantOutputId = %i" % (quantOutputId)
            rows = system.db.runUpdateQuery(SQL)
            cnt = cnt + rows
        print "   ...deleted %i rows from DtRecommendationDefinition" % (rows)
        
        # Delete QuantOutputs
        SQL = "delete from DtQuantOutput where ApplicationId = %i" % (applicationId)
        rows=system.db.runUpdateQuery(SQL)
        print "   ...deleted %i rows from DtQuantOutputs..." % (rows)
        
        # Delete FinalDiagnosis
        SQL = "select FamilyId from DtFamily where ApplicationID = %i" % applicationId
        pds = system.db.runQuery(SQL)
        cnt = 0
        for record in pds:
            familyId = record["FamilyId"]
            SQL = "delete from DtFinalDiagnosis where FamilyId = %i" % (familyId)
            rows = system.db.runUpdateQuery(SQL)
            cnt = cnt + rows
        print "   ...deleted %i rows from DtFinalDiagnosis" % (rows)
        
        # Delete Families
        SQL = "delete from DtFamily where ApplicationId = %i" % (applicationId)
        rows=system.db.runUpdateQuery(SQL)
        print "   ...deleted %i rows from DtFamily..." % (rows)
        
        # Delete the Application
        SQL = "delete from DtApplication where ApplicationId = %i" % (applicationId)
        rows=system.db.runUpdateQuery(SQL)
        print "   ...deleted %i rows from DtApplication..." % (rows)
        
        # Delete everything from the message Queues
        SQL = "delete from QueueDetail" 
        rows=system.db.runUpdateQuery(SQL)
        print "   ...deleted %i rows from QueueDetail..." % (rows)
    print "Done!" 
    
# Create everything required for the APP1 test
def insertApp1():
    application='TESTAPP1'
    logbook='Test Logbook'
    post = 'XO1TEST'
    unit = 'TESTUnit'
    logbookId = insertLogbook(logbook)
    postId = insertPost(post, logbookId)
    groupRampMethod='Simple'
    queueKey='TEST'
    app1Id=insertApplication(application, postId, unit, groupRampMethod, queueKey)
    return app1Id

def insertApp1Families(appId,T1Id,T2Id,T3Id,
    FD111calculationMethod='xom.vistalon.diagToolkit.test.test.fd1_1_1',
    FD121calculationMethod='xom.vistalon.diagToolkit.test.test.fd1_2_1',
    FD122calculationMethod='xom.vistalon.diagToolkit.test.test.fd1_2_2',
    FD123calculationMethod='xom.vistalon.diagToolkit.test.test.fd1_2_3',
    FD124calculationMethod='',
    FD125calculationMethod='xom.vistalon.diagToolkit.test.test.fd1_2_5',
    FD126calculationMethod='xom.vistalon.diagToolkit.test.test.fd1_2_6',
    postProcessingCallback=None
    ):
    
    family = 'TESTFamily1_1'
    familyPriority=5.4
    familyId=insertFamily(family, appId, familyPriority)

    finalDiagnosis = 'TESTFD1_1_1'
    finalDiagnosisPriority=2.3
    textRecommendation = "Final Diagnosis 1.1.1"
    finalDiagnosisId=insertFinalDiagnosis(finalDiagnosis, familyId, finalDiagnosisPriority, FD111calculationMethod, 
        textRecommendation, postProcessingCallback=postProcessingCallback)
    insertRecommendationDefinition(finalDiagnosisId, T1Id)

    family = 'TESTFamily1_2'
    familyPriority=7.6
    familyId=insertFamily(family, appId, familyPriority)
    
    finalDiagnosis = 'TESTFD1_2_1'
    finalDiagnosisPriority=4.5
    textRecommendation = "Final Diagnosis 1.2.1"
    finalDiagnosisId=insertFinalDiagnosis(finalDiagnosis, familyId, finalDiagnosisPriority, FD121calculationMethod, 
        textRecommendation, postProcessingCallback=postProcessingCallback)
    insertRecommendationDefinition(finalDiagnosisId, T1Id)
    insertRecommendationDefinition(finalDiagnosisId, T2Id)

    finalDiagnosis = 'TESTFD1_2_2'
    finalDiagnosisPriority=4.5
    textRecommendation = "Final Diagnosis 1.2.2"
    finalDiagnosisId=insertFinalDiagnosis(finalDiagnosis, familyId, finalDiagnosisPriority, FD122calculationMethod, 
        textRecommendation, postProcessingCallback=postProcessingCallback)
    insertRecommendationDefinition(finalDiagnosisId, T2Id)
    insertRecommendationDefinition(finalDiagnosisId, T3Id)
    
    finalDiagnosis = 'TESTFD1_2_3'
    finalDiagnosisPriority=9.8
    textRecommendation = "Final Diagnosis 1.2.3"
    finalDiagnosisId=insertFinalDiagnosis(finalDiagnosis, familyId, finalDiagnosisPriority, FD123calculationMethod, 
        textRecommendation, postProcessingCallback=postProcessingCallback)
    insertRecommendationDefinition(finalDiagnosisId, T1Id)
    insertRecommendationDefinition(finalDiagnosisId, T2Id)
    insertRecommendationDefinition(finalDiagnosisId, T3Id)
    
    finalDiagnosis = 'TESTFD1_2_4'
    finalDiagnosisPriority=4.5
    textRecommendation = "Final Diagnosis 1.2.4 is CONstant"
    finalDiagnosisId=insertFinalDiagnosis(finalDiagnosis, familyId, finalDiagnosisPriority, FD124calculationMethod, 
        textRecommendation, constant=1, postProcessingCallback=postProcessingCallback)
    
    finalDiagnosis = 'TESTFD1_2_5'
    finalDiagnosisPriority=10.2
    textRecommendation = "Final Diagnosis 1.2.5 is a low priority text recommendation.  "
    finalDiagnosisId=insertFinalDiagnosis(finalDiagnosis, familyId, finalDiagnosisPriority, FD125calculationMethod, 
        textRecommendation, postTextRecommendation=1, postProcessingCallback=postProcessingCallback)

    finalDiagnosis = 'TESTFD1_2_6'
    finalDiagnosisPriority=1.2
    textRecommendation = "Final Diagnosis 1.2.6 is a high priority text recommendation.  "
    finalDiagnosisId=insertFinalDiagnosis(finalDiagnosis, familyId, finalDiagnosisPriority, FD126calculationMethod, 
        textRecommendation, postTextRecommendation=1, postProcessingCallback=postProcessingCallback)

# Create everything required for the APP2 test
def insertApp2():
    application='TESTAPP2'
    logbook='Test Logbook'
    post = 'XO1TEST'
    unit = 'TESTUnit'
    logbookId = insertLogbook(logbook)
    postId = insertPost(post, logbookId)
    groupRampMethod='Simple'
    queueKey='TEST'
    app2Id=insertApplication(application, postId, unit, groupRampMethod, queueKey)
    return app2Id

def insertApp2Families(appId,T1Id,T2Id,
    FD211calculationMethod='xom.vistalon.diagToolkit.test.test.fd2_1_1'
    ):

    family = 'TESTFamily2_1'
    familyPriority=5.2
    familyId=insertFamily(family, appId, familyPriority)

    finalDiagnosis = 'TESTFD2_1_1'
    finalDiagnosisPriority=7.8
    textRecommendation = "Final Diagnosis 2.1.1"
    finalDiagnosisId=insertFinalDiagnosis(finalDiagnosis, familyId, finalDiagnosisPriority, FD211calculationMethod, textRecommendation)
    insertRecommendationDefinition(finalDiagnosisId, T1Id)

# Insert a Quant Output
def insertQuantOutput(appId, quantOutput, tagPath, tagValue, mostNegativeIncrement=-500.0, mostPositiveIncrement=500.0, minimumIncrement=0.0001,
        setpointHighLimit=1000.0, setpointLowLimit=-1000.0, feedbackMethod='Most Positive', incrementalOutput=True):
    feedbackMethodId=fetchFeedbackMethodId(feedbackMethod)
    SQL = "insert into DtQuantOutput (QuantOutputName, ApplicationId, TagPath, MostNegativeIncrement, MostPositiveIncrement, MinimumIncrement, "\
        "SetpointHighLimit, SetpointLowLimit, FeedbackMethodId, IncrementalOutput) values "\
        "('%s', %i, '%s', %f, %f, %f, %f, %f, %i, '%s')" % \
        (quantOutput, appId, tagPath, mostNegativeIncrement, mostPositiveIncrement, minimumIncrement,
        setpointHighLimit, setpointLowLimit, feedbackMethodId, incrementalOutput)
    id = system.db.runUpdateQuery(SQL, getKey=True)
    print "Writing ", tagValue, " to ", tagPath
    system.tag.write(tagPath, tagValue, 60)
    return id

# Define a Logbook
def insertLogbook(logbookName):
    SQL = "select logbookId from tkLogbook where LogbookName = '%s'" % (logbookName)
    logbookId = system.db.runScalarQuery(SQL)
    
    if logbookId < 0:
        SQL = "insert into TkLogbook (LogbookName) values ('%s')" % (logbookName)
        logbookId = system.db.runUpdateQuery(SQL, getKey=True)
    return logbookId

# Define a post
def insertPost(post, logbookId):
    SQL = "select postId from tkPost where Post = '%s'" % (post)
    postId = system.db.runScalarQuery(SQL)
    
    if postId < 0:
        SQL = "insert into TkPost (Post, LogbookId) values ('%s', %i)" % (post, logbookId)
        postId = system.db.runUpdateQuery(SQL, getKey=True)
    return postId

# Define a unit
def insertUnit(unitName, postId):
    SQL = "select unitId from TkUnit where UnitName = '%s'" % (unitName)
    unitId = system.db.runScalarQuery(SQL)
    
    if unitId < 0:
        SQL = "insert into TkUnit (UnitName, PostId) values ('%s', %s)" % (unitName, str(postId))
        unitId = system.db.runUpdateQuery(SQL, getKey=True)
    return unitId

# Fetch the Group Ramp Method for the unit
def fetchGroupRampMethodId(groupRampMethod):
    SQL = "select LookupId from Lookup where LookupTypeCode = 'GroupRampMethod' and LookupName = '%s'" % (groupRampMethod)
    groupRampMethodId = system.db.runScalarQuery(SQL)
    return groupRampMethodId

def fetchFeedbackMethodId(feedbackMethod):
    SQL = "select LookupId from Lookup where LookupTypeCode = 'FeedbackMethod' and LookupName = '%s'" % (feedbackMethod)
    feedbackMethodId = system.db.runScalarQuery(SQL)
    return feedbackMethodId

def fetchFinalDiagnosisId(finalDiagnosisName):
    SQL = "select FinalDiagnosisId from DtFinalDiagnosis where FinalDiagnosisName = '%s'" % (finalDiagnosisName)
    finalDiagnosisId = system.db.runScalarQuery(SQL)
    return finalDiagnosisId
        
# Fetch the Queue id for the key
def fetchQueueId(queueKey):
    SQL = "select QueueId from QueueMaster where QueueKey = '%s'" % (queueKey)
    queueId = system.db.runScalarQuery(SQL)
    return queueId
    
# Fetch the Post id for the post
def fetchPostId(post):
    SQL = "select PostId from TkPost where Post = '%s'" % (post)
    postId = system.db.runScalarQuery(SQL)
    return postId
    
# Define an application
def insertApplication(application, postId, unit, groupRampMethod, queueKey):
    print "The group ramp method is: ", groupRampMethod
    unitId=insertUnit(unit, postId)
    groupRampMethodId=fetchGroupRampMethodId(groupRampMethod)
    queueId=fetchQueueId(queueKey)
    SQL = "insert into DtApplication (applicationName, UnitId, GroupRampMethodId, IncludeInMainMenu, MessageQueueId)"\
        " values ('%s', %s, %s, 1, %s)" % (application, str(unitId), str(groupRampMethodId), str(queueId))
    applicationId = system.db.runUpdateQuery(SQL, getKey=True)
    return applicationId

# Create all of the families in this Application
def insertFamily(familyName, applicationId, familyPriority):
    SQL = "insert into DtFamily (FamilyName, ApplicationId, FamilyPriority) values ('%s', %i, %f)" % (familyName, applicationId, familyPriority)
    familyId = system.db.runUpdateQuery(SQL, getKey=True)
    return familyId

# Create a final diagnosis
def insertFinalDiagnosis(finalDiagnosis, familyId, finalDiagnosisPriority, calculationMethod='', 
    textRecommendation='', constant=0, postTextRecommendation=0, postProcessingCallback=None, 
    refreshRate=300):

#    SQL = "insert into DtFinalDiagnosis (FinalDiagnosisName, FamilyId, FinalDiagnosisPriority, CalculationMethod, "\
#        " TextRecommendation, Constant, PostTextRecommendation, " \
#        " PostProcessingCallback, RefreshRate, Active, State) "\
#        " values ('%s', %i, %f, '%s', '%s', %i, %i, '%s', %i, 0, 0)"\
#        % (finalDiagnosis, familyId, finalDiagnosisPriority, calculationMethod, textRecommendation, constant, 
#        postTextRecommendation, postProcessingCallback, refreshRate)
#    finalDiagnosisId = system.db.runUpdateQuery(SQL, getKey=True)
    
    SQL = "insert into DtFinalDiagnosis (FinalDiagnosisName, FamilyId, FinalDiagnosisPriority, CalculationMethod, "\
            " TextRecommendation, Constant, PostTextRecommendation, " \
            " PostProcessingCallback, RefreshRate, Active, State) "\
            " values (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0)"
            
    finalDiagnosisId = system.db.runPrepUpdate(SQL, [finalDiagnosis, familyId, finalDiagnosisPriority, calculationMethod, 
        textRecommendation, constant, postTextRecommendation, postProcessingCallback, refreshRate], getKey=True)
        
    return finalDiagnosisId
    
# Create the recommendationDefinitions
def insertRecommendationDefinition(finalDiagnosisId, quantOutputId):
    SQL = "insert into DtRecommendationDefinition (FinalDiagnosisId, QuantOutputId) "\
        " values (%i, %i)" % (finalDiagnosisId, quantOutputId)
    system.db.runUpdateQuery(SQL)