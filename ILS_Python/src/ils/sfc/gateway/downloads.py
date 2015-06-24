'''

Helper methods for I/O steps (WriteOutput, Monitor PV, Monitor Downloads) that 
do not directly involve client interaction

Created on Jun 18, 2015
@author: rforbes
'''

def handleTimer(chartScope, stepScope, stepProperties):
    '''perform the timer-related logic for a step'''
    from ils.sfc.gateway.api import s88Set
    from ils.sfc.gateway.util import getStepProperty
    from system.ils.sfc.common.Constants import TIMER_LOCATION, TIMER_KEY, TIMER_SET, TIMER_CLEAR
    import time
    timerLocation = getStepProperty(stepProperties, TIMER_LOCATION)
    timerKey = getStepProperty(stepProperties, TIMER_KEY)
    setTimer = getStepProperty(stepProperties, TIMER_SET)
    # Note: there may be no timer-clear property, in which case the
    # value is null which 
    clearTimer = getStepProperty(stepProperties, TIMER_CLEAR)
    if setTimer:
        s88Set(chartScope, stepScope, timerKey, time.time(), timerLocation)
    elif clearTimer:
        s88Set(chartScope, stepScope, timerKey, None, timerLocation)

def getTimerStart(chartScope, stepScope, stepProperties):
    '''get the start time for a timer (will be None if cleared but not set)'''
    from ils.sfc.gateway.util import getStepProperty
    from ils.sfc.gateway.api import s88Get
    from system.ils.sfc.common.Constants import TIMER_LOCATION, TIMER_KEY
    timerLocation = getStepProperty(stepProperties, TIMER_LOCATION)
    timerKey = getStepProperty(stepProperties, TIMER_KEY)
    return s88Get(chartScope, stepScope, timerKey, timerLocation)

def waitForTimerStart(chartScope, stepScope, stepProperties, logger):
    '''Wait until the i/o timer shows a non-null value'''
    from ils.sfc.common.constants import _STATUS, CANCEL, PAUSE, SLEEP_INCREMENT
    from ils.sfc.gateway.util import checkForCancelOrPause
    import time
    timerStart = getTimerStart(chartScope, stepScope, stepProperties)
    while timerStart == None:
        
        # Handle Cancel/Pause, as this loop has sleeps
        chartStatus = checkForCancelOrPause(stepScope, logger)
        if chartStatus == CANCEL:
            return None
        elif chartStatus == PAUSE:
            continue
        
        time.sleep(SLEEP_INCREMENT)
        timerStart = getTimerStart(chartScope, stepScope, stepProperties)
    return timerStart

def writeOutput(chartScope, config, verbose, logger):
    '''write an output value'''
    from ils.sfc.gateway.util import queueMessage
    from ils.sfc.common.constants import MSG_STATUS_INFO
    # updateStepTimeStatus(chartScope, config.key, ORANGE)
    logger.debug("writing %s.%s" % (config.tagPath, config.ioAttribute))
    config.io.set(config.ioAttribute, config.value)
    config.written = True
    if config.confirmWrite:
        confirmWrite(chartScope, config, logger)
    # updateStepTimeStatus(chartScope, config.key, GREEN)
    # TODO: handle pending status and write confirmation
    # s88Set(chartScope, stepScope, createRecipeKey(row.key, WRITE_CONFIRMED), True, recipeLocation)
    # updateStepTimeStatus(chartScope, config.key, RED)
    if verbose:
        queueMessage(chartScope, 'tag ' + config.tagPath + " written; value: " + str(config.value), MSG_STATUS_INFO)

def confirmWrite(chartScope, config, logger):
    '''confirms the write on a separate thread and writes the result back to recipe data'''
    import threading
    def worker(chartScope, config, logger):
        from system.ils.sfc.common.Constants import WRITE_CONFIRMED
        # ordinarily, exceptions are automatically caught in PythonCall but that
        # doesn't work for threads so we need to have a local handler:
        from ils.sfc.gateway.util import handleUnexpectedGatewayError
        import sys
        try:
            actualValue = config.io.get(config.ioAttribute)
            writeConfirmed = (actualValue == config.value)
            config.outputRD.set(WRITE_CONFIRMED, writeConfirmed)
        except:
            # note that Java exceptions are not caught by "except Exception", so this
            # way is more complete:
            e = sys.exc_info()[1]
            msg = "Error confirming write: " + str(e)
            print msg
            handleUnexpectedGatewayError(chartScope, msg, logger)
    t = threading.Thread(target=worker, args=(chartScope, config, logger,))
    t.start()

