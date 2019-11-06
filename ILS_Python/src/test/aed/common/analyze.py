'''
Created on Nov 13, 2016

@author: Pete
'''

import system, os, string, time

def compareResults(table, row, key, path, modelType, fileRoot):
    print "In compareResults..."
#    print "fileRoot = ", fileRoot
    
    path = os.path.join(path,modelType)
    
    resultFilename = os.path.join(path,'out')
    resultFilename = os.path.join(resultFilename, fileRoot + "-out.csv")

    goldFilename = os.path.join(path,'gold')
    goldFilename = os.path.join(goldFilename, fileRoot + "-gold.csv")

    #---------------------------------------------------------------------------------------------
    def compare(table=table, row=row, key=key, resultFilename=resultFilename, goldFilename=goldFilename):

        #---------------------------------------------------------------------------------
        def waitUntilComplete():
#            print "waiting"
            status = system.tag.read("[]FT/Control/TestingStatus").value 

            while (status == "Running" or status == "Initializing"):
                time.sleep(1)    # Sleep in seconds
                status = system.tag.read("[]FT/Control/TestingStatus").value
                
            print "   ...the test is complete!"
            
            return
        #---------------------------------------------------------------------------------
        def appendDatabaseInfo(resultFilename, model):
            SQL = "select Status from EventLog where RuleId = ? order by EventLogId"
            pds=system.db.runPrepQuery(SQL, args=[model])
            for record in pds:
                status = record['Status']
                print status
                system.file.writeFile(resultFilename, status, True)
        #---------------------------------------------------------------------------------

        print "   ...waiting for the test to complete..."

        time.sleep(10)    # Give the engine enough time to get started
        waitUntilComplete()
        time.sleep(10)    # Give the engine enough time to stop
        
        # May need a wait here depending on whether or not the last line makes it to the file

#        print "   ...stopping the engine..."
#        from xom.emre.aed.engine.core.wrapper import stop
#        stop(key)
        
        print "   ...analyzing the results..."
        print "The result filename is: <%s>" % resultFilename

        # Check if the Gold file exists
        if not(system.file.fileExists(goldFilename)):
            print "  The gold file <%s> does not exist!" % (goldFilename)
            print "Complete ........................... FAILED"
            table.setValue(row, 'result', 'Failed')
            return
            
        # Check if the output file exists
        if not(system.file.fileExists(resultFilename)):
            print "  The output file <%s> does not exist!" % (resultFilename)
            print "Complete ........................... FAILED"
            table.setValue(row, 'result', 'Failed')
            return

        # Fetch the event log for the model and append it to the output
        # This didn't seem to work, maybe this is a good idea, but need a database cleanup as part of the test then.
        # This also screws up making a rectangular dataset for the diff.
#        ds = table.data
#        model = ds.getValueAt(row, "Models")
#        appendDatabaseInfo(resultFilename, model)
                
        # Check if the two files are identical
        from xom.emre.test.common.diff import diff
        result, explanation = diff(resultFilename, goldFilename, True)
        
        if result:
            txt = 'Passed'
            print "Complete ........................... Passed"
        else:
            txt = 'Failed'
            print "Complete ........................... FAILED"
            
        # Try to update the status row of the table
        table.setValue(row, 'result', txt)

        #---------------------------------------------------------------------------------

#    print "Submitting Compare..."
    system.util.invokeAsynchronous(compare)
#    print "Submitted!"

 