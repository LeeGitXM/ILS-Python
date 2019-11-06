'''
Created on Nov 4, 2019

@author: ils
'''

import system, string, time, os
from test.aed.common.engine import startExecution, sendModelList, stopExecution
from test.aed.file.output import writeLine
log = system.util.getLogger("com.ils.test.runner")

def runPrepare(rootContainer):
    testTagFolder = rootContainer.testTagFolder
    print "Running ", testTagFolder, " tests..." 
    system.tag.write(testTagFolder + "/State", "Run")


def prepareEngine(rootContainer, modelType, table, models, functionName, fileRoot, description, row):    
    global params, sqlparams, dict
    global pyResults     

    log.infof("=======================================================")
    log.infof("Preparing the engine ...") 
    pyResults = {}
    
    path = rootContainer.getComponent("Path").text
    cadence = 60

    # Write the key to a property of the window
    # Maybe the user should get to input this
    key = "AED"    
    rootContainer.setPropertyValue("key", key)    

    # Send the model to the engine        
    log.tracef("Sending the model to the engine...")
    tags = ["nyCrappyTag"]
    sendModelTestCase(params, sqlparams, tags, key, cadence, path, modelType, fileRoot)

    # Wait for 1/2 of the cadence
    log.tracef("...sleeping...")
    time.sleep(cadence / 2.0 / 1000.0)
    
    # Start the execution engine
    log.tracef("   ...starting the engine...")
    startExecution(key)        
    #--------------------------------------------------------------------------------------------



    # Wait until the test completes and then compare the results
    time.sleep(10)
    
    from test.aed.common.analyze import compareResults
    compareResults(table, row, key, path, modelType, fileRoot)

#
def sendModelTestCase(params, sqlparams, tags, key, cadence, path, modelType, fileRoot):

    #-----------
    #  Write the first line of the regression test output file.  
    # This runs on the client, writing the actual results happens in the gateway, so if the test is 
    # being run from a client that is not the same computer as the gateway, then the header will
    # be in a different file from the data.
    # 
    def writeHeader(path,format,params,sqlparams, tags) :
        lineList = [format,params,sqlparams,tags]
        line = ",".join(lineList)
        line += "\n"
        system.file.writeFile(path,line)
    #-----------

    print "*** IN sendModelTestCase() ***"

    header = {}
    header['dataCollectionTimeout'] = "%d"%cadence
    header['projectName'] = "AED"    
    header['session'] = key

    # Define the path to the results file in an O/S neutral way
    filename = os.path.join(path,modelType)
    filename = os.path.join(filename,'out')
    filename = os.path.join(filename, fileRoot + "-out.csv")

    header['DataOutputPath'] = filename
    header['TestMode'] = True
    
    format = "MM/dd/yyyy HH:mm:ss"
    header['TimeFormat'] = format
    
    # Define the output columns to extract from the results dictionary and write to the output file.
    header['OutputParameters'] = params
    header['SQLParameters'] = sqlparams
    header['Tags'] = tags

#    header['alternateScript'] = header.get('completionScript')
    header['completionScript'] = "xom.emre.test.common.modelComplete.reportComplete()"
    
    log.tracef("The filename is: <%s>", filename)
    # Write the results header to the output file
    writeHeader(filename, format, params, sqlparams, tags)
    
    # Read the test data file
    filename = os.path.join(path,modelType)
    filename = os.path.join(filename,'in')
    filename = os.path.join(filename, fileRoot + "-in.csv")

    from test.aed.common.data import load, prime

    tags, data = load(filename)
    header['dataTags'] = tags
    header['data'] = data
    log.tracef("The header with data is: %s", header)

    # Prime the tags
    prime(tags, data)
        
    models = []
    models.append(header)            
        
#    print "Path: ", path
#    print "Format: ", format
#    print "Params: ", params
#    print "SQL Params: ", sqlparams    
    
#    print "Sending model list..."
#    print "Key: ", key
#    print "Models: ", models
    sendModelList(key, models)
#    print "... model has been sent!"
    
    return models


def stop(rootContainer):
    testTagFolder = rootContainer.testTagFolder
    print "Stopping ", testTagFolder, " tests..."
    system.tag.write(testTagFolder + "/State", "Stop")

# This is called from a tag change script
def run(stateTagPath):
    import os
    
    #-------------------------------------------
    def initializeTags():
        log.infof("Initializing tags...")
        
        log.infof("...done initializing tags!")
    
    #-------------------------------------------
    def initializeDatabase(db):
        rows = -99
        log.infof("Initializing the database...")
        for SQL in [
            "delete from suppressors",
            "delete from eventLog",
            "delete from events"
            ]:

            log.infof( "   %s", SQL)
            rows=system.db.runPrepUpdate(SQL, database=db)
            log.infof("   ...deleted %d rows", rows)
        
        log.infof("...done initializing the database!")
        
    #----------------
    # Fetch Recommendations
    def logRecommendations(post, filename, db):
        SQL = "select count(*) from DtRecommendation"
        rows = system.db.runScalarQuery(SQL)
        log.trace("There are %i recommendations..." % (rows))
        
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
        log.trace("   fetched %i recommendation..." % (len(pds)))

        header = 'Family,FamilyPriority,FinalDiagnosis,FinalDiagnosisPriority,Status,'\
            'RecommendationStatus,TextRecommendation,QuantOutput, TagPath,Recommendation,'\
            'AutoRecommendation,ManualRecommendation,A,B,C,D,E,F,G,H,I'
        
        log.trace("   writing results to filename: %s" % (filename))
        system.file.writeFile(filename, header, False)

        for record in pds:
            textRecommendation=record['TextRecommendation']
            textRecommendation=string.replace(textRecommendation, '\n',' ')
            txt = "\n%s,%s,%s, %s,%s,%s, %s,%s,%s, %s,%s,%s,0,0,0,0,0,0,0,0,0" % \
                (record['FamilyName'], str(record['FamilyPriority']), record['FinalDiagnosisName'], \
                str(record['FinalDiagnosisPriority']), record['Status'], record['RecommendationStatus'], \
                textRecommendation, record['QuantOutputName'], record['TagPath'],\
                str(record['Recommendation']), str(record['AutoRecommendation']), str(record['ManualRecommendation']))
            log.trace("%s" % (txt))
            system.file.writeFile(filename, txt, True)
            
    #----------------------------------------------------
    # Fetch Quant Outputs
    def logQuantOutputs(post, filename, db):
    
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
            " order by QuantOutputName" % (post)

        pds = system.db.runQuery(SQL, database=db)
        log.trace("   fetched %i  QuantOutputs..." % (len(pds)))

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

            log.trace("%s" % (txt))
            system.file.writeFile(filename, txt, True)

    #----------------------------------------------------
    # Fetch Diagnosis
    def logDiagnosis(post, filename, db):
        SQL = "select FD.FinalDiagnosisName, DE.Status, DE.TextRecommendation, DE.RecommendationStatus, "\
            " DE.Multiplier, FD.Constant "\
            " from DtFinalDiagnosis FD, DtDiagnosisEntry DE "\
            " where FD.FinalDiagnosisId = DE.FinalDiagnosisId"\
            " order by FD.FinalDiagnosisName"

        pds = system.db.runQuery(SQL, database=db)
        log.trace("   fetched %i Diagnosis..." % (len(pds)))

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

            log.trace("%s" % (txt))
            system.file.writeFile(filename, txt, True)

    #-------------------------------------------
    def compareResults(outputFilename, goldFilename, ds, row):
        log.trace("...analyzing the results...")
    
        # Check if the Gold file exists
        if not(system.file.fileExists(goldFilename)):
            log.info("  The gold file <%s> does not exist!" % (goldFilename))
            log.info("Complete ........................... FAILED")
            ds = system.dataset.setValue(ds, row, 'result', 'Failed')
            system.tag.write("Sandbox/Diagnostic/Final Test/Table", ds)
            return ds
        
        # Check if the output file exists
        if not(system.file.fileExists(outputFilename)):
            log.info("  The output file <%s> does not exist!" % (outputFilename))
            log.info("Complete ........................... FAILED")
            ds = system.dataset.setValue(ds, row, 'result', 'Failed')
            system.tag.write("Sandbox/Diagnostic/Final Test/Table", ds)
            return ds
    
        # Check if the two files are identical
        from ils.diagToolkit.test.diff import diff
        result, explanation = diff(outputFilename, goldFilename, log)
                
        if result:
            txt = 'Passed'
            log.info("Complete ........................... Passed")
        else:
            txt = 'Failed'
            log.info("Complete ........................... FAILED")
                
        # Try to update the status row of the table
        ds = system.dataset.setValue(ds, row, 'result', txt)
        system.tag.write("Sandbox/Diagnostic/Final Test/Table", ds)
    
        log.trace("Done analyzing results!")
        return ds
    #-------------------------------------------
    
    log.trace("Running...")
    tagRoot = stateTagPath[:stateTagPath.rfind("/")]
    system.tag.write(stateTagPath,"Running")
#    package="ils.diagToolkit.test.tests"
    tableTagPath=tagRoot + "/Table"
#    path = system.tag.read("Sandbox/Diagnostic/Final Test/Path").value
    ds = system.tag.read(tableTagPath).value
    testDataPath = system.tag.read(tagRoot + "/Test Data Folder").value
    db = "XOM"

    # Clear the results column for selected rows
    cnt = 0
    for row in range(ds.rowCount):
        selected = ds.getValueAt(row, 'selected')
        print "Selected: ", selected
        if selected:
            cnt = cnt + 1
            ds = system.dataset.setValue(ds, row, 'result', 'Running')
            system.tag.write(tableTagPath, ds) 
            
            description = ds.getValueAt(row, 'description')
            resultFile = ds.getValueAt(row, 'resultFile')
            testScript = ds.getValueAt(row, 'testScript')
            dataFile = ds.getValueAt(row, 'dataFile')

            if system.file.fileExists(testDataPath + dataFile):
                # Start with a clean slate            
                initializeDatabase(db)
                initializeTags()
                time.sleep(2)
                
                # Run a specific test
                log.tracef("...starting %s..." % (description))
                
                from test.aed.common.data import simplePlayer
                simplePlayer(testDataPath + dataFile)
    
    #            from test.aed import deadbandTimer
    #            applicationName = eval("deadbandTimer." + functionName)()
                
    #            log.trace("...done! (application = %s)" % (applicationName))
                
                time.sleep(35)
                ds = system.dataset.setValue(ds, row, 'result', 'Analyzing')
                system.tag.write(tableTagPath, ds) 
                
                # Define the path to the results file in an O/S neutral way
    #            outputFilename = os.path.join(path, functionName + "-out.csv")
    #            goldFilename = os.path.join(path, functionName + "-gold.csv")
                
                # Fetch the results from the database
    #            log.trace("...fetching results... (filename=%s, database=%s)" % (outputFilename, db))
    #            logRecommendations(post, outputFilename, db)
    #            logQuantOutputs(post, outputFilename, db)
    #            logDiagnosis(post, outputFilename, db)
                log.trace("...done fetching results!")
                time.sleep(1)
                
                # Compare the results of this run to the Master results
                log.trace("Comparing results...")
                log.infof("Test: %s" % (description))
    #            ds=compareResults(outputFilename, goldFilename, ds, row)
                time.sleep(2)
            else:
                print "crap"
                log.errorf("ERROR: Test %s, data file <%s> does not exist!" % (description, testDataPath + dataFile))
                ds = system.dataset.setValue(ds, row, 'result', 'Data file not found')
                system.tag.write(tableTagPath, ds)

        
    # If we get all of the way through, and there is nothing left to run, then stop the timer.
    log.trace("...totally done!")
    system.tag.write(stateTagPath,"Done")
    

def reportComplete(modelResults):

    def stopTheShow(key):
        print "Stopping the show (stopping the engine and setting the tag)"
        # Stop the Java execution engine
        stopExecution(key)
      
        # Signal the client that the test is finished
        system.tag.write("[AED]FT/Control/TestingStatus", "Stop")
        
        
    print "============== Execution Complete (Final Test) =============="
    
    #
    # We should really exec() the alternateScript
    # For the moment we hard code it.
    #app.engine.core.wrapper.reportComplete(modelResults)
    # I think the idea here is that we call the normal engine stuff and then we call out special
    # test environment logic
    from xom.emre.aed.engine.main import main
    main(modelResults)

    print "=========== End Results (Final Test) ========  "
    # Read the next value from the data file
    if len(modelResults) > 0 :
        properties = modelResults[0]
        try :
            maxCycles = int(properties.get('maxCycles',1000000))
            cycles =    int(properties.get('executionCycles',0))
        except:
            maxCycles = 1000000
            cycles = 0
            print "Caught an exception"
             
        key = properties.get('session','unknown')
        print "Key: ", key
        print properties
        print "Cycles: ", cycles
        if cycles <= maxCycles :
            print "...more work to do..."
            writeLine(modelResults)
            from xom.emre.test.common.data import playNextPoint
            finished = playNextPoint(cycles, properties)
            if finished:
                stopTheShow(key)
                
        if cycles == maxCycles :
            stopTheShow(key)

