'''

Helper methods for I/O steps (WriteOutput, Monitor PV, Monitor Downloads) that 
do not directly involve client interaction

Created on Jun 18, 2015
@author: rforbes
'''

import system, time
from java.util import Date, Calendar
from system.ils.sfc.common.Constants import DEACTIVATED, ACTIVATED, PAUSED, CANCELLED, RESUMED, TAG_PATH, \
    TIMER_STATE, TIMER_STATE_CANCEL, TIMER_STATE_CLEAR, TIMER_STATE_PAUSE, TIMER_STATE_RESUME, TIMER_STATE_RUN, TIMER_STATE_STOP, \
    TIMER_LOCATION, TIMER_KEY, TIMER_SET, TIMER_CLEAR, TIMER_RUN_MINUTES, TIMER_START_TIME

'''
These methods make the timer UDT work.  They are called by a tag change script on the UDT or by a scripting function on the UDT
'''
def handleTimerCommand(tagPath, previousValue, currentValue, initialChange, missedEvents):
    val = currentValue.value
    print "Handling a change in command for: ", tagPath
    parentPath = tagPath[:tagPath.rfind("/")]
    print "The parent path is <%s>" % (parentPath)
    if val == TIMER_STATE_CLEAR:
        print "Clear the run time"
        system.tag.write(parentPath + "/runTime", 0.0)
    elif val == TIMER_STATE_RUN:
        print "Set the start time"
        startTime = Date().getTime()
        system.tag.write(parentPath + "/startTime", startTime)
    elif val == TIMER_STATE_PAUSE:
        print "PAUSE"
    elif val == TIMER_STATE_RESUME:
        print "resume"
    elif val in [TIMER_STATE_STOP, TIMER_STATE_CANCEL]:
        print "stop or cancel"
    else:
        print "Unsupported command: ", currentValue

# This is generally called every second, but it doesn't matter, it will calculate the elapsed time, in minutes since it was last called.
def updateTimer(tagPath, previousValue, currentValue, initialChange, missedEvents):
    parentPath = tagPath[:tagPath.rfind("/")]
    qvs=system.tag.readAll([parentPath + "/state", parentPath + "/runTime"])
    state = qvs[0]
        
    # If the timer is running then update the runtime by calculating the elapsed time since it was last updated or it started running.
    # If the current state is resume, then the last state must have been paused.
    if state.value in [TIMER_STATE_RUN, TIMER_STATE_RESUME]:
        runtime = qvs[1]
        now = Date().getTime()

        if state.timestamp > runtime.timestamp:
#                print "The state was most recently changed"
            elapsedMs = now - state.timestamp.getTime()
        else:
#                print "The runtime was most recently changed" 
            elapsedMs = now - runtime.timestamp.getTime()
#            print "The elapsed seconds is: ", str(elapsedMs / 1000.0)
        system.tag.write(parentPath + "/runTime", runtime.value + elapsedMs / 1000.0 / 60.0)

'''
These methods are called by steps that use a timer.  This is designed so that any step that is using a timer 
can pause it.  It does not have to be the step that was designated to set (start) or clear the timer, those 
steps may have finished.  Since individual steps cannot be paused, this should work.
'''
def pauseTimer(chartScope, stepScope, stepProperties, logger):
    from ils.sfc.gateway.util import getStepProperty
    from ils.sfc.gateway.recipe import RecipeData, splitKey
        
    timerLocation = getStepProperty(stepProperties, TIMER_LOCATION) 
    timerKeyAndAttribute = getStepProperty(stepProperties, TIMER_KEY)
    timerKey, timerAttribute = splitKey(timerKeyAndAttribute)
    timer = RecipeData(chartScope, stepScope, timerLocation, timerKey)
    timerState = timer.get(TIMER_STATE)
    print "The Timer state is: ", timerState
    if timerState <> TIMER_STATE_PAUSE:
        logger.info("Pausing the download timer...")
        timer.set(TIMER_STATE, TIMER_STATE_PAUSE)

def resumeTimer(chartScope, stepScope, stepProperties, logger):
    from ils.sfc.gateway.util import getStepProperty
    from ils.sfc.gateway.recipe import RecipeData, splitKey
    
    timerLocation = getStepProperty(stepProperties, TIMER_LOCATION) 
    timerKeyAndAttribute = getStepProperty(stepProperties, TIMER_KEY)
    timerKey, timerAttribute = splitKey(timerKeyAndAttribute)
    timer = RecipeData(chartScope, stepScope, timerLocation, timerKey)
    timerState = timer.get(TIMER_STATE)
    print "The Timer state is: ", timerState
    if timerState <> TIMER_STATE_RESUME:
        logger.info("Resuming the download timer...")
        timer.set(TIMER_STATE, TIMER_STATE_RESUME)

def handleTimer(chartScope, stepScope, stepProperties, logger):
    '''perform the timer-related logic for a step'''
    from ils.sfc.gateway.util import getStepProperty
    from ils.sfc.gateway.recipe import RecipeData, splitKey
    
    timerLocation = getStepProperty(stepProperties, TIMER_LOCATION) 
    timerKeyAndAttribute = getStepProperty(stepProperties, TIMER_KEY)
    logger.trace("The timer key and attribute are: %s" % (timerKeyAndAttribute))
#    print "The step properties are: ", stepProperties
    timerKey, timerAttribute = splitKey(timerKeyAndAttribute)
    timer = RecipeData(chartScope, stepScope, timerLocation, timerKey)

    # Note: there may be no timer-clear property, in which case the
    # value is null which 
    clearTimer = getStepProperty(stepProperties, TIMER_CLEAR)
    if clearTimer:
        logger.info("Clearing the download timer...")
        timer.set(TIMER_STATE, TIMER_STATE_CLEAR)

    setTimer = getStepProperty(stepProperties, TIMER_SET)
    if setTimer:
        logger.info("Starting the download timer...")
        print "Clearing..."
        timer.set(TIMER_STATE, TIMER_STATE_CLEAR)
        time.sleep(0.5)
        print "Running..."
        timer.set(TIMER_STATE, TIMER_STATE_RUN)

    return timer, timerAttribute

# Get the timer run time in minutes
def getRunMinutes(chartScope, stepScope, stepProperties):
    from ils.sfc.gateway.recipe import RecipeData, splitKey
    from ils.sfc.gateway.util import getStepProperty
    
    timerLocation = getStepProperty(stepProperties, TIMER_LOCATION) 
    timerKeyAndAttribute = getStepProperty(stepProperties, TIMER_KEY)
    timerKey, timerAttribute = splitKey(timerKeyAndAttribute)
    timer = RecipeData(chartScope, stepScope, timerLocation, timerKey)
    
    runMinutes = timer.get(TIMER_RUN_MINUTES)
    
    return runMinutes

# Get the start time for a timer (will be None if cleared but not set)
# The timer start time is read from a date time tag (recipe data)
def getTimerStart(chartScope, stepScope, stepProperties):
    from ils.sfc.gateway.recipe import RecipeData, splitKey
    from ils.sfc.gateway.util import getStepProperty
    
    timerLocation = getStepProperty(stepProperties, TIMER_LOCATION) 
    timerKeyAndAttribute = getStepProperty(stepProperties, TIMER_KEY)
    timerKey, timerAttribute = splitKey(timerKeyAndAttribute)
    timer = RecipeData(chartScope, stepScope, timerLocation, timerKey)
    startTime = timer.get(TIMER_START_TIME)
    return startTime

# This returns the elapsed time in minutes from the given Java time (milliseconds sine the epoch)
def getElapsedMinutes(startTime):
    from java.util import Date
    now=Date()
    elapsedMinutes = (now.getTime() - startTime.getTime()) / 1000.0 / 60.0
    return elapsedMinutes

def waitForTimerStart(chartScope, stepScope, stepProperties, logger):
    '''Wait until the i/o timer shows a non-null value'''
    from ils.sfc.common.constants import CANCEL, PAUSE, SLEEP_INCREMENT
    from ils.sfc.gateway.util import checkForCancelOrPause
    import time
    timerStart = getTimerStart(chartScope, stepScope, stepProperties)
    while timerStart == None:
        # print 'waiting for timer start'
        # Handle Cancel/Pause, as this loop has sleeps
        chartStatus = checkForCancelOrPause(stepScope, logger)
        if chartStatus == CANCEL:
            return None
        elif chartStatus == PAUSE:
            continue
        
        time.sleep(SLEEP_INCREMENT)
        timerStart = getTimerStart(chartScope, stepScope, stepProperties)
    return timerStart

#
# Modified this to use WriteDatum from the IO layer which automatically does a Write Confirm...
def writeValue(chartScope, config, logger, providerName):
    '''write an output value'''
    
    #----------------------------------------------------------------------------------------------------
    def _writeValue(chartScope=chartScope, config=config, logger=logger, providerName=providerName):
        from ils.io.api import write
        from ils.sfc.gateway.util import queueMessage
        from ils.sfc.common.constants import MSG_STATUS_INFO
        from ils.sfc.common.constants import STEP_DOWNLOADING, STEP_SUCCESS, STEP_FAILURE
        from system.ils.sfc.common.Constants import  DOWNLOAD_STATUS, PENDING, OUTPUT_TYPE, SETPOINT,  WRITE_CONFIRMED, SUCCESS, FAILURE
    
        tagPath = "[%s]%s" % (providerName, config.tagPath)
        outputType = config.outputRD.get(OUTPUT_TYPE)
        logger.info("writing %s to %s - attribute %s (confirm: %s)" % (config.value, tagPath, outputType,str(config.confirmWrite)))
        
        logger.trace("---- setting status to downloading ----")
        config.outputRD.set(DOWNLOAD_STATUS, STEP_DOWNLOADING)
        writeStatus, txt = write(tagPath, config.value, config.confirmWrite, outputType)
        logger.trace("WriteDatum returned: %s - %s" % (str(writeStatus), txt))
        config.written = True
    
        if config.confirmWrite:
            config.outputRD.set(WRITE_CONFIRMED, writeStatus)
    
        if writeStatus:
            logger.trace("---- setting status to SUCCESS ----")
            config.outputRD.set(DOWNLOAD_STATUS, STEP_SUCCESS)
        else:
            logger.trace("---- setting status to FAILURE ----")
            config.outputRD.set(DOWNLOAD_STATUS, STEP_FAILURE)
    
        queueMessage(chartScope, 'tag ' + config.tagPath + " written; value: " + str(config.value) + txt, MSG_STATUS_INFO)
    #----------------------------------------------------------------------------------------------------
    system.util.invokeAsynchronous(_writeValue)


def confirmWrite(chartScope, config, logger):
    '''confirms the write on a separate thread and writes the result back to recipe data'''
    import threading
    def worker(chartScope, config, logger):
        from system.ils.sfc.common.Constants import WRITE_CONFIRMED, DOWNLOAD_STATUS, SUCCESS, FAILURE
        # ordinarily, exceptions are automatically caught in PythonCall but that
        # doesn't work for threads so we need to have a local handler:
        from ils.sfc.gateway.util import handleUnexpectedGatewayError
        import sys
        try:
            actualValue = config.io.getSetpoint()
            writeConfirmed = (actualValue == config.value)
            config.outputRD.set(WRITE_CONFIRMED, writeConfirmed)
            config.outputRD.set(DOWNLOAD_STATUS, SUCCESS)
        except:
            # note that Java exceptions are not caught by "except Exception", so this
            # way is more complete:
            e = sys.exc_info()[1]
            msg = "Error confirming write: " + str(e)
            handleUnexpectedGatewayError(chartScope, msg, logger)
            config.outputRD.set(DOWNLOAD_STATUS, FAILURE)
    t = threading.Thread(target=worker, args=(chartScope, config, logger,))
    t.start()

