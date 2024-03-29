'''
Created on Sep 13, 2016

@author: ils
'''

import system, time, string
from ils.diagToolkit.finalDiagnosisClient import postDiagnosisEntry
from ils.common.util import escapeSqlQuotes

from ils.log import getLogger
logger=getLogger("com.ils.test")
    
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
    def initializeTags():
        logger.infof("Initializing tags...")
        system.tag.write("[XOM]Configuration/DiagnosticToolkit/zeroChangeThreshold", 0.00005)
        system.tag.write("[XOM]DiagnosticToolkit/Inputs/T1", 0.1)
        system.tag.write("[XOM]DiagnosticToolkit/Inputs/T2", 0.2)
        system.tag.write("[XOM]DiagnosticToolkit/Inputs/T3", 0.3)
        system.tag.write("[XOM]DiagnosticToolkit/Inputs/T4", 0.4)
        system.tag.write("[XOM]DiagnosticToolkit/Inputs/T5", 0.5)
        system.tag.write("[XOM]DiagnosticToolkit/Inputs/T6", 0.6)
        system.tag.write("[XOM]DiagnosticToolkit/Inputs/T7", 0.7)
        system.tag.write("[XOM]DiagnosticToolkit/Inputs/T8", 0.8)
        system.tag.write("[XOM]DiagnosticToolkit/Inputs/T9", 0.9)
        system.tag.write("[XOM]DiagnosticToolkit/Inputs/T10", 0.1)
        system.tag.write("[XOM]DiagnosticToolkit/Inputs/T11", 0.2)
        system.tag.write("[XOM]DiagnosticToolkit/Inputs/T12", 0.3)
        system.tag.write("[XOM]DiagnosticToolkit/Inputs/T13", 0.4)
        system.tag.write("[XOM]DiagnosticToolkit/Inputs/T14", 0.5)
        system.tag.write("[XOM]DiagnosticToolkit/Inputs/T15", 0.6)
        logger.infof("Initializing the database...")
    
            
    #----------------
    # Fetch Recommendations
    def logTextRecommendations(post, filename, db):
        SQL = "select count(*) from DtTextRecommendation"
        rows = system.db.runScalarQuery(SQL)
        logger.trace("There are %i Text recommendations..." % (rows))
    
        SQL = "select F.FamilyName, F.FamilyPriority, FD.FinalDiagnosisName, FD.FinalDiagnosisPriority, DE.Status,"\
            " DE.RecommendationStatus, R.TextRecommendation "\
            " from DtFamily F, DtFinalDiagnosis FD, DtDiagnosisEntry DE, DtTextRecommendation R "\
            " where F.FamilyId = FD.FamilyId "\
            " and FD.FinalDiagnosisId = DE.FinalDiagnosisId "\
            " and DE.DiagnosisEntryId = R.DiagnosisEntryId "\
            " order by FamilyName, FinalDiagnosisName "
            
        pds = system.db.runQuery(SQL, database=db)
        logger.trace("   fetched %i Text recommendation..." % (len(pds)))

        header = 'Family,FamilyPriority,FinalDiagnosis,FinalDiagnosisPriority,Status,'\
            'RecommendationStatus,TextRecommendation,'\
            'A,B,C,D,E,F,G,H,I,J,K,L,M,N'
        
        logger.trace("   writing results to filename: %s" % (filename))
        system.file.writeFile(filename, header, False)
        
        for record in pds:
            textRecommendation=record['TextRecommendation']
            textRecommendation=string.replace(textRecommendation, '\n',' ')
            txt = "\n%s,%s,%s, %s,%s,%s, %s,,0,0,0,0,0,0,0,0,0,0,0,0,0,0" % \
                (record['FamilyName'], str(record['FamilyPriority']), record['FinalDiagnosisName'], \
                str(record['FinalDiagnosisPriority']), record['Status'], record['RecommendationStatus'], \
                textRecommendation)
            logger.trace("%s" % (txt))
            system.file.writeFile(filename, txt, True)
    
    
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
        pds = system.db.runQuery(SQL, database=db)
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
            
    def logRecommendationsExtended(post, filename, db):
        print "In logRecommendationsExtended()..."
        SQL = "select count(*) from DtRecommendation"
        rows = system.db.runScalarQuery(SQL)
        logger.trace("There are %i recommendations..." % (rows))
            
        SQL = "SELECT     DtFamily.FamilyName, DtFamily.FamilyPriority, DtFinalDiagnosis.FinalDiagnosisName, DtFinalDiagnosis.FinalDiagnosisPriority, DtDiagnosisEntry.Status, "\
            " DtDiagnosisEntry.RecommendationStatus, DtDiagnosisEntry.TextRecommendation, DtQuantOutput.QuantOutputName, DtQuantOutput.TagPath, "\
            " DtRecommendation.Recommendation, DtRecommendation.AutoRecommendation, DtRecommendation.ManualRecommendation, DtQuantOutputRamp.Ramp "\
            " FROM  DtFamily INNER JOIN "\
             " DtFinalDiagnosis ON DtFamily.FamilyId = DtFinalDiagnosis.FamilyId INNER JOIN "\
            " DtDiagnosisEntry ON DtFinalDiagnosis.FinalDiagnosisId = DtDiagnosisEntry.FinalDiagnosisId INNER JOIN "\
            " DtRecommendationDefinition ON DtFinalDiagnosis.FinalDiagnosisId = DtRecommendationDefinition.FinalDiagnosisId INNER JOIN "\
            " DtQuantOutput ON DtRecommendationDefinition.QuantOutputId = DtQuantOutput.QuantOutputId INNER JOIN "\
            " DtRecommendation ON DtDiagnosisEntry.DiagnosisEntryId = DtRecommendation.DiagnosisEntryId AND "\
            " DtRecommendationDefinition.RecommendationDefinitionId = DtRecommendation.RecommendationDefinitionId LEFT OUTER JOIN "\
            " DtQuantOutputRamp ON DtQuantOutput.QuantOutputId = DtQuantOutputRamp.QuantOutputId "
            
        print SQL
        pds = system.db.runQuery(SQL, database=db)
        logger.trace("   fetched %i recommendation..." % (len(pds)))

        header = 'Family,FamilyPriority,FinalDiagnosis,FinalDiagnosisPriority,Status,'\
            'RecommendationStatus,TextRecommendation,QuantOutput, TagPath,Recommendation,'\
            'AutoRecommendation,ManualRecommendation,Ramp,B,C,D,E,F,G,H,I'
        
        logger.trace("   writing results to filename: %s" % (filename))
        system.file.writeFile(filename, header, False)

        for record in pds:
            textRecommendation=record['TextRecommendation']
            textRecommendation=string.replace(textRecommendation, '\n',' ')
            txt = "\n%s,%s,%s, %s,%s,%s, %s,%s,%s, %s,%s,%s,%s,0,0,0,0,0,0,0,0" % \
                (record['FamilyName'], str(record['FamilyPriority']), record['FinalDiagnosisName'], \
                str(record['FinalDiagnosisPriority']), record['Status'], record['RecommendationStatus'], \
                textRecommendation, record['QuantOutputName'], record['TagPath'],\
                str(record['Recommendation']), str(record['AutoRecommendation']), str(record['ManualRecommendation']), str(record['Ramp']) )
            logger.trace("%s" % (txt))
            system.file.writeFile(filename, txt, True)
            
    #----------------------------------------------------
    # Fetch Quant Outputs
    def logQuantOutputs(post, applicationName, filename, db):
    
        SQL = "select QuantOutputName, TagPath, MostNegativeIncrement, MostPositiveIncrement, "\
            " MinimumIncrement, SetpointHighLimit, SetpointLowLimit, L.LookupName FeedbackMethod, "\
            " OutputLimitedStatus, OutputLimited, OutputPercent, IncrementalOutput, "\
            " FeedbackOutput, FeedbackOutputManual, FeedbackOutputConditioned, "\
            " DisplayedRecommendation, ManualOverride, QO.Active, CurrentSetpoint,  "\
            " FinalSetpoint, DisplayedRecommendation"\
            " from DtQuantOutput QO, lookup L, DtApplication A, TkUnit U, TkPost P "\
            " where QO.FeedbackMethodId = L.LookupId "\
            " and L.LookupTypeCode = 'FeedbackMethod' "\
            " and A.ApplicationId = QO.ApplicationId "\
            " and A.UnitId = U.UnitId "\
            " and P.PostId = U.PostId "\
            " and P.Post = '%s' "\
            " and A.ApplicationName like '%s' "\
            " order by QuantOutputName" % (post, applicationName)

        pds = system.db.runQuery(SQL, database=db)
        logger.trace("   fetched %i  QuantOutputs..." % (len(pds)))

        header = "\nQuantOutput,TagPath,MostNegativeIncrement,MostPositiveIncrement,"\
            "MinimumIncrement,SetpointHighLimit,SetpointLowLimit,FeedbackMethod,"\
            "OutputLimitedStatus,OutputLimited,OutputPercent,IncrementalOutput,"\
            "FeedbackOutput,FeedbackOutputManual,FeedbackOutputConditioned,"\
            "DisplayedRecommendation,ManualOverride,Active,CurrentSetpoint,"\
            "FinalSetpoint,DisplayedRecommendation"

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
    def logDiagnosis(post, applicationName,  filename, db):
        SQL = "select FD.FinalDiagnosisName, DE.Status, DE.TextRecommendation, DE.RecommendationStatus, "\
            " DE.Multiplier, FD.Constant "\
            " from DtApplication A, DtFamily F, DtFinalDiagnosis FD, DtDiagnosisEntry DE "\
            " where A.ApplicationId = F.ApplicationId"\
            " and F.FamilyId = FD.FamilyId"\
            " and FD.FinalDiagnosisId = DE.FinalDiagnosisId"\
            " and A.applicationName like '%s' "\
            " order by FD.FinalDiagnosisName" % (applicationName)

        pds = system.db.runQuery(SQL, database=db)
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
        logger.info("...analyzing the results...")
    
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
    
    logger.infof("In %s.run() Starting to run tests...", __name__)
    system.tag.write("Sandbox/Diagnostic/Final Test/State","Running")
    package="ils.diagToolkit.test.tests"
    tableTagPath="Sandbox/Diagnostic/Final Test/Table"
    path = system.tag.read("Sandbox/Diagnostic/Final Test/Path").value
    ds = system.tag.read(tableTagPath).value
    post = "XO1TEST"
    projectName = "XOM"
    db = system.tag.read("Sandbox/Diagnostic/Final Test/db").value
    provider = "XOM"

    # Clear the results column for selected rows
    cnt = 0
    for row in range(ds.rowCount):
        selected = ds.getValueAt(row, 'selected')
        if selected:
            cnt = cnt + 1
            ds = system.dataset.setValue(ds, row, 'result', 'Running')
            system.tag.write(tableTagPath, ds) 
                
            functionName = ds.getValueAt(row, 'function')
            logger.infof("Starting to prepare to run: %s", functionName)

            # Start with a clean slate            
            initializeDatabase(db)
            initializeTags()
            time.sleep(2)
            
            # Run a specific test
            logger.trace("...calling %s..." % (functionName))
            from ils.diagToolkit.test import tests
            applicationName = eval("tests." + functionName)(db)
            logger.trace("...done! (application = %s)" % (applicationName))
            
            time.sleep(60)
            ds = system.dataset.setValue(ds, row, 'result', 'Analyzing')
            system.tag.write(tableTagPath, ds) 
            
            # Define the path to the results file in an O/S neutral way
            outputFilename = os.path.join(path, functionName + "-out.csv")
            goldFilename = os.path.join(path, functionName + "-gold.csv")
            
            # Fetch the results from the database
            logger.trace("...fetching results... (filename=%s, database=%s)" % (outputFilename, db))
            
            resultsMode = ds.getValueAt(row, 'Results')
            print "The results mode is: ", resultsMode
            
            if resultsMode == "Basic":
                logRecommendations(post, outputFilename, db)
                logQuantOutputs(post, applicationName, outputFilename, db)
                logDiagnosis(post, applicationName, outputFilename, db)
            elif resultsMode == "Extended":
                logRecommendationsExtended(post, outputFilename, db)
                logQuantOutputs(post, applicationName, outputFilename, db)
                logDiagnosis(post, applicationName, outputFilename, db)
                
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

#-------------------------------------------
def initializeDatabase(db):
    rows = -99
    logger.infof("Initializing the database...")

    applicationId = system.db.runScalarQuery("select ApplicationId from DtApplication where ApplicationName = 'FINAL_TEST_1' ", db)
    logger.tracef("The application id is: %s", str(applicationId))
    
    SQL_LIST = [
        "delete from DtFinalDiagnosisLog",
        "delete from DtRecommendation", 
        "delete from QueueDetail", 
        "delete from DtDiagnosisEntry",
        
        "delete from DtRecommendationDefinition where QuantOutputId in (select QuantOutputId from DtQuantOutput where QuantOutputName = 'TESTQ1')",
        "delete from DtQuantOutput where QuantOutputName = 'TESTQ1' ", 
        "delete from DtRecommendationDefinition where QuantOutputId in (select QuantOutputId from DtQuantOutput where QuantOutputName = 'TESTQ2')", 
        "delete from DtQuantOutput where QuantOutputName = 'TESTQ2' ",
        "delete from DtRecommendationDefinition where QuantOutputId in (select QuantOutputId from DtQuantOutput where QuantOutputName = 'TESTQ3')",
        "delete from DtQuantOutput where QuantOutputName = 'TESTQ3' ",
        "delete from DtRecommendationDefinition where QuantOutputId in (select QuantOutputId from DtQuantOutput where QuantOutputName = 'TEST_Q21')", 
        "delete from DtQuantOutput where QuantOutputName = 'TEST_Q21' ",
        "delete from DtRecommendationDefinition where QuantOutputId in (select QuantOutputId from DtQuantOutput where QuantOutputName = 'TEST_Q22')", 
        "delete from DtQuantOutput where QuantOutputName = 'TEST_Q22' ",
        "delete from DtRecommendationDefinition where QuantOutputId in (select QuantOutputId from DtQuantOutput where QuantOutputName = 'TEST_Q23')",
        "delete from DtQuantOutput where QuantOutputName = 'TEST_Q23' ",
        "delete from DtRecommendationDefinition where QuantOutputId in (select QuantOutputId from DtQuantOutput where QuantOutputName = 'TEST_Q24')",
        "delete from DtQuantOutput where QuantOutputName = 'TEST_Q24' ",
        "delete from DtRecommendationDefinition where QuantOutputId in (select QuantOutputId from DtQuantOutput where QuantOutputName = 'TEST_Q25')", 
        "delete from DtQuantOutput where QuantOutputName = 'TEST_Q25' ",
    
        "delete from DtFinalDiagnosis where FinalDiagnosisName like 'FT_%'", 
        "delete from DtFamily where FamilyName like 'FT_FAMILY%'", 
        "delete from DtApplication where ApplicationName like 'FINAL_TEST%'"
        ]
    
    for SQL in SQL_LIST:
        logger.tracef( "   %s", SQL)
        rows=system.db.runPrepUpdate(SQL, database=db)
        logger.tracef("   ...deleted %d rows", rows)
    
    logger.tracef("...done initializing the database")


def scrubDatabaseXXX(applicationName):
    print "Scrubbing recommendations for application: %s", applicationName
    
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
def insertApp1(db, groupRampMethod='Shortest'):
    application='FINAL_TEST_1'
    messageQueue="Test"
    logbook='Test Logbook'
    post = 'XO1TEST'
    unit = 'TESTUnit'
    messageQueueId = insertMessageQueue(messageQueue, db)
    logbookId = insertLogbook(logbook, db)
    postId = insertPost(post, messageQueueId, logbookId, db)
    queueKey='Test'
    managed=1
    app1Id=insertApplication(application, postId, unit, groupRampMethod, queueKey, managed, db)
    return app1Id

def insertApp1Families(appId,T1Id,T2Id,T3Id,
    FD111calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_1_1',
    FD121calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_1',
    FD122calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_2',
    FD123calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3',
    FD124calculationMethod='',
    FD125calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_5',
    FD126calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_6',
    postProcessingCallback=None,
    FD111Priority=2.3,
    FD121Priority=4.5,
    FD122Priority=4.5,
    FD123Priority=9.8,
    FD124Priority=4.5,
    FD125Priority=10.2,
    FD126Priority=1.2,
    insertExtraRecDef=False,
    db="CRAP",
    trapInsignificantRecommendations=1
    ):
    
    family = 'FT_Family1_1'
    familyPriority=5.4
    familyId=insertFamily(family, appId, familyPriority, db)

    finalDiagnosis = 'FT_FD1_1_1'
    finalDiagnosisPriority=FD111Priority
    textRecommendation = "Final Diagnosis 1.1.1"
    finalDiagnosisId=insertFinalDiagnosis(finalDiagnosis, familyId, finalDiagnosisPriority, FD111calculationMethod, textRecommendation, 
                        postProcessingCallback=postProcessingCallback, db=db, trapInsignificantRecommendations=trapInsignificantRecommendations)
    insertRecommendationDefinition(finalDiagnosisId, T1Id, db)

    family = 'FT_Family1_2'
    familyPriority=7.6
    familyId=insertFamily(family, appId, familyPriority, db)
    
    finalDiagnosis = 'FT_FD1_2_1'
    finalDiagnosisPriority = FD121Priority
    textRecommendation = "Final Diagnosis 1.2.1"
    finalDiagnosisId=insertFinalDiagnosis(finalDiagnosis, familyId, finalDiagnosisPriority, FD121calculationMethod, textRecommendation, 
                                          postProcessingCallback=postProcessingCallback, db=db, trapInsignificantRecommendations=trapInsignificantRecommendations)
    insertRecommendationDefinition(finalDiagnosisId, T1Id, db)
    insertRecommendationDefinition(finalDiagnosisId, T2Id, db)
    if insertExtraRecDef:
        insertRecommendationDefinition(finalDiagnosisId, T3Id, db)

    finalDiagnosis = 'FT_FD1_2_2'
    finalDiagnosisPriority=FD122Priority
    textRecommendation = "Final Diagnosis 1.2.2"
    finalDiagnosisId=insertFinalDiagnosis(finalDiagnosis, familyId, finalDiagnosisPriority, FD122calculationMethod, textRecommendation, 
                                          postProcessingCallback=postProcessingCallback, db=db, trapInsignificantRecommendations=trapInsignificantRecommendations)
    insertRecommendationDefinition(finalDiagnosisId, T2Id, db)
    insertRecommendationDefinition(finalDiagnosisId, T3Id, db)
    
    finalDiagnosis = 'FT_FD1_2_3'
    finalDiagnosisPriority=FD123Priority
    textRecommendation = "Final Diagnosis 1.2.3"
    finalDiagnosisId=insertFinalDiagnosis(finalDiagnosis, familyId, finalDiagnosisPriority, FD123calculationMethod, textRecommendation, 
                                          postProcessingCallback=postProcessingCallback, db=db, trapInsignificantRecommendations=trapInsignificantRecommendations)
    insertRecommendationDefinition(finalDiagnosisId, T1Id, db)
    insertRecommendationDefinition(finalDiagnosisId, T2Id, db)
    insertRecommendationDefinition(finalDiagnosisId, T3Id, db)
    
    finalDiagnosis = 'FT_FD1_2_4'
    finalDiagnosisPriority=FD124Priority
    textRecommendation = "Final Diagnosis 1.2.4 is CONstant"
    finalDiagnosisId=insertFinalDiagnosis(finalDiagnosis, familyId, finalDiagnosisPriority, FD124calculationMethod, textRecommendation, 
                                          constant=1, postProcessingCallback=postProcessingCallback, db=db, trapInsignificantRecommendations=trapInsignificantRecommendations)
    
    finalDiagnosis = 'FT_FD1_2_5'
    finalDiagnosisPriority=FD125Priority
    textRecommendation = "Final Diagnosis 1.2.5 is a low priority text recommendation.  "
    finalDiagnosisId=insertFinalDiagnosis(finalDiagnosis, familyId, finalDiagnosisPriority, FD125calculationMethod, textRecommendation, 
                                          postTextRecommendation=1, postProcessingCallback=postProcessingCallback, db=db, trapInsignificantRecommendations=trapInsignificantRecommendations)

    finalDiagnosis = 'FT_FD1_2_6'
    finalDiagnosisPriority=FD126Priority
    textRecommendation = "Final Diagnosis 1.2.6 is a high priority text recommendation which is correct 95% of the time.  "
    finalDiagnosisId=insertFinalDiagnosis(finalDiagnosis, familyId, finalDiagnosisPriority, FD126calculationMethod, textRecommendation, 
                                          postTextRecommendation=1, postProcessingCallback=postProcessingCallback, db=db, trapInsignificantRecommendations=trapInsignificantRecommendations)

# Create everything required for the APP2 test
def insertApp2(db):
    application='FINAL_TEST_2'
    messageQueue="Test"
    logbook='Test Logbook'
    post = 'XO1TEST'
    unit = 'TESTUnit'
    messageQueueId = insertMessageQueue(messageQueue, db)
    logbookId = insertLogbook(logbook, db)
    postId = insertPost(post, messageQueueId, logbookId, db)
    groupRampMethod='Shortest'
    queueKey='Test'
    managed=1
    app2Id=insertApplication(application, postId, unit, groupRampMethod, queueKey, managed, db)
    return app2Id

def insertApp2Families(appId, Q21_id, Q22_id, Q23_id, Q24_id, Q25_id, Q26_id, FD211calculationMethod='ils.diagToolkit.test.calculationMethods.fd2_1_1', db="CRAP"):
    logger.tracef("Entering insertApp2Families...")

    family = 'FT_Family2_1'
    familyPriority=5.2
    familyId=insertFamily(family, appId, familyPriority, db)

    finalDiagnosis = 'FT_FD2_1_1'
    finalDiagnosisPriority=7.8
    textRecommendation = "Final Diagnosis 2.1.1"
    logger.tracef("...inserting final diagnosis...")
    finalDiagnosisId=insertFinalDiagnosis(finalDiagnosis, familyId, finalDiagnosisPriority, FD211calculationMethod, textRecommendation, db=db)
    logger.tracef("...inserting recdefs...")
    insertRecommendationDefinition(finalDiagnosisId, Q21_id, db)
    insertRecommendationDefinition(finalDiagnosisId, Q22_id, db)
    insertRecommendationDefinition(finalDiagnosisId, Q23_id, db)
    insertRecommendationDefinition(finalDiagnosisId, Q24_id, db)
    insertRecommendationDefinition(finalDiagnosisId, Q25_id, db)
    insertRecommendationDefinition(finalDiagnosisId, Q26_id, db)
    logger.tracef("...done inserting App2!")

# Insert a Quant Output
def insertQuantOutput(appId, quantOutput, tagPath, tagValue, mostNegativeIncrement=-500.0, mostPositiveIncrement=500.0, minimumIncrement=0.0001,
        setpointHighLimit=1000.0, setpointLowLimit=-1000.0, feedbackMethod='Most Positive', incrementalOutput=True, db="CRAP"):
    
    logger.tracef("Inserting QuantOutput named: %s", quantOutput)
    feedbackMethodId=fetchFeedbackMethodId(feedbackMethod, db)
    SQL = "insert into DtQuantOutput (QuantOutputName, ApplicationId, TagPath, MostNegativeIncrement, MostPositiveIncrement, MinimumIncrement, "\
        "SetpointHighLimit, SetpointLowLimit, FeedbackMethodId, IncrementalOutput) values "\
        "('%s', %i, '%s', %f, %f, %f, %f, %f, %i, '%s')" % \
        (quantOutput, appId, tagPath, mostNegativeIncrement, mostPositiveIncrement, minimumIncrement,
        setpointHighLimit, setpointLowLimit, feedbackMethodId, incrementalOutput)
    logger.tracef("...SQL: %s", SQL)
    quantOutputId = system.db.runUpdateQuery(SQL, getKey=True, database=db)
    logger.tracef("...inserted a quant output with id: %d", quantOutputId)
    logger.tracef("Writing %s to %s", str(tagValue), tagPath)
    system.tag.write(tagPath, tagValue, 60)
    return quantOutputId

# Define a Message Queue
def insertMessageQueue(messageQueue, db):
    SQL = "select QueueId from QueueMaster where QueueKey = '%s'" % (messageQueue)
    queueId = system.db.runScalarQuery(SQL, database=db)
    
    if queueId < 0:
        SQL = "insert into QueueMaster (QueueKey, Title, AutoViewSeverityThreshold, Position, AutoViewAdmin, AutoViewAE, AutoViewOperator) values ('%s', '%s', 10, 'center', 0, 0, 0)" % (messageQueue, messageQueue)
        queueId = system.db.runUpdateQuery(SQL, getKey=True, database=db)
    return queueId

# Define a Logbook
def insertLogbook(logbookName, db):
    SQL = "select logbookId from tkLogbook where LogbookName = '%s'" % (logbookName)
    logbookId = system.db.runScalarQuery(SQL, database=db)
    
    if logbookId < 0:
        SQL = "insert into TkLogbook (LogbookName) values ('%s')" % (logbookName)
        logbookId = system.db.runUpdateQuery(SQL, getKey=True, database=db)
    return logbookId

# Define a post
def insertPost(post, messageQueueId, logbookId, db):
    SQL = "select postId from tkPost where Post = '%s'" % (post)
    postId = system.db.runScalarQuery(SQL, database=db)
    
    if postId < 0:
        SQL = "insert into TkPost (Post, MessageQueueId, LogbookId, DownloadActive) values ('%s', %d, %d, 0)" % (post, messageQueueId, logbookId)
        postId = system.db.runUpdateQuery(SQL, getKey=True, database=db)
    return postId

# Define a unit
def insertUnit(unitName, postId, db):
    SQL = "select unitId from TkUnit where UnitName = '%s'" % (unitName)
    unitId = system.db.runScalarQuery(SQL, database=db)
    
    if unitId < 0:
        SQL = "insert into TkUnit (UnitName, PostId) values ('%s', %s)" % (unitName, str(postId))
        unitId = system.db.runUpdateQuery(SQL, getKey=True, database=db)
    return unitId

# Fetch the Group Ramp Method for the unit
def fetchGroupRampMethodId(groupRampMethod, db):
    SQL = "select LookupId from Lookup where LookupTypeCode = 'GroupRampMethod' and LookupName = '%s'" % (groupRampMethod)
    groupRampMethodId = system.db.runScalarQuery(SQL, database=db)
    return groupRampMethodId

def fetchFeedbackMethodId(feedbackMethod, db):
    SQL = "select LookupId from Lookup where LookupTypeCode = 'FeedbackMethod' and LookupName = '%s'" % (feedbackMethod)
    feedbackMethodId = system.db.runScalarQuery(SQL, database=db)
    return feedbackMethodId

def fetchFinalDiagnosisId(finalDiagnosisName, db):
    SQL = "select FinalDiagnosisId from DtFinalDiagnosis where FinalDiagnosisName = '%s'" % (finalDiagnosisName)
    finalDiagnosisId = system.db.runScalarQuery(SQL, database=db)
    return finalDiagnosisId
        
# Fetch the Queue id for the key
def fetchQueueId(queueKey, db):
    SQL = "select QueueId from QueueMaster where QueueKey = '%s'" % (queueKey)
    queueId = system.db.runScalarQuery(SQL, database=db)
    return queueId
    
# Fetch the Post id for the post
def fetchPostId(post, db):
    SQL = "select PostId from TkPost where Post = '%s'" % (post)
    postId = system.db.runScalarQuery(SQL, database=db)
    return postId
    
# Define an application
def insertApplication(application, postId, unit, groupRampMethod, queueKey, managed, db):
    unitId=insertUnit(unit, postId, db)
    groupRampMethodId=fetchGroupRampMethodId(groupRampMethod, db)
    queueId=fetchQueueId(queueKey, db)
    SQL = "insert into DtApplication (applicationName, UnitId, GroupRampMethodId, IncludeInMainMenu, MessageQueueId, Managed, NotificationStrategy)"\
        " values ('%s', %s, %s, 1, %s, %s, 'ocAlert')" % (application, str(unitId), str(groupRampMethodId), str(queueId), str(managed))
    applicationId = system.db.runUpdateQuery(SQL, getKey=True, database=db)
    return applicationId

# Create all of the families in this Application
def insertFamily(familyName, applicationId, familyPriority, db):
    SQL = "insert into DtFamily (FamilyName, ApplicationId, FamilyPriority) values ('%s', %i, %f)" % (familyName, applicationId, familyPriority)
    familyId = system.db.runUpdateQuery(SQL, getKey=True, database=db)
    return familyId

# Create a final diagnosis
def insertFinalDiagnosis(finalDiagnosis, familyId, finalDiagnosisPriority, calculationMethod='', 
    textRecommendation='', constant=0, postTextRecommendation=0, postProcessingCallback=None, 
    refreshRate=300, db="CRAP", trapInsignificantRecommendations=0):

#    SQL = "insert into DtFinalDiagnosis (FinalDiagnosisName, FamilyId, FinalDiagnosisPriority, CalculationMethod, "\
#        " TextRecommendation, Constant, PostTextRecommendation, " \
#        " PostProcessingCallback, RefreshRate, Active, State) "\
#        " values ('%s', %i, %f, '%s', '%s', %i, %i, '%s', %i, 0, 0)"\
#        % (finalDiagnosis, familyId, finalDiagnosisPriority, calculationMethod, textRecommendation, constant, 
#        postTextRecommendation, postProcessingCallback, refreshRate)
#    finalDiagnosisId = system.db.runUpdateQuery(SQL, getKey=True)
    
    SQL = "insert into DtFinalDiagnosis (FinalDiagnosisName, FamilyId, FinalDiagnosisPriority, CalculationMethod, "\
            " TextRecommendation, Constant, PostTextRecommendation, " \
            " PostProcessingCallback, RefreshRate, Active, State, TrapInsignificantRecommendations) "\
            " values (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?)"
    args = [finalDiagnosis, familyId, finalDiagnosisPriority, calculationMethod, 
        textRecommendation, constant, postTextRecommendation, postProcessingCallback, refreshRate, trapInsignificantRecommendations]
    
    logger.tracef("%s", SQL)
    logger.tracef("%s", str(args))
            
    finalDiagnosisId = system.db.runPrepUpdate(SQL, args, getKey=True, database=db)
    logger.tracef("Insert a new Final Diagnosis with id: %d", finalDiagnosisId)
    return finalDiagnosisId
    
# Create the recommendationDefinitions
def insertRecommendationDefinition(finalDiagnosisId, quantOutputId, db):
    SQL = "insert into DtRecommendationDefinition (FinalDiagnosisId, QuantOutputId) "\
        " values (%i, %i)" % (finalDiagnosisId, quantOutputId)
    system.db.runUpdateQuery(SQL, database=db)
    
# Update the text recommendation for a Final Diagnosis
def updateFinalDiagnosisTextRecommendation(finalDiagnosisName, textRecommendation, db):
    textRecommendation = escapeSqlQuotes(textRecommendation)
    SQL = "update DtFinalDiagnosis set TextRecommendation = '%s' where FinalDiagnosisName = '%s' " % (textRecommendation, finalDiagnosisName)
    logger.tracef("%s", SQL)   
    rows = system.db.runUpdateQuery(SQL, database=db)
    logger.tracef("Updated %d rows", rows)