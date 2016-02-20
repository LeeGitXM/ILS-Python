'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties, deactivate): 
    from ils.sfc.gateway.util import getStepProperty, handleUnexpectedGatewayError
    from ils.sfc.gateway.api import getChartLogger
    from system.ils.sfc.common.Constants import RECIPE_LOCATION, WRITE_OUTPUT_CONFIG, \
    STEP_TIMESTAMP, STEP_TIME, TIMING, DOWNLOAD, VALUE, TAG_PATH, DOWNLOAD_STATUS
    from ils.sfc.common.constants import SLEEP_INCREMENT, WAITING_FOR_REPLY
    import system, time
    from java.util import Date, Calendar
    from ils.sfc.common.util import formatTime
    from ils.sfc.gateway.api import getIsolationMode
    from system.ils.sfc import getWriteOutputConfig
    from ils.sfc.gateway.downloads import handleTimer, getTimerStart, getElapsedMinutes
    from ils.sfc.gateway.recipe import RecipeData
    from ils.sfc.gateway.downloads import writeValue
    from ils.sfc.gateway.abstractSfcIO import AbstractSfcIO
    from system.ils.sfc import getProviderName
    
    # local constants that could be moved somewhere
    INITIALIZED="initialized"
    TIMER_RUNNING="timerRunning"
    IMMEDIATE_ROWS="immediateRows"
    TIMED_ROWS="timedRows"
    FINAL_ROWS="finalRows"
    DOWNLOAD_ROWS="downloadRows"
    
    complete = False
    stepScope = scopeContext.getStepScope()
    chartScope = scopeContext.getChartScope()
    isolationMode = getIsolationMode(chartScope)
    providerName = getProviderName(isolationMode)
        
    logger = getChartLogger(chartScope)
    logger.trace("In writeOutput.activate() (deactivate: %s)..." % (deactivate))
    
    # This does not initially exist in the step scope dictionary, so we will get a value of False
    initialized = stepScope.get(INITIALIZED, False)
    if deactivate:
        logger.trace("*** A deactivate has been detected ***")
        complete=True
        
    elif not initialized:
        stepScope[INITIALIZED]=True
        logger.info("Initializing a Write Output block")
        configJson = getStepProperty(stepProperties, WRITE_OUTPUT_CONFIG)
        config = getWriteOutputConfig(configJson)
        logger.trace("Block Configuration: %s" % (str(config)))
        outputRecipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION)
        logger.trace("Using recipe location: %s" % (outputRecipeLocation))

        # The timer is not running until someone starts it
        stepScope[TIMER_RUNNING]=False
    
        # filter out disabled rows:
        downloadRows = []
        numDisabledRows = 0
        for row in config.rows:
            row.outputRD = RecipeData(chartScope, stepScope, outputRecipeLocation, row.key)
            row.outputRD.set("setpointStatus", "")
            download = row.outputRD.get(DOWNLOAD)
            if download:
                downloadRows.append(row)
            else:
                ++numDisabledRows
                row.outputRD.set(DOWNLOAD_STATUS, "")
        
        # do the timer logic, if there are rows that need timing
        timerNeeded = False
        for row in downloadRows:
            row.timingMinutes = row.outputRD.get(TIMING)
            if row.timingMinutes > 0.:
                timerNeeded = True
    
        logger.trace("Timer is needed: %s" % (str(timerNeeded)))
                
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
            
            logger.trace("Tag: %s, Value: %s, Time: %s" % (str(row.tagPath), str(row.value), str(row.timingMinutes)))

            # classify the rows
            if row.timingMinutes == 0.:
                immediateRows.append(row)
                row.outputRD.set(DOWNLOAD_STATUS, "approaching")
            elif row.timingMinutes >= 1000.:
                finalRows.append(row)
                row.outputRD.set(DOWNLOAD_STATUS, "pending")
            else:
                timedRows.append(row)
                row.outputRD.set(DOWNLOAD_STATUS, "pending")
        
            # I have no idea what this does - maybe it is needed for PV monitoring??? (Pete)
            row.io = AbstractSfcIO.getIO(row.tagPath, isolationMode) 

        stepScope[IMMEDIATE_ROWS]=immediateRows
        stepScope[TIMED_ROWS]=timedRows
        stepScope[FINAL_ROWS]=finalRows
        stepScope[DOWNLOAD_ROWS]=downloadRows

        logger.trace("There are %i immediate rows" % (len(immediateRows)))
        logger.trace("There are %i timed rows" % (len(timedRows)))
        logger.trace("There are %i final rows" % (len(finalRows)))
        
        if len(immediateRows) == 0 and len(timedRows) == 0 and len(finalRows) == 0:
            complete = True
        else:
            handleTimer(chartScope, stepScope, stepProperties, logger)

    else:
        logger.trace("...performing write output work...")
        try:
            timerStart=getTimerStart(chartScope, stepScope, stepProperties)
            
            if timerStart == None:
                logger.trace("The timer has not been started")
            else:
                elapsedMinutes = getElapsedMinutes(timerStart)
                logger.trace("   the timer start is: %s, the elapsed time is: %.2f" % (str(timerStart), elapsedMinutes))    
                immediateRows=stepScope.get(IMMEDIATE_ROWS, [])
                timedRows=stepScope.get(TIMED_ROWS,[])
                finalRows=stepScope.get(FINAL_ROWS,[])
                downloadRows=stepScope.get(DOWNLOAD_ROWS,[])
                
                timerWasRunning=stepScope.get(TIMER_RUNNING, False)
                
                # Immediately after the timer starts running we need to calculate the absolute download times for each output.
                if not(timerWasRunning):
                    stepScope[TIMER_RUNNING]=True

                    # wait until the timer starts
                    logger.trace("   the timer just started at: %s" % (str(timerStart)))
                    
                    # This is a strange little initialization that is done to initialize final writes in the bizzare case where ALL of the writes are final
                    cal = Calendar.getInstance()
                    cal.setTime(timerStart)
                    absTiming = cal.getTime()
                    timestamp = system.db.dateFormat(absTiming, "dd-MMM-yy H:mm:ss a")

                    # Immediately after the timer starts running we need to calculate the absolute download time.            
                    for row in downloadRows:
                        row.written = False
                        
                        # write the absolute step timing back to recipe data
                        if row.timingMinutes >= 1000.0:
                            # Final writes
                            # Because the rows are ordered by the timing, it is safe to use the last timestamp...
                            row.outputRD.set(STEP_TIMESTAMP, timestamp)
                            # I don't want to propagate the magic 1000 value, so we use None
                            # to signal an event-driven step
                            row.outputRD.set(STEP_TIME, None)
                            
                        elif row.timingMinutes > 0 and row.timingMinutes < 1000.0:
                            # Timed writes
                            cal = Calendar.getInstance()
                            cal.setTime(timerStart)
                            cal.add(Calendar.SECOND, int(row.timingMinutes * 60))
                            absTiming = cal.getTime()
                            timestamp = system.db.dateFormat(absTiming, "dd-MMM-yy H:mm:ss a")
                            row.outputRD.set(STEP_TIMESTAMP, timestamp)
                            row.outputRD.set(STEP_TIME, absTiming)
                        
                        else:
                            # Immediate writes
                            cal = Calendar.getInstance()
                            cal.setTime(timerStart)
                            absTiming = cal.getTime()
                            timestamp = system.db.dateFormat(absTiming, "dd-MMM-yy H:mm:ss a")
                            row.outputRD.set(STEP_TIMESTAMP, timestamp)
                            row.outputRD.set(STEP_TIME, absTiming)

                    logger.trace("...performing immediate writes...")
                    for row in immediateRows:
#                        row.outputRD.set("setpointStatus", "downloading")
                        logger.trace("   writing a immediate write for step %s" % (row.key))
                        writeValue(chartScope, row, logger, providerName)
                     
                logger.trace("...checking timed writes...")
                writesPending = False
                if len(timedRows) > 0:                    
                    
                    for row in timedRows:
                        if not row.written:
                            # If the row hasn't been written and the elapsed time is greater than the requested time then write the output
                            logger.trace("   checking output step %s at %.2f" % (row.key, row.timingMinutes))

                            if elapsedMinutes >= row.timingMinutes:
                                logger.trace("      writing a timed write for step %s" % (row.key))
#                                row.outputRD.set("setpointStatus", "downloading")
                                writeValue(chartScope, row, logger, providerName)
                                row.written = True
                            else:
                                writesPending = True
                                if elapsedMinutes >= row.timingMinutes - 0.5:
                                    row.outputRD.set(DOWNLOAD_STATUS, "approaching")
            
                # If all of the timed writes have been written then do the final writes
                if not(writesPending):
                    logger.trace("...starting final writes...")
                    for row in finalRows:
                        logger.trace("   writing a final write for step %s" % (row.key))
                        absTiming = Date()
                        timestamp = system.db.dateFormat(absTiming, "dd-MMM-yy H:mm:ss a")
                        row.outputRD.set(STEP_TIMESTAMP, timestamp)
                        row.outputRD.set(STEP_TIME, absTiming)
#                        row.outputRD.set("setpointStatus", "downloading")
                        writeValue(chartScope, row, logger, providerName)
                    
                    # All of the timed writes have completed and the final writes have been made so signal that the block is done
                    complete = True
                    logger.info("Write output block finished all of its work!")
                    
            #Note: write confirmations are on a separate thread and will write the result
            # directly to recipe data
        except:
            handleUnexpectedGatewayError(chartScope, 'Unexpected error in writeOutput.py', logger)
        finally:
            # TODO: handle re-entrant logic; don't return True until really done
            pass

    logger.trace("leaving writeOutput.activate(), complete=%s..." % (str(complete)))    
        
    return complete