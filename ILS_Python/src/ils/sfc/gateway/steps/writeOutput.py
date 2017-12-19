'''
Created on Dec 17, 2015

@author: rforbes
'''

from ils.sfc.recipeData.api import s88Get, s88Set
from ils.sfc.gateway.api import getChartLogger, handleUnexpectedGatewayError, getStepProperty, getTopChartRunId
from ils.sfc.common.constants import TIMER_SET, TIMER_KEY, TIMER_LOCATION, \
    START_TIMER, PAUSE_TIMER, RESUME_TIMER, STEP_NAME, \
    STEP_SUCCESS, STEP_FAILURE, DOWNLOAD, OUTPUT_VALUE, TAG, RECIPE_LOCATION, WRITE_OUTPUT_CONFIG, ACTUAL_DATETIME, ACTUAL_TIMING, TIMING, DOWNLOAD_STATUS, WRITE_CONFIRMED, \
    ERROR_COUNT_LOCAL, ERROR_COUNT_SCOPE, ERROR_COUNT_MODE, ERROR_COUNT_KEY, \
    DEACTIVATED, PAUSED, RESUMED, \
    LOCAL_SCOPE, PRIOR_SCOPE, SUPERIOR_SCOPE, PHASE_SCOPE, OPERATION_SCOPE, GLOBAL_SCOPE, CHART_SCOPE, STEP_SCOPE, COUNT_ABSOLUTE
import system
from java.util import Date, Calendar
from ils.sfc.gateway.api import getIsolationMode
from system.ils.sfc import getWriteOutputConfig
from ils.sfc.gateway.downloads import handleTimer
from ils.sfc.gateway.downloads import writeValue
from system.ils.sfc import getProviderName

# local constants that could be moved somewhere
INITIALIZED="initialized"
TIMER_RUNNING="timerRunning"
IMMEDIATE_ROWS="immediateRows"
TIMED_ROWS="timedRows"
FINAL_ROWS="finalRows"
DOWNLOAD_ROWS="downloadRows"
TIMER_NEEDED="timerNeeded"

def activate(scopeContext, stepProperties, state): 
    writeComplete = False
    writeConfirmComplete = False
    stepScope = scopeContext.getStepScope()
    chartScope = scopeContext.getChartScope()
    runId = getTopChartRunId(chartScope)
    isolationMode = getIsolationMode(chartScope)
    providerName = getProviderName(isolationMode)
    timerLocation = getStepProperty(stepProperties, TIMER_LOCATION) 
    timerKey = getStepProperty(stepProperties, TIMER_KEY)
    recipeDataScope = getStepProperty(stepProperties, RECIPE_LOCATION)
    stepName = getStepProperty(stepProperties, STEP_NAME)

    logger = getChartLogger(chartScope)
    logger.trace("In writeOutput.activate() (state: %s)..." % (state))
    
    # This does not initially exist in the step scope dictionary, so we will get a value of False
    initialized = stepScope.get(INITIALIZED, False)
    if state == DEACTIVATED:
        logger.trace("*** A deactivate has been detected ***")
        writeComplete=True
        writeConfirmComplete = True
    elif state == PAUSED:
        logger.trace("The writeOutput was paused")
        handleTimer(chartScope, stepScope, stepProperties, timerKey, timerLocation, PAUSE_TIMER, logger)
    elif state == RESUMED:
        logger.trace("The writeOutput was paused")
        handleTimer(chartScope, stepScope, stepProperties, timerKey, timerLocation, RESUME_TIMER, logger)
    elif not initialized:
        stepScope[INITIALIZED]=True
        stepScope[ERROR_COUNT_LOCAL] = 0
        logger.infof("Initializing Write Output block %s", stepName)
        configJson = getStepProperty(stepProperties, WRITE_OUTPUT_CONFIG)
        config = getWriteOutputConfig(configJson)
        logger.trace("Block Configuration: %s" % (str(config)))

        # The timer is not running until someone starts it
        stepScope[TIMER_RUNNING]=False

        # filter out disabled rows:
        downloadRows = []
        numDisabledRows = 0
        for row in config.rows:
            download = s88Get(chartScope, stepScope, row.key + "." + DOWNLOAD, recipeDataScope)
            if download:
                downloadRows.append(row)
            else:
                print row.key, " is disabled"
                numDisabledRows = numDisabledRows + 1
                s88Set(chartScope, stepScope, row.key + "." + DOWNLOAD_STATUS, "", recipeDataScope)
        
        # do the timer logic, if there are rows that need timing
        timerNeeded = False
        for row in downloadRows:
            row.timingMinutes = s88Get(chartScope, stepScope, row.key + "." + TIMING, recipeDataScope)
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
            row.value = s88Get(chartScope, stepScope, row.key + "." + OUTPUT_VALUE, recipeDataScope)
            row.tagPath = s88Get(chartScope, stepScope, row.key + "." + TAG, recipeDataScope)
            
            logger.trace("Tag: %s, Value: %s, Time: %s" % (str(row.tagPath), str(row.value), str(row.timingMinutes)))

            # classify the rows
            if row.timingMinutes == 0.:
                immediateRows.append(row)
                s88Set(chartScope, stepScope, row.key + "." + DOWNLOAD_STATUS, "approaching", recipeDataScope)
            elif row.timingMinutes >= 1000.:
                finalRows.append(row)
                s88Set(chartScope, stepScope, row.key + "." + DOWNLOAD_STATUS, "pending", recipeDataScope)
            else:
                timedRows.append(row)
                s88Set(chartScope, stepScope, row.key + "." + DOWNLOAD_STATUS, "pending", recipeDataScope)

        stepScope[IMMEDIATE_ROWS]=immediateRows
        stepScope[TIMED_ROWS]=timedRows
        stepScope[FINAL_ROWS]=finalRows
        stepScope[DOWNLOAD_ROWS]=downloadRows
        stepScope[TIMER_NEEDED]=timerNeeded

        logger.trace("There are %i immediate rows" % (len(immediateRows)))
        logger.trace("There are %i timed rows" % (len(timedRows)))
        logger.trace("There are %i final rows" % (len(finalRows)))
        
        if len(immediateRows) == 0 and len(timedRows) == 0 and len(finalRows) == 0:
            writeComplete = True
            writeConfirmComplete = True
        if timerNeeded  and getStepProperty(stepProperties, TIMER_SET):
            handleTimer(chartScope, stepScope, stepProperties, timerKey, timerLocation, START_TIMER, logger)

    else:
        logger.trace("...performing write output work...")
        try:
            timerNeeded=stepScope[TIMER_NEEDED]
            downloadRows=stepScope.get(DOWNLOAD_ROWS,[])
            
            if timerNeeded:
                # Monitor for the specified period, possibly extended by persistence time
                # It is possible that this block starts before some other block starts the timer
                elapsedMinutes=s88Get(chartScope, stepScope, timerKey + ".elapsedMinutes", timerLocation)
                
                if elapsedMinutes <= 0.0:
                    logger.trace("The timer has not been started")
                else:
                    logger.trace("   the elapsed time is: %.2f" % (elapsedMinutes))    
                    immediateRows=stepScope.get(IMMEDIATE_ROWS, [])
                    timedRows=stepScope.get(TIMED_ROWS,[])
                    finalRows=stepScope.get(FINAL_ROWS,[])
                    timerWasRunning=stepScope.get(TIMER_RUNNING, False)
                    
                    # Immediately after the timer starts running we need to calculate the absolute download times for each output.
                    if not(timerWasRunning):
                        stepScope[TIMER_RUNNING]=True
    
                        # wait until the timer starts
                        logger.trace("   the timer just started... ")
                        
                        # This is a strange little initialization that is done to initialize final writes in the bizzare 
                        # case where ALL of the writes are final
                        timerStart=s88Get(chartScope, stepScope, timerKey + ".StartTime", timerLocation)
                        cal = Calendar.getInstance()
                        cal.setTime(timerStart)
                        absTiming = cal.getTime()
                        timestamp = system.db.dateFormat(absTiming, "dd-MMM-yy h:mm:ss a")
    
                        # Immediately after the timer starts running we need to calculate the absolute download time.            
                        for row in downloadRows:
                            row.written = False
                            
                            # write the absolute step timing back to recipe data
                            if row.timingMinutes >= 1000.0:
                                # Final writes
                                # Because the rows are ordered by the timing, it is safe to use the last timestamp...
                                s88Set(chartScope, stepScope, row.key + "." + ACTUAL_DATETIME, timestamp, recipeDataScope)
                                # I don't want to propagate the magic 1000 value, so we use None
                                # to signal an event-driven step
                                s88Set(chartScope, stepScope, row.key + "." + ACTUAL_TIMING, elapsedMinutes, recipeDataScope)
                                
                            elif row.timingMinutes > 0 and row.timingMinutes < 1000.0:
                                # Timed writes
                                cal = Calendar.getInstance()
                                cal.setTime(timerStart)
                                cal.add(Calendar.SECOND, int(row.timingMinutes * 60))
                                absTiming = cal.getTime()
                                timestamp = system.db.dateFormat(absTiming, "dd-MMM-yy h:mm:ss a")
                                s88Set(chartScope, stepScope, row.key + "." + ACTUAL_DATETIME, timestamp, recipeDataScope)
                                s88Set(chartScope, stepScope, row.key + "." + ACTUAL_TIMING, elapsedMinutes, recipeDataScope)
                            
                            else:
                                # Immediate writes
                                cal = Calendar.getInstance()
                                cal.setTime(timerStart)
                                absTiming = cal.getTime()
                                timestamp = system.db.dateFormat(absTiming, "dd-MMM-yy h:mm:ss a")
                                s88Set(chartScope, stepScope, row.key + "." + ACTUAL_DATETIME, timestamp, recipeDataScope)
                                s88Set(chartScope, stepScope, row.key + "." + ACTUAL_TIMING, elapsedMinutes, recipeDataScope)
    
                        logger.trace("...performing immediate writes...")
                        for row in immediateRows:
                            logger.trace("   writing a immediate write for step %s" % (row.key))
                            writeValue(chartScope, stepScope, row, logger, providerName, recipeDataScope)
                         
                    logger.trace("...checking timed writes...")
                    writesPending = False
                    if len(timedRows) > 0:                    
                        
                        for row in timedRows:
                            if not row.written:
                                # If the row hasn't been written and the elapsed time is greater than the requested time then write the output
                                logger.trace("   checking output step %s at %.2f" % (row.key, row.timingMinutes))
    
                                if elapsedMinutes >= row.timingMinutes:
                                    logger.trace("      writing a timed write for step %s" % (row.key))
                                    writeValue(chartScope, stepScope, row, logger, providerName, recipeDataScope)
                                    row.written = True
                                else:
                                    writesPending = True
                                    if elapsedMinutes >= row.timingMinutes - 0.5:
                                        s88Set(chartScope, stepScope, row.key + "." + DOWNLOAD_STATUS, "approaching", recipeDataScope)
                
                    # If all of the timed writes have been written then do the final writes
                    if not(writesPending):
                        logger.trace("...starting final writes...")
                        for row in finalRows:
                            if s88Get(chartScope, stepScope, row.key + "." + DOWNLOAD_STATUS, recipeDataScope) == "pending":
                                logger.trace("   writing a final write for step %s" % (row.key))
                                absTiming = Date()
                                timestamp = system.db.dateFormat(absTiming, "dd-MMM-yy h:mm:ss a")
                                s88Set(chartScope, stepScope, row.key + "." + ACTUAL_DATETIME, timestamp, recipeDataScope)
                                s88Set(chartScope, stepScope, row.key + "." + ACTUAL_TIMING, elapsedMinutes, recipeDataScope)
                                writeValue(chartScope, stepScope, row, logger, providerName, recipeDataScope)
                        
                        # All of the timed writes have completed and the final writes have been made so signal that the block is done
                        writeComplete = True
                        logger.trace("...Write output block finished all of its writes!")
                        
                #Note: write confirmations are on a separate thread and will write the result
                # directly to recipe data
            
            else:
                # There are no timed writes - everything should be immediate
                # Immediately after the timer starts running we need to calculate the absolute download time. 
                # Even when all of the rows are immediate, we will call the activate several times as we await confirmation of the writes.  To make sure that we only
                # attempt to write values once, remove them from the list to download once they have been written.           
                logger.trace("The timer is not needed, performing immediate writes.")
                elapsedMinutes = 0.0
                immediateRows=stepScope.get(IMMEDIATE_ROWS, [])
                absTiming = system.date.now()
                timestamp = system.db.dateFormat(absTiming, "dd-MMM-yy h:mm:ss a")

                for row in immediateRows:
                    s88Set(chartScope, stepScope, row.key + "." + ACTUAL_DATETIME, timestamp, recipeDataScope)
                    s88Set(chartScope, stepScope, row.key + "." + ACTUAL_TIMING, elapsedMinutes, recipeDataScope)

                    logger.trace("   writing an immediate write for step %s" % (row.key))
                    writeValue(chartScope, stepScope, row, logger, providerName, recipeDataScope)
                    immediateRows.remove(row)

                writeComplete = True
                stepScope[IMMEDIATE_ROWS]=immediateRows
                              
                logger.trace("Write output block finished all of its work, which was purely immediate!")
                
                #Note: write confirmations are on a separate thread and will write the result
                
        except:
            handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in writeOutput.py', logger)
        finally:
            # TODO: handle re-entrant logic; don't return True until really done
            pass

    if writeComplete and not(writeConfirmComplete):
        logger.trace("The writes are all complete, check if the confirmations are complete...")
        writeConfirmComplete = True
        for row in downloadRows:
            downloadStatus = s88Get(chartScope, stepScope, row.key + "." + DOWNLOAD_STATUS, recipeDataScope)
            writeConfirmed = s88Get(chartScope, stepScope, row.key + "." + WRITE_CONFIRMED, recipeDataScope)
            logger.tracef( "Tag: %s", row.tagPath)
            logger.tracef( "          written: %s", str(row.written))
            logger.tracef( "  download status: %s", downloadStatus)
            logger.tracef( "  write confirmed: %s", writeConfirmed)
            if downloadStatus not in [STEP_SUCCESS, STEP_FAILURE]:
                writeConfirmComplete = False
                
        if writeConfirmComplete == False:
            logger.tracef("Found at least one output that still needs to be confirmed.")
        
    logger.trace("leaving writeOutput.activate(), writeComplete=%s, writeConfirmComplete=%s... " % (str(writeComplete), str(writeConfirmComplete)))    
    workDone = False
    if writeComplete and writeConfirmComplete:
        logger.infof("Write output step %s is complete!", stepName)
        localErrorCount = stepScope[ERROR_COUNT_LOCAL]
        
        errorCountScope = getStepProperty(stepProperties, ERROR_COUNT_SCOPE)
        errorCountKey = getStepProperty(stepProperties, ERROR_COUNT_KEY)
        errorCountMode = getStepProperty(stepProperties, ERROR_COUNT_MODE)
        
        if errorCountScope == CHART_SCOPE:
            logger.infof("Setting a chart scope error counter, %d local errors were found...", localErrorCount)
            if errorCountMode == COUNT_ABSOLUTE:
                chartScope[errorCountKey] = localErrorCount
            else:
                cnt = chartScope[errorCountKey]
                chartScope[errorCountKey] = cnt + localErrorCount
        
        elif errorCountScope == STEP_SCOPE:
            ''' For stepScope counters the mode is implicitly incremental because the data is transient '''
            logger.infof("Setting a step scope error counter, %d local errors were found...", localErrorCount)
            stepScope[errorCountKey] = localErrorCount
        
        elif errorCountScope in [LOCAL_SCOPE, PRIOR_SCOPE, SUPERIOR_SCOPE, PHASE_SCOPE, OPERATION_SCOPE, GLOBAL_SCOPE]:
            logger.infof("Setting a recipe error counter (%s.%s), %d local errors were found...", errorCountScope, errorCountKey, localErrorCount)
            if errorCountMode == COUNT_ABSOLUTE:
                s88Set(chartScope, stepScope, errorCountKey + ".Value", localErrorCount, errorCountScope)
            else:
                cnt = s88Get(chartScope, stepScope, errorCountKey + ".Value", errorCountScope)
                s88Set(chartScope, stepScope, errorCountKey + ".Value", localErrorCount + cnt, errorCountScope)
                
        workDone = True
        
        ''' Set up the step for the next time it is called if this is in a loop '''
        stepScope[INITIALIZED]=False
    
    return workDone