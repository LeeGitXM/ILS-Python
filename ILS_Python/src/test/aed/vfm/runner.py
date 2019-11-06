'''
Created on Nov 13, 2016

@author: Pete
'''
global fileRoot, params, sqlparams, dict, pyResults

# This is called from a button
def runPrepare(rootContainer):
    import system, os

    table = rootContainer.getComponent("Table")
    ds = table.data
    pds = system.dataset.toPyDataSet(ds)

    # Clear the results column for selected rows
    cnt = 0
    for row in range(ds.rowCount):
        selected = ds.getValueAt(row, 'selected')
        if selected:
            cnt = cnt + 1
            table.setValue(row, 5, '')

    # Enable the timer that will keep the tests running
    if cnt > 0:
        timer = rootContainer.getComponent("Timer")
        timer.running = True


# This is called by the timer
def runCheck(rootContainer):
    import app, system, string
    
    #print "checking to see if there is a test to run..."
    
    status = rootContainer.getComponent('Status').text
    if string.upper(status) == 'RUNNING':
        # print 'A test is running'
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
                # print "A test is already running"
                return
                
            if result == '':
                table.setValue(row, 'result', 'Running')

                models = ds.getValueAt(row, 'models')
                functionName = ds.getValueAt(row, 'function')
                description = ds.getValueAt(row, 'description')
                
                app.test.vfm.runner.run(rootContainer, table, models, functionName, description, row)
                return

    # If we get all of the way through, and there is nothing left to run, then stop the timer.
    timer = rootContainer.getComponent("Timer")
    timer.running = False
    
            
def run(rootContainer, table, models, functionName, description, row):
    import app, system, os
    import app.test.vfm.runner as module
    import app.test.common as common
    global fileRoot, params, sqlparams, dict
    global pyResults     

    project = system.util.getProjectName()    
    pyResults = {}
    
    path = rootContainer.getComponent("Path").text
    cadence = rootContainer.getComponent("Cadence").intValue

    # Convert models into a list
    models = models.split(',')

    if len(models) >= 1:
        modelId1 = models[0]
        print "Model #1: <%s>" % (modelId1)
        biasTag = '[]%s/Models/VFM%s/bias' % (project, modelId1)
        print "Bias tag: <%s>" % (biasTag)
        system.tag.write(biasTag, 0.0)
    else:
        modelId1 = -1

    system.tag.write('[]\FT\Control\Model1Id', int(modelId1))

    if len(models) >= 2:
        modelId2 = models[1]
        biasTag = '[]%s/Models/VFM%s/bias' % (project, modelId2)
        system.tag.write(biasTag, 0.0)
    else:
        modelId2 = -1
    system.tag.write('[]\FT\Control\Model2Id', int(modelId2))    

    func = getattr(module, functionName)
    
    # Write the key to a property of the window
    modelType = 'VFM'
    key = project
    rootContainer.setPropertyValue("key", key)    
    system.tag.write("[]/FT/Control/TestingStatus", description)
    
    # Initialize the database so we have a known starting point for the test
    common.initialize.initializeDatabase(modelId1)
    
    # Initialize the engine so we have a known starting point for the test
    common.initialize.initializeEngine()            

    # Configure the specific test - the function puts the test specific configuration into globals
    print "Running test #%i - %s" % (row + 1, description)
    func(key, models)

    # Send the model to the engine        
    common.engine.sendModelTestCase(params, sqlparams, key, dict, cadence, path, modelType, fileRoot)
    
    # Start playing the data file (There is a built in delay in the player to wait for half of the cadence before starting the data file
    print "Starting the data pump..."
    common.data.play(path, modelType, fileRoot, cadence)
    
    # Start the execution engine
    app.test.common.engine.startExecution(key, cadence)
    
    # Wait until the test completes and then compare the results
    common.analyze.compareResults(table, row, key, path, modelType, fileRoot)

# Test #1: Simple Alert
def test01(key, models):
    import app
    import app.test.vfm as vfm
    global fileRoot, params, sqlparams, dict
    
    modelId = models[0]
    fileRoot = 'simple-alert'

    # Define the output columns to extract from the results dictionary and write to the output file.
    params = "status,certainty,dcsAlarm,dcsAlarmSuppression,"

    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Create the dictionary
    dict = vfm.create.basic(key, modelId)