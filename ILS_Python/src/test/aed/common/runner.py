'''
Created on Nov 13, 2016

@author: Pete
'''

import system, string, os, time
from test.aed.common.engine import startExecution, sendModelList
log = system.util.getLogger("com.ils.aed.python.test")

global params, sqlparams, dict, pyResults

# This is called from a button
def runPrepare(rootContainer):
    log.info("In runPrepare...")
    table = rootContainer.getComponent("Table")
    ds = table.data

    # Clear the results column for selected rows
    cnt = 0
    for row in range(ds.rowCount):
        selected = ds.getValueAt(row, 'selected')
        if selected:
            cnt = cnt + 1
            table.setValue(row, 6, '')

    # Enable the timer that will keep the tests running
    if cnt > 0:
        timer = rootContainer.getComponent("Timer")
        timer.running = True
    else:
        system.gui.messageBox("No tests are designated to run!","")

# This is called by the timer
def runCheck(rootContainer, modelType):
    log.trace("checking to see if there is a test to run...")
    
    status = rootContainer.getComponent('Status').text
    if string.upper(status) == 'RUNNING':
        log.trace('A test is running')
        return
    
    # look for a row that is selected with no results
    table = rootContainer.getComponent("Table")
    ds = table.data
            
    # Clear the results column
    for row in range(ds.rowCount):
        selected = ds.getValueAt(row, 'selected')
        result = ds.getValueAt(row, 'result')
        
        if selected:
            if string.upper(result) == 'RUNNING':
                log.trace("A test is already running")
                return
                
            if result == '':
                table.setValue(row, 'result', 'Running')

                models = ds.getValueAt(row, 'models')
                functionName = ds.getValueAt(row, 'function')
                fileRoot = ds.getValueAt(row, 'fileRoot')
                description = ds.getValueAt(row, 'description')
                log.trace("Starting %s..." % (functionName))

                run(rootContainer, modelType, table, models, functionName, fileRoot, description, row)
                return

    # If we get all of the way through, and there is nothing left to run, then stop the timer.
    timer = rootContainer.getComponent("Timer")
    timer.running = False
    
    
def run(rootContainer, modelType, table, models, functionName, fileRoot, description, row):    
    global params, sqlparams, dict
    global pyResults     

    log.infof("=======================================================")
    log.infof("Running %s ...", functionName) 
    pyResults = {}
    
    path = rootContainer.getComponent("Path").text
    cadence = rootContainer.getComponent("Cadence").intValue

    # Convert models into a list
    models = models.split(',')

    if len(models) >= 1:
        modelId1 = models[0]
    else:
        modelId1 = -1
    system.tag.write('[]\FT\Control\Model1Id', int(modelId1))

    if len(models) >= 2:
        modelId2 = models[1]
    else:
        modelId2 = -1
    system.tag.write('[]\FT\Control\Model2Id', int(modelId2))    

    if modelType == 'pid':
        import test.aed.pid.tests
        func = getattr(test.aed.pid.tests, functionName)
#    elif modelType == 'PCA': 
#        func = getattr(xom.emre.test.pca.tests, functionName)
#    elif modelType == 'VFM':
#        func = getattr(xom.emre.test.vfm.tests, functionName)
    else:
        log.errorf("Unsupported model type: %s", modelType)

    # Write the key to a property of the window
    # Maybe the user should get to input this
    key = "AED"    
    rootContainer.setPropertyValue("key", key)    

    #--------------------------------------------------
    def _run(modelId1=modelId1, models=models, cadence=cadence, row=row, description=description, key=key, path=path, modelType=modelType, fileRoot=fileRoot):
        global params, sqlparams, tags, dict
        
        if modelType == 'pid':
            from test.aed.pid.tests import initializeTags
            initializeTags()

        from test.aed.common.initialize import initializeDatabase
        initializeDatabase()
        
        log.tracef("In _run, func is %s", func)
        system.tag.writeToTag("FT/Control/TestingStatus", "Running") 
        
        # Configure the specific test - the function puts the test specific configuration into globals
        log.tracef("Running test #%d - %s", row + 1, description)
        params, sqlparams, tags, modelDictionary = func(key, models)

        # Send the model to the engine        
        log.tracef("Sending the model to the engine...")
        sendModelTestCase(params, sqlparams, tags, key, modelDictionary, cadence, path, modelType, fileRoot)

        # Wait for 1/2 of the cadence
        log.tracef("...sleeping...")
        time.sleep(cadence / 2.0 / 1000.0)
        
        # Start the execution engine
        log.tracef("   ...starting the engine...")
        startExecution(key)        
    #--------------------------------------------------------------------------------------------

    #    print "Submitting..."
    system.util.invokeAsynchronous(_run)
    #    print "Submitted!"

    # Wait until the test completes and then compare the results
    time.sleep(10)
    
    from test.aed.common.analyze import compareResults
    compareResults(table, row, key, path, modelType, fileRoot)

#
def sendModelTestCase(params, sqlparams, tags, key, modelDictionary, cadence, path, modelType, fileRoot):

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
    models.append(modelDictionary)
        
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