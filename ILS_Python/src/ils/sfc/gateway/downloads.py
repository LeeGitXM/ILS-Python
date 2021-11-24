'''

Helper methods for I/O steps (WriteOutput, Monitor PV, Monitor Downloads) that 
do not directly involve client interaction

Created on Jun 18, 2015
@author: rforbes
'''

import system, string
from java.util import Date
from ils.io.util import readTag
from ils.sfc.recipeData.api import s88Set, s88Get, s88SetFromId
from ils.sfc.recipeData.constants import TIMER
from ils.sfc.common.constants import START_TIMER, PAUSE_TIMER, RESUME_TIMER, CLEAR_TIMER, ERROR_COUNT_LOCAL, \
    WRITE_CONFIRMED, DOWNLOAD_STATUS, SUCCESS, FAILURE, OUTPUT_TYPE

'''
perform the timer-related logic for a step
'''
def handleTimer(timerRecipeDataId, command, logger, db):
    logger.trace("Timer command: <%s>, the timer's recipe data id is: %d" % (command, timerRecipeDataId))
    key = "command"
    
    # The specifics of the command are handled in the s88Set command 
    if command == CLEAR_TIMER:
        logger.info("Clearing the download timer...")
        s88SetFromId(timerRecipeDataId, TIMER, key, CLEAR_TIMER, db)

    if command == START_TIMER:
        logger.info("Starting the download timer...")
        s88SetFromId(timerRecipeDataId, TIMER, key, START_TIMER, db)
    
    if command == PAUSE_TIMER:
        logger.info("Pausing the download timer...")
        s88SetFromId(timerRecipeDataId, TIMER, key, PAUSE_TIMER, db)
    
    if command == RESUME_TIMER:
        logger.info("Resuming the download timer...")
        s88SetFromId(timerRecipeDataId, TIMER, key, RESUME_TIMER, db)


# This returns the elapsed time in minutes from the given Java time (milliseconds sine the epoch)
def getElapsedMinutes(startTime):
    now=Date()
    elapsedMinutes = (now.getTime() - startTime.getTime()) / 1000.0 / 60.0
    return elapsedMinutes

'''
Write an output value
Modified this to use WriteDatum from the IO layer which automatically does a Write Confirm...
This updates the internal error counter in the step, it is the job of the step to update the error counter that the user specified.
'''
def writeValue(chartScope, stepScope, config, logger, providerName, recipeDataScope):
    
    tagPath = "[%s]%s" % (providerName, config.tagPath)
    outputType = s88Get(chartScope, stepScope, config.key + "." + OUTPUT_TYPE, recipeDataScope)
    
    #----------------------------------------------------------------------------------------------------
    def _writeValue(chartScope=chartScope, stepScope=stepScope, config=config, logger=logger, providerName=providerName, 
                    recipeDataScope=recipeDataScope, tagPath=tagPath, outputType=outputType):
        from ils.io.api import write, writeRamp
        from ils.common.config import getTagProvider
        from ils.sfc.gateway.api import postToQueue
        from ils.sfc.common.constants import MSG_STATUS_INFO, MSG_STATUS_WARNING, MSG_STATUS_ERROR
        from ils.sfc.common.constants import STEP_DOWNLOADING, STEP_SUCCESS, STEP_FAILURE, RAMP_TIME, RAMP_UPDATE_FREQUENCY

        productionProviderName = getTagProvider()   # Get the production tag provider
        
        '''
        Only pay attention to the write enabled flag if we are writing to a production tag.
        '''
        s88WriteEnabled = readTag("[" + providerName + "]/Configuration/SFC/sfcWriteEnabled").value   
        if providerName == productionProviderName and not(s88WriteEnabled):
            logger.info('Write bypassed for %s because SFC writes are inhibited!' % (tagPath))
            s88Set(chartScope, stepScope, config.key + "." + DOWNLOAD_STATUS, STEP_FAILURE, recipeDataScope)

            errorCount = stepScope[ERROR_COUNT_LOCAL]
            stepScope[ERROR_COUNT_LOCAL] = errorCount + 1
#            if errorCountKey <> "" and errorCountLocation <> "":
#                print " *** INCREMENTING THE GLOBAL ERROR COUNTER *** "
#                errorCount = s88Get(chartScope, stepScope, errorCountKey, errorCountLocation)
#                s88Set(chartScope, stepScope, errorCountKey, errorCount + 1, errorCountLocation)
    
            txt = "Write of %s to %s bypassed because SFC I/O is disabled." % (str(config.value), config.tagPath)
            postToQueue(chartScope, MSG_STATUS_WARNING, txt)
            return
        
        logger.info("writing %s to %s - attribute %s (confirm: %s)" % (config.value, tagPath, outputType,str(config.confirmWrite)))
        
        logger.trace("---- setting status to downloading ----")
        s88Set(chartScope, stepScope, config.key + "." + DOWNLOAD_STATUS, STEP_DOWNLOADING, recipeDataScope)
        
        if string.upper(outputType) in ["OUTPUT RAMP", "SETPOINT RAMP"]:
            logger.tracef("Fetching ramp properties from %s recipe data", config.key)
            rampTime = s88Get(chartScope, stepScope, config.key + "." + RAMP_TIME, recipeDataScope)
            updateFrequency = s88Get(chartScope, stepScope, config.key + "." + RAMP_UPDATE_FREQUENCY, recipeDataScope)
            writeStatus, txt = writeRamp(tagPath, config.value, outputType, rampTime, updateFrequency, config.confirmWrite)
            
            logger.trace("writeRamp() returned: %s - %s" % (str(writeStatus), txt))
        else:
            writeStatus, txt = write(tagPath, config.value, config.confirmWrite, outputType)
            logger.trace("write() returned: %s - %s" % (str(writeStatus), txt))
        config.written = True
    
        if config.confirmWrite:
            s88Set(chartScope, stepScope, config.key + "." + WRITE_CONFIRMED, writeStatus, recipeDataScope)
    
        if writeStatus:
            logger.trace("---- setting status to SUCCESS ----")
            s88Set(chartScope, stepScope, config.key + "." + DOWNLOAD_STATUS, STEP_SUCCESS, recipeDataScope)
            postToQueue(chartScope, MSG_STATUS_INFO, 'tag ' + config.tagPath + " written; value: " + str(config.value) + txt)
        else:
            logger.trace("---- setting status to FAILURE ----")
            s88Set(chartScope, stepScope, config.key + "." + DOWNLOAD_STATUS, STEP_FAILURE, recipeDataScope)

            errorCount = stepScope[ERROR_COUNT_LOCAL]
            stepScope[ERROR_COUNT_LOCAL] = errorCount + 1
            postToQueue(chartScope, MSG_STATUS_ERROR, 'tag ' + config.tagPath + " written; value: " + str(config.value) + txt)        
        
    #----------------------------------------------------------------------------------------------------
    system.util.invokeAsynchronous(_writeValue)
    return


def confirmWrite(chartScope, config, logger):
    '''confirms the write on a separate thread and writes the result back to recipe data'''
    import threading
    def worker(chartScope, config, logger):
        # ordinarily, exceptions are automatically caught in PythonCall but that
        # doesn't work for threads so we need to have a local handler:
        from ils.sfc.gateway.api import handleUnexpectedGatewayError
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
