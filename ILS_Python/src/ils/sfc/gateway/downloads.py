'''

Helper methods for I/O steps (WriteOutput, Monitor PV, Monitor Downloads) that 
do not directly involve client interaction

Created on Jun 18, 2015
@author: rforbes
'''

import system

def handleTimer(chartScope, stepScope, stepProperties, logger):
    '''perform the timer-related logic for a step'''
    from ils.sfc.gateway.api import s88Set, s88Get
    from ils.sfc.gateway.util import getStepProperty
    from ils.sfc.gateway.recipe import getSiblingKey
    from system.ils.sfc.common.Constants import TIMER_LOCATION, TIMER_KEY, TIMER_SET, TIMER_CLEAR, DATA_ID
    import time
    from ils.sfc.gateway.recipe import RecipeData, splitKey
    
    timerLocation = getStepProperty(stepProperties, TIMER_LOCATION) 
    timerKeyAndAttribute = getStepProperty(stepProperties, TIMER_KEY)
    print "The timer key and attribute is: ", timerKeyAndAttribute
    print "The step properties are: ", stepProperties
    timerKey, timerAttribute = splitKey(timerKeyAndAttribute)
    timer = RecipeData(chartScope, stepScope, timerLocation, timerKey)
    # Note: there may be no timer-clear property, in which case the
    # value is null which 
    clearTimer = getStepProperty(stepProperties, TIMER_CLEAR)
    if clearTimer:
        logger.info("Clearing the download timer...")
        timer.set(timerAttribute, None)
        
    setTimer = getStepProperty(stepProperties, TIMER_SET)
    if setTimer:
        # print 'starting timer'
        logger.info("Setting the download timer...")
        startTime = time.time()
        timer.set(timerAttribute, startTime)

    return timer, timerAttribute

def getTimerStart(chartScope, stepScope, stepProperties):
    '''get the start time for a timer (will be None if cleared but not set)'''
    from ils.sfc.gateway.util import getStepProperty, handleUnexpectedGatewayError
    from ils.sfc.gateway.api import s88Get
    from system.ils.sfc.common.Constants import TIMER_LOCATION, TIMER_KEY
    from ils.sfc.gateway.api import getTopChartStartTime
    timerLocation = getStepProperty(stepProperties, TIMER_LOCATION)
    timerKey = getStepProperty(stepProperties, TIMER_KEY)
    timerStart = s88Get(chartScope, stepScope, timerKey, timerLocation)
    # print 'getting timer start'
    # do a sanity check on the timer start:
    topChartStartTime = getTopChartStartTime(chartScope)
    if timerStart != None and timerStart < topChartStartTime:
        handleUnexpectedGatewayError(chartScope, "download timer read before set or cleared; stale value")
    
    return timerStart

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
        from system.ils.sfc.common.Constants import  DOWNLOAD_STATUS, PENDING, VALUE_TYPE, SETPOINT,  WRITE_CONFIRMED, SUCCESS, FAILURE
    
        tagPath = "[%s]%s" % (providerName, config.tagPath)
        valueType = config.outputRD.get(VALUE_TYPE)
        logger.info("writing %s to %s - attribute %s (confirm: %s)" % (config.value, tagPath, valueType,str(config.confirmWrite)))
        
        config.outputRD.set(DOWNLOAD_STATUS, STEP_DOWNLOADING)
        writeStatus, txt = write(tagPath, config.value, config.confirmWrite, valueType)
        logger.trace("WriteDatum returned: %s - %s" % (str(writeStatus), txt))
        config.written = True
    
        if config.confirmWrite:
            config.outputRD.set(WRITE_CONFIRMED, writeStatus)
    
        if writeStatus:
            config.outputRD.set(DOWNLOAD_STATUS, STEP_SUCCESS)
        else:
            config.outputRD.set(DOWNLOAD_STATUS, STEP_FAILURE)
    
        queueMessage(chartScope, 'tag ' + config.tagPath + " written; value: " + str(config.value) + txt, MSG_STATUS_INFO)
    #----------------------------------------------------------------------------------------------------
    system.util.invokeAsynchronous(_writeValue)


def writeOutputOriginal(chartScope, config, verbose, logger):
    '''write an output value'''
    from ils.sfc.gateway.util import queueMessage
    from ils.sfc.common.constants import MSG_STATUS_INFO
    from system.ils.sfc.common.Constants import  DOWNLOAD_STATUS, PENDING, VALUE_TYPE, SETPOINT

    logger.trace("writing %s to %s" % (config.value, config.tagPath))
    print "Config: ", config
    valueType = config.outputRD.get(VALUE_TYPE)
    if valueType == SETPOINT:
        config.io.setSetpoint(config.value)
    else:
        config.io.setCurrentValue(config.value)
    config.written = True
    if config.confirmWrite:
        config.outputRD.set(DOWNLOAD_STATUS, PENDING)
        confirmWrite(chartScope, config, logger)
    else:
        config.outputRD.set(DOWNLOAD_STATUS, PENDING)

    if verbose:
        queueMessage(chartScope, 'tag ' + config.tagPath + " written; value: " + str(config.value), MSG_STATUS_INFO)

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

