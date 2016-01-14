'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, step): 
    from ils.sfc.gateway.util import getStepProperty, handleUnexpectedGatewayError
    from ils.sfc.gateway.api import getChartLogger
    from system.ils.sfc.common.Constants import RECIPE_LOCATION, WRITE_OUTPUT_CONFIG, \
    STEP_TIMESTAMP, STEP_TIME, TIMING, DOWNLOAD, VALUE, TAG_PATH
    from ils.sfc.common.constants import SLEEP_INCREMENT
    import time
    from ils.sfc.common.util import getMinutesSince, formatTime
    from ils.sfc.gateway.api import getIsolationMode
    from ils.sfc.gateway.util import checkForCancelOrPause
    from system.ils.sfc import getWriteOutputConfig
    from ils.sfc.gateway.downloads import handleTimer, waitForTimerStart
    from ils.sfc.gateway.recipe import RecipeData
    from ils.sfc.gateway.downloads import writeValue
    from ils.sfc.gateway.abstractSfcIO import AbstractSfcIO
    from system.ils.sfc import getProviderName
    
    try:
        chartScope = scopeContext.getChartScope() 
        stepScope = scopeContext.getStepScope()
        stepProperties = step.getProperties();
        logger = getChartLogger(chartScope)
        logger.info("Executing a Write Output block")
        configJson = getStepProperty(stepProperties, WRITE_OUTPUT_CONFIG)
        config = getWriteOutputConfig(configJson)
        logger.trace("Block Configuration: %s" % (str(config)))
        outputRecipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION)
        logger.trace("Using recipe location: %s" % (outputRecipeLocation))
    
        # Everything will have the same tag provider - check isolation mode and get the provider
        isolationMode = getIsolationMode(chartScope)
        providerName = getProviderName(isolationMode)
        logger.trace("Isolation: %s - Provider: %s" % (str(isolationMode), providerName))
    
        # filter out disabled rows:
        downloadRows = []
        numDisabledRows = 0
        for row in config.rows:
            row.outputRD = RecipeData(chartScope, stepScope, outputRecipeLocation, row.key)
            download = row.outputRD.get(DOWNLOAD)
            print 'download:', download
            if download:
                downloadRows.append(row)
            else:
                ++numDisabledRows
        
        # do the timer logic, if there are rows that need timing
        timerNeeded = False
        for row in downloadRows:
            row.timingMinutes = row.outputRD.get(TIMING)
            if row.timingMinutes > 0.:
                timerNeeded = True
    
        logger.trace("Timer is needed: %s" % (str(timerNeeded)))
        
        if timerNeeded:
            handleTimer(chartScope, stepScope, stepProperties, logger)
            # wait until the timer starts
            logger.trace("Waiting for the timer to start...")
            timerStart = waitForTimerStart(chartScope, stepScope, stepProperties, logger)
            logger.trace("The timer start is: %s" % (str(timerStart)))
            
            if timerStart == None:
                logger.info("The chart has been canceled")
                return
                
        # separate rows into timed rows and those that are written after timed rows:
        immediateRows = []
        timedRows = []
        finalRows = []
                 
        # initialize row data and separate into immediate/timed/final:
        logger.trace("Initializing data and classifying outputs...")
        logger.trace("There are %i total rows; %i to download and %i  disabled" % (len(config.rows), len(downloadRows), numDisabledRows))
        for row in downloadRows:
            row.written = False
    
            # cache some frequently used values from recipe data:
            row.value = row.outputRD.get(VALUE)
            row.tagPath = row.outputRD.get(TAG_PATH)
                
            # classify the rows
            timingIsEventDriven = False
            if row.timingMinutes == 0.:
                immediateRows.append(row)
            elif row.timingMinutes >= 1000.:
                finalRows.append(row)
                timingIsEventDriven = True
            else:
                timedRows.append(row)
      
            # write the absolute step timing back to recipe data
            if timingIsEventDriven:
                row.outputRD.set(STEP_TIMESTAMP, '')
                # I don't want to propagate the magic 1000 value, so we use None
                # to signal an event-driven step
                row.outputRD.set(STEP_TIME, None)
            elif timerNeeded:
                absTiming = timerStart + row.timingMinutes * 60.
                timestamp = formatTime(absTiming)
                row.outputRD.set(STEP_TIMESTAMP, timestamp)
                row.outputRD.set(STEP_TIME, absTiming)
            # ?? do we need a timestamp for immediate rows?
            
            # I have no idea what this does - maybe it is needed for PV monitoring??? (Pete)
            row.io = AbstractSfcIO.getIO(row.tagPath, isolationMode) 
              
        logger.trace("There are %i immediate rows" % (len(immediateRows)))
        logger.trace("There are %i timed rows" % (len(timedRows)))
        logger.trace("There are %i final rows" % (len(finalRows)))
        
        logger.trace("Starting immediate writes")
        for row in immediateRows:
            writeValue(chartScope, row, logger, providerName)
                 
        logger.trace("Starting timed writes")
        if len(timedRows) > 0:
            writesPending = True
        else:
            writesPending = False
                 
        while writesPending:
            writesPending = False 
            
            elapsedMinutes = getMinutesSince(timerStart)
            for row in timedRows:
                if not row.written:
                    writesPending = True
                    logger.trace("checking output step %s; %.2f elapsed %.2f" % (row.key, row.timingMinutes, elapsedMinutes))
                    if elapsedMinutes >= row.timingMinutes:
                        writeValue(chartScope, row, logger, providerName)
                        row.written = True
    
            if writesPending:
                time.sleep(SLEEP_INCREMENT)
     
            if checkForCancelOrPause(chartScope, logger):
                logger.trace("Aborting the write output because the chart has been cancelled")
                return
    
        logger.trace("Starting final writes")
        for row in finalRows:
            logger.trace("In steps.writeOutput - Writing a final write for step %s" % (row.key))
            absTiming = time.time()
            timestamp = formatTime(absTiming)
            row.outputRD.set(STEP_TIMESTAMP, timestamp)
            row.outputRD.set(STEP_TIME, absTiming)
            writeValue(chartScope, row, logger, providerName)
    
        logger.info("Write output block finished!")
        #Note: write confirmations are on a separate thread and will write the result
        # directly to recipe data
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in writeOutput.py', logger)