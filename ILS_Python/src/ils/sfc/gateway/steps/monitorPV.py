'''
Created on Dec 17, 2015

see the G2 procedures S88-RECIPE-INPUT-DATA__S88-MONITOR-PV.txt and S88-RECIPE-OUTPUT-DATA__S88-MONITOR-PV.txt

@author: rforbes
'''

import system, string
from java.util import Date 
from ils.sfc.gateway.api import getIsolationMode
from system.ils.sfc import getProviderName, getPVMonitorConfig, getDatabaseName
from ils.sfc.gateway.downloads import handleTimer, getElapsedMinutes
from ils.sfc.gateway.recipe import RecipeData
from ils.io.api import getMonitoredTagPath
    
from ils.sfc.recipeData.api import s88Get, s88Set, s88GetTargetStepUUID, s88GetFromStep,s88SetFromStep
from ils.sfc.common.constants import SHARED_ERROR_COUNT_KEY, SHARED_ERROR_COUNT_LOCATION, TIMER_SET, TIMER_KEY, TIMER_LOCATION, \
    START_TIMER, PAUSE_TIMER, RESUME_TIMER,  VALUE, SETPOINT, RECIPE, \
    STEP_SUCCESS, STEP_FAILURE, DOWNLOAD, OUTPUT_VALUE, TAG, RECIPE_LOCATION, WRITE_OUTPUT_CONFIG, ACTUAL_DATETIME, ACTUAL_TIMING, TIMING, DOWNLOAD_STATUS, WRITE_CONFIRMED, \
    CLASS, DATA_LOCATION, DOWNLOAD_STATUS, IMMEDIATE, KEY, MONITOR, MONITORING, STRATEGY, RECIPE_DATA_TYPE, \
    RECIPE_LOCATION, PV_MONITOR_ACTIVE, PV_MONITOR_CONFIG, PV_VALUE, STATIC, TARGET_VALUE, TIMEOUT, WAIT, \
    DEACTIVATED, ACTIVATED, PAUSED, CANCELLED, RESUMED
from ils.sfc.gateway.util import getStepProperty, handleUnexpectedGatewayError
from ils.sfc.gateway.api import getChartLogger

from ils.sfc.common.constants import NAME, NUMBER_OF_TIMEOUTS, PV_MONITOR_STATUS, PV_MONITORING, PV_WARNING, PV_OK_NOT_PERSISTENT, PV_OK, \
    PV_BAD_NOT_CONSISTENT, PV_ERROR, SETPOINT_STATUS, SETPOINT_OK, SETPOINT_PROBLEM, \
    STEP_SUCCESS, STEP_FAILURE, TIMED_OUT

def activate(scopeContext, stepProperties, state):
    # some local constants
    MONITOR_ACTIVE_COUNT = "monitorActiveCount"
    PERSISTENCE_PENDING = "persistencePending"
    INITIALIZED = "initialized"
    MAX_PERSISTENCE = "maxPersistence"

    complete = False 

    try:
        # general initialization:
        chartScope = scopeContext.getChartScope()
        stepScope = scopeContext.getStepScope()
        recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION)
        stepName = getStepProperty(stepProperties, NAME)
        logger = getChartLogger(chartScope)
        logger.trace("In monitorPV.activate(), step: %s, state: %s, recipe location: %s..." % (str(stepName), str(state), str(recipeLocation)))

        # Everything will have the same tag provider - check isolation mode and get the provider
        isolationMode = getIsolationMode(chartScope)
        providerName = getProviderName(isolationMode)
        database = getDatabaseName(isolationMode)
        timerLocation = getStepProperty(stepProperties, TIMER_LOCATION) 
        timerKey = getStepProperty(stepProperties, TIMER_KEY)
        recipeDataLocation = getStepProperty(stepProperties, RECIPE_LOCATION)
        targetStepUUID = s88GetTargetStepUUID(chartScope, stepScope, recipeDataLocation)

        # This does not initially exist in the step scope dictionary, so we will get a value of False
        initialized = stepScope.get(INITIALIZED, False)   
        if state == DEACTIVATED:
            logger.trace("*** A deactivate has been detected ***")
            complete=True
        elif state == PAUSED:
            logger.trace("The PV Monitor was paused")
            handleTimer(chartScope, stepScope, stepProperties, timerKey, timerLocation, PAUSE_TIMER, logger)
        elif state == RESUMED:
            logger.trace("The PV Monitor was resumed")
            handleTimer(chartScope, stepScope, stepProperties, timerKey, timerLocation, RESUME_TIMER, logger)
        else:
            if not initialized:
                logger.trace("...initializing PV Monitor step %s ..." % (stepName))
                stepScope[NUMBER_OF_TIMEOUTS] = 0
                stepScope[TIMED_OUT] = False
                stepScope[INITIALIZED] = True
                stepScope["workDone"] = False
    
                configJson =  getStepProperty(stepProperties, PV_MONITOR_CONFIG)
                config = getPVMonitorConfig(configJson)
    
                # initialize each input
                maxPersistence = 0
                monitorActiveCount = 0
                for configRow in config.rows:
                    logger.trace("PV Key: %s - Target Type: %s - Target Name: %s - Strategy: %s" % (configRow.pvKey, configRow.targetType, configRow.targetNameIdOrValue, configRow.strategy))
                    configRow.status = MONITORING
                    pvKey = configRow.pvKey
                    
                    # This is a little clever - the type of the target determines where we will store the results.  These results are used by the 
                    # download GUI block.  It appears that the PV of a PV monitoring block is always INPUT recipe data.  The target of a PV monitoring  
                    # block can be just about anything.  If the target is an OUTPUT - then write results there, if the target is anything else then store the 
                    # results in the INPUT.
                    targetType = configRow.targetType
                    if targetType == SETPOINT:
                        targetKey = configRow.targetNameIdOrValue
                        s88SetFromStep(targetStepUUID, targetKey + "." + PV_MONITOR_STATUS, PV_MONITORING, database)
                        s88SetFromStep(targetStepUUID, targetKey + "." + SETPOINT_STATUS, "", database)
                        s88SetFromStep(targetStepUUID, targetKey + "." + PV_MONITOR_ACTIVE, True, database)
                        s88SetFromStep(targetStepUUID, targetKey + "." + PV_VALUE, "Null", database)
                    else:
                        targetKey = configRow.pvKey

                    dataType = s88GetFromStep(targetStepUUID, targetKey + "." + RECIPE_DATA_TYPE, database)
                    configRow.isOutput = (dataType == 'Output')

                    configRow.isDownloaded = False
                    configRow.persistenceOK = False
                    configRow.inToleranceTime = 0
                    configRow.outToleranceTime = Date().getTime()
                    monitorActiveCount = monitorActiveCount + 1
                    
                    if configRow.persistence > maxPersistence:
                        maxPersistence = configRow.persistence
                        
                    # we assume the target value won't change, so we get it once.
                    # (This is storing the target into the config structure not recipe data)
                    # The constants are all lower case so make this case insensitive by converting to lowercase
                    targetType = string.lower(configRow.targetType)
                    configRow.targetType = targetType
                    
                    if targetType == SETPOINT:
                        # This means that the recipe data is an OUTPUT recipe data that points to some part of a controller I/O,
                        # the recipe data will tell what
                        logger.trace("Getting the target value using SETPOINT strategy...")
                        targetKey = configRow.targetNameIdOrValue
                        tagPath =    s88GetFromStep(targetStepUUID, targetKey + '.Tag', database)
                        outputType = s88GetFromStep(targetStepUUID, targetKey + '.OutputType', database)
                        logger.tracef("...Tagpath: %s, Output Type: %s", tagPath, outputType)
                        
                        # I'm not sure why I need to put this into the configrow PAH 2/19/17
                        configRow.targetValue = s88GetFromStep(targetStepUUID, targetKey + '.TargetValue', database)
#                        targetRd.set(TARGET_VALUE, configRow.targetValue)
                        
                    elif targetType == VALUE:
                        # The target value is hard coded in the config data
                        configRow.targetValue = float(configRow.targetNameIdOrValue)
                    elif targetType == TAG:
                        # Read the value from a tag
                        qv = system.tag.read("[" + providerName + "]" + configRow.targetNameIdOrValue)
                        configRow.targetValue = qv.value
                    elif targetType == RECIPE:
                        # This means that the value will be in some property of the recipe data
                        configRow.targetValue = s88GetFromStep(targetStepUUID, targetKey, database)           

                    logger.trace("...the target value is: %s" % (str(configRow.targetValue)))

                # Put the initialized config data back into step scope for the next iteration
                stepScope[PV_MONITOR_CONFIG] = config
                stepScope[MONITOR_ACTIVE_COUNT] = monitorActiveCount
                stepScope[PERSISTENCE_PENDING] = False
                stepScope[MAX_PERSISTENCE] = maxPersistence
                
                # This will clear and/or set the timer if the block is configured to do so               
                startTimer = getStepProperty(stepProperties, TIMER_SET)
                if startTimer:
                    handleTimer(chartScope, stepScope, stepProperties, timerKey, timerLocation, START_TIMER, logger)

                # If there are no rows configured to monitor, then the block is done, even though the block is probably misconfigured
                if monitorActiveCount <= 0:
                    logger.warn("PV Monitoring block is not configured to monitor anything")
                    complete = True

                logger.tracef("Completed the initialization phase of PV monitoring")
            
            else:    
                logger.trace("...monitoring step %s..." % (stepName))
                
                durationLocation = getStepProperty(stepProperties, DATA_LOCATION)
                durationStrategy = getStepProperty(stepProperties, STRATEGY)
                if durationStrategy == STATIC:
                    timeLimitMin = getStepProperty(stepProperties, VALUE) 
                else:
                    durationKey = getStepProperty(stepProperties, KEY)
                    timeLimitMin = s88Get(chartScope, stepScope, durationKey, durationLocation)
                    
                logger.trace("   PV Monitor time limit strategy: %s - minutes: %s" % (durationStrategy, str(timeLimitMin)))
                    
                config = stepScope[PV_MONITOR_CONFIG]
            
                # Monitor for the specified period, possibly extended by persistence time
                timerStart=s88Get(chartScope, stepScope, timerKey + ".StartTime", timerLocation)

                # It is possible that this block starts before some other block starts the timer
                if timerStart == None:
                    logger.trace("   ...waiting for the timer to start...")
                    complete = False
                    return complete
                
                elapsedMinutes = s88Get(chartScope, stepScope, timerKey + ".ElapsedMinutes", timerLocation)
                persistencePending = stepScope[PERSISTENCE_PENDING]
                monitorActiveCount = stepScope[MONITOR_ACTIVE_COUNT]
                maxPersistence = stepScope[MAX_PERSISTENCE]
                
                extendedDuration = timeLimitMin + maxPersistence # extra time allowed for persistence checks
                
                if monitorActiveCount > 0 and ((elapsedMinutes < timeLimitMin) or (persistencePending and elapsedMinutes < extendedDuration)):
                    logger.trace("Starting a PV monitor pass...")
           
                    monitorActiveCount = 0
                    persistencePending = False
                    for configRow in config.rows:
                        if not configRow.enabled:
                            continue;
                        
                        # SUCCESS is a terminal state - once the criteria is met stop monitoring that PV
                        if configRow.status == PV_OK:
                            continue
                        
                        logger.trace('PV monitoring - PV: %s, Target type: %s, Target: %s, Strategy: %s' % (configRow.pvKey, configRow.targetType, configRow.targetNameIdOrValue, configRow.strategy))
    
                        pvKey = configRow.pvKey
                        dataType = s88GetFromStep(targetStepUUID, pvKey + "." + RECIPE_DATA_TYPE, database)
    
                        # This is a little clever - the type of the target determines where we will store the results.  These results are used by the 
                        # download GUI block.  It appears that the PV of a PV monitoring block is always INPUT recipe data.  The target of a PV monitoring  
                        # block can be just about anything.  If the target is an OUTPUT - then write results there, if the target is anything else then store the 
                        # results in the INPUT.
                        targetType = configRow.targetType
                        if targetType == SETPOINT:
                            targetKey = configRow.targetNameIdOrValue
                        else:
                            targetKey = configRow.pvKey
                        
                        targetStepUUID = s88GetTargetStepUUID(chartScope, stepScope, recipeDataLocation)
                        monitorActiveCount = monitorActiveCount + 1
                        #TODO: how are we supposed to know about a download unless we have an Output??
                        if configRow.isOutput and not configRow.isDownloaded:
                            logger.trace("The item is an output and it hasn't been downloaded...")
                            downloadStatus = s88Get(chartScope, stepScope, targetKey + "." + DOWNLOAD_STATUS, recipeDataLocation)
                            configRow.isDownloaded = (downloadStatus == STEP_SUCCESS or downloadStatus == STEP_FAILURE)
                            if configRow.isDownloaded:
                                logger.trace("...the download just completed!")
                                configRow.downloadTime = elapsedMinutes
            
                        # Display the PVs as soon as the block starts running, even before the SP has been written
                        tagPath = getMonitoredTagPath(targetStepUUID, pvKey, providerName, database)
                        qv = system.tag.read(tagPath)
                        
                        logger.trace("The present qualified value for %s is: %s-%s" % (tagPath, str(qv.value), str(qv.quality)))
                        if not(qv.quality.isGood()):
                            logger.warn("The monitored value is bad: %s-%s" % (str(qv.value), str(qv.quality)))
                            continue
    
                        pv=qv.value
                        s88Set(chartScope, stepScope, targetKey + ".pvValue", pv, recipeDataLocation)
    
                        # If we are configured to wait for the download and it hasn't been downloaded, then don't start to monitor
                        if configRow.download == WAIT and not configRow.isDownloaded:
                            logger.trace('   skipping because this output is designated to wait for a download and it has not been downloaded')
                            continue
                       
                        # if we're just reading for display purposes, we're done with this pvInput:

                        if configRow.strategy != MONITOR:
                            logger.trace('   skipping because the strategy is NOT monitor!')
                            continue
                        
                        target=configRow.targetValue
                        toleranceType=configRow.toleranceType
                        tolerance=configRow.tolerance
                        limitType=configRow.limits
                        
                        # Check if the value is within the limits
                        from ils.sfc.gateway.util import compareValueToTarget
                        valueOk,txt = compareValueToTarget(pv, target, tolerance, limitType, toleranceType, logger)
                        
                        # check persistence:
                        if valueOk:
                            configRow.outToleranceTime = 0
                            isConsistentlyOutOfTolerance = False
                            if configRow.inToleranceTime != 0:
                                isPersistent = getElapsedMinutes(Date(long(configRow.inToleranceTime))) > configRow.persistence                    
                            else:
                                configRow.inToleranceTime = Date().getTime()
                                if configRow.persistence > 0.0:
                                    isPersistent = False
                                else:
                                    isPersistent = True
                        else:
                            configRow.inToleranceTime = 0
                            isPersistent = False
                            if configRow.outToleranceTime != 0:
                                outToleranceTime=long(configRow.outToleranceTime)
                                isConsistentlyOutOfTolerance = getElapsedMinutes(Date(long(outToleranceTime))) > configRow.consistency
                            else:
                                isConsistentlyOutOfTolerance = False
                                configRow.outToleranceTime = Date().getTime()
                                
                        # check dead time - assume that immediate writes coincide with starting the timer.      
                        if configRow.download == IMMEDIATE:
                            logger.tracef("Setting the reference time to the timer start time", timerStart)
                            referenceTime = timerStart
                        else:
                            logger.tracef("Setting the reference time as the download time")
                            referenceTime = configRow.downloadTime

                        logger.tracef("Checking if the dead time has been exceeded:: Elapsed Minutes: %f, referenceTime: %s, allowed dead time: %f", elapsedMinutes, str(referenceTime), configRow.deadTime)
                        deadTimeExceeded = (elapsedMinutes - referenceTime) > configRow.deadTime 

                        # print '   pv', presentValue, 'target', configRow.targetValue, 'low limit',  configRow.lowLimit, 'high limit', configRow.highLimit   
                        # print '   inToleranceTime', configRow.inToleranceTime, 'outToleranceTime', configRow.outToleranceTime, 'deadTime',configRow.deadTime  
                        # SUCCESS, WARNING, MONITORING, NOT_PERSISTENT, NOT_CONSISTENT, OUT_OF_RANGE, ERROR, TIMEOUT
                        if valueOk:
                            if isPersistent:
                                configRow.status = PV_OK
                                s88Set(chartScope, stepScope, targetKey + "." + PV_MONITOR_ACTIVE, False, recipeDataLocation)
                            else:
                                configRow.status = PV_OK_NOT_PERSISTENT
                                persistencePending = True
                        else: # out of tolerance
                            if deadTimeExceeded:
                                # print '   setting error status'
                                configRow.status = PV_ERROR
                            elif isConsistentlyOutOfTolerance:
                                configRow.status = PV_WARNING
                            else:
                                configRow.status = PV_BAD_NOT_CONSISTENT
            
                        if configRow.status == PV_ERROR:
                            # Set the setpoint status to PROBLEM - this cannot be reset
                            s88Set(chartScope, stepScope, targetKey + "." + SETPOINT_STATUS, SETPOINT_PROBLEM, recipeDataLocation)
            
                        logger.trace("  Status: %s" % configRow.status)  
                        s88Set(chartScope, stepScope, targetKey + "." + PV_MONITOR_STATUS, configRow.status, recipeDataLocation)        
                
                logger.trace("Checking end conditions...")
                if monitorActiveCount == 0:
                    logger.info("The PV monitor is finished because there is nothing left to monitor...")
                    complete = True
                
                # If the maximum time has been exceeded then count how many items did not complete their monitoring, aka Timed-Out 
                if (elapsedMinutes > timeLimitMin) or (persistencePending and elapsedMinutes > extendedDuration):
                    logger.info("The PV monitor is finished because the max run time has been reached...")
                    complete = True
                    
                    numTimeouts = 0
                    for configRow in config.rows:
                        logger.trace("...checking row whose status is: %s" % (configRow.status))
                        targetType = configRow.targetType
                        if targetType == SETPOINT:
                            targetKey = configRow.targetNameIdOrValue
                        else:
                            targetKey = configRow.pvKey
    
                        if configRow.status in [PV_ERROR, PV_WARNING, PV_BAD_NOT_CONSISTENT]:
                            numTimeouts = numTimeouts + 1
                            s88Set(chartScope, stepScope, targetKey + "." + SETPOINT_STATUS, SETPOINT_PROBLEM, recipeDataLocation)
                            s88Set(chartScope, stepScope, targetKey + "." + PV_MONITOR_STATUS, PV_ERROR, recipeDataLocation)
    
                        s88Set(chartScope, stepScope, targetKey + "." + PV_MONITOR_ACTIVE, 0, recipeDataLocation)
                    stepScope[NUMBER_OF_TIMEOUTS] = numTimeouts
                    if numTimeouts > 0:
                        stepScope[TIMED_OUT] = True
                    logger.info("...there were %i PV monitoring timeouts!" % (numTimeouts))
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in monitorPV.py', logger)
    finally:
        # do cleanup here
        pass
        
    return complete