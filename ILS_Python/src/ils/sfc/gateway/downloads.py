'''

Helper methods for I/O steps (WriteOutput, Monitor PV, Monitor Downloads) that 
do not directly involve client interaction

Created on Jun 18, 2015
@author: rforbes
'''

import system
from java.util import Date, Calendar
from ils.sfc.recipeData.api import s88Set, s88Get
from ils.sfc.common.constants import START_TIMER, PAUSE_TIMER, STOP_TIMER, RESUME_TIMER, CLEAR_TIMER 
from system.ils.sfc.common.Constants import DEACTIVATED, ACTIVATED, PAUSED, CANCELLED, RESUMED, TAG_PATH, \
    TIMER_STATE, TIMER_STATE_CANCEL, TIMER_STATE_CLEAR, TIMER_STATE_PAUSE, TIMER_STATE_RESUME, TIMER_STATE_RUN, TIMER_STATE_STOP, \
    TIMER_LOCATION, TIMER_KEY, TIMER_SET, TIMER_CLEAR, TIMER_RUN_MINUTES, TIMER_START_TIME
    

def handleTimer(chartScope, stepScope, stepProperties, timerKey, timerLocation, command, logger):
    '''perform the timer-related logic for a step'''
    logger.trace("Timer command: <%s>, the key and attribute are: %s" % (command, timerKey))
    key = timerKey + ".command"
    
    # The specifics of the command are handled in the s88Set command 
    if command == CLEAR_TIMER:
        logger.info("Clearing the download timer...")
        s88Set(chartScope, stepScope, key, CLEAR_TIMER, timerLocation)

    if command == START_TIMER:
        logger.info("Starting the download timer...")
        s88Set(chartScope, stepScope, key, START_TIMER, timerLocation)
    
    if command == PAUSE_TIMER:
        logger.info("Pausing the download timer...")
        s88Set(chartScope, stepScope, key, PAUSE_TIMER, timerLocation)
    
    if command == RESUME_TIMER:
        logger.info("Resuming the download timer...")
        s88Set(chartScope, stepScope, key, RESUME_TIMER, timerLocation)


# This returns the elapsed time in minutes from the given Java time (milliseconds sine the epoch)
def getElapsedMinutes(startTime):
    now=Date()
    elapsedMinutes = (now.getTime() - startTime.getTime()) / 1000.0 / 60.0
    return elapsedMinutes


# Write an output value
# Modified this to use WriteDatum from the IO layer which automatically does a Write Confirm...
def writeValue(chartScope, stepScope, config, errorCountKey, errorCountLocation, logger, providerName, recipeDataScope):
    
    #----------------------------------------------------------------------------------------------------
    def _writeValue(chartScope=chartScope, stepScope=stepScope, config=config, errorCountKey=errorCountKey, errorCountLocation=errorCountLocation, logger=logger, providerName=providerName, recipeDataScope=recipeDataScope):
        from ils.io.api import write
        from ils.sfc.gateway.util import queueMessage
        from ils.sfc.common.constants import MSG_STATUS_INFO
        from ils.sfc.common.constants import STEP_DOWNLOADING, STEP_SUCCESS, STEP_FAILURE, DOWNLOAD_STATUS, PENDING, OUTPUT_TYPE, SETPOINT, WRITE_CONFIRMED, SUCCESS, FAILURE

        tagPath = "[%s]%s" % (providerName, config.tagPath)
        outputType = s88Get(chartScope, stepScope, config.key + "." + OUTPUT_TYPE, recipeDataScope)
     
        s88WriteEnabled = system.tag.read("[" + providerName + "]/Configuration/SFC/sfcWriteEnabled").value   
        if not(s88WriteEnabled):
            logger.info('Write bypassed for %s because SFC writes are inhibited!' % (tagPath))
            s88Set(chartScope, stepScope, config.key + "." + DOWNLOAD_STATUS, STEP_FAILURE, recipeDataScope)

            if errorCountKey <> "" and errorCountLocation <> "":
                print " *** INCREMENTING THE GLOBAL ERROR COUNTER *** "
                errorCount = s88Get(chartScope, stepScope, errorCountKey, errorCountLocation)
                s88Set(chartScope, stepScope, errorCountKey, errorCount + 1, errorCountLocation)
    
            txt = "Write of %s to %s bypassed because SFC I/O is disabled." % (str(config.value), config.tagPath)
            queueMessage(chartScope, txt, MSG_STATUS_INFO)
            return
        
        logger.info("writing %s to %s - attribute %s (confirm: %s)" % (config.value, tagPath, outputType,str(config.confirmWrite)))
        
        logger.trace("---- setting status to downloading ----")
        s88Set(chartScope, stepScope, config.key + "." + DOWNLOAD_STATUS, STEP_DOWNLOADING, recipeDataScope)
        writeStatus, txt = write(tagPath, config.value, config.confirmWrite, outputType)
        logger.trace("WriteDatum returned: %s - %s" % (str(writeStatus), txt))
        config.written = True
    
        if config.confirmWrite:
            s88Set(chartScope, stepScope, config.key + "." + WRITE_CONFIRMED, writeStatus, recipeDataScope)
    
        if writeStatus:
            logger.trace("---- setting status to SUCCESS ----")
            s88Set(chartScope, stepScope, config.key + "." + DOWNLOAD_STATUS, STEP_SUCCESS, recipeDataScope)
        else:
            logger.trace("---- setting status to FAILURE ----")
            s88Set(chartScope, stepScope, config.key + "." + DOWNLOAD_STATUS, STEP_FAILURE, recipeDataScope)

            if errorCountKey <> "" and errorCountLocation <> "":
                print " *** INCREMENTING THE GLOBAL ERROR COUNTER FOR %s *** " % (config.key)
                errorCount = s88Get(chartScope, stepScope, errorCountKey, errorCountLocation)
                s88Set(chartScope, stepScope, errorCountKey, errorCount + 1, errorCountLocation)
    
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

