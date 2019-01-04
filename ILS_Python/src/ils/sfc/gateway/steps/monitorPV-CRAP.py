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
from ils.io.api import getMonitoredTagPath

from ils.sfc.common.util import callMethodWithParams
from ils.sfc.recipeData.api import s88Get, s88Set, s88GetStep, s88GetFromStep, s88SetFromStep, s88GetRecipeDataId, s88GetRecipeDataIdFromStep, s88GetFromId, s88SetFromId
from ils.sfc.common.constants import TIMER_SET, TIMER_KEY, TIMER_LOCATION, ACTIVATION_CALLBACK, \
    START_TIMER, PAUSE_TIMER, RESUME_TIMER,  VALUE, SETPOINT, RECIPE, \
    STEP_SUCCESS, STEP_FAILURE, DOWNLOAD, OUTPUT_VALUE, TAG, RECIPE_LOCATION, WRITE_OUTPUT_CONFIG, ACTUAL_DATETIME, ACTUAL_TIMING, TIMING, DOWNLOAD_STATUS, WRITE_CONFIRMED, \
    CLASS, DATA_LOCATION, DOWNLOAD_STATUS, IMMEDIATE, KEY, MONITOR, MONITORING, STRATEGY, RECIPE_DATA_TYPE, \
    RECIPE_LOCATION, PV_MONITOR_ACTIVE, PV_MONITOR_CONFIG, PV_VALUE, STATIC, TARGET_VALUE, TIMEOUT, WAIT, \
    DEACTIVATED, ACTIVATED, PAUSED, CANCELLED, RESUMED, \
    ERROR_COUNT_SCOPE, ERROR_COUNT_KEY, ERROR_COUNT_MODE, COUNT_ABSOLUTE, \
    LOCAL_SCOPE, PRIOR_SCOPE, SUPERIOR_SCOPE, PHASE_SCOPE, OPERATION_SCOPE, GLOBAL_SCOPE, CHART_SCOPE, STEP_SCOPE, \
    NAME, PV_MONITOR_STATUS, PV_MONITORING, PV_WARNING, PV_OK_NOT_PERSISTENT, PV_OK, \
    PV_BAD_NOT_CONSISTENT, PV_ERROR, SETPOINT_STATUS, SETPOINT_PROBLEM
from ils.sfc.recipeData.constants import TIMER, OUTPUT, INPUT
from ils.sfc.gateway.api import getChartLogger, handleUnexpectedGatewayError, getStepProperty, compareValueToTarget

def activate(scopeContext, stepProperties, state):
    # some local constants
    MONITOR_ACTIVE_COUNT = "monitorActiveCount"
    PERSISTENCE_PENDING = "persistencePending"
    INITIALIZED = "initialized"
    MAX_PERSISTENCE = "maxPersistence"
    WATCH_ONLY = "watchOnly"

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

        # This does not initially exist in the step scope dictionary, so we will get a value of False
        initialized = stepScope.get(INITIALIZED, False)   
        if state == DEACTIVATED:
            logger.trace("*** A deactivate has been detected ***")
            complete=True
        elif state == PAUSED:
            logger.trace("The PV Monitor was paused")
            timerRecipeDataId = stepScope["timerRecipeDataId"]
            handleTimer(timerRecipeDataId, PAUSE_TIMER, logger, database)
        elif state == RESUMED:
            logger.trace("The PV Monitor was resumed")
            timerRecipeDataId = stepScope["timerRecipeDataId"]
            handleTimer(timerRecipeDataId, RESUME_TIMER, logger, database)
        else:
            if not initialized:
                logger.info("...***initializing*** PV Monitor step %s ..." % (stepName))
                stepScope[INITIALIZED] = True
                stepScope["workDone"] = False
                
                timerLocation = getStepProperty(stepProperties, TIMER_LOCATION)
                timerKey = getStepProperty(stepProperties, TIMER_KEY)
                timerRecipeDataId, timerRecipeDataType = s88GetRecipeDataId(chartScope, stepScope, timerKey, timerLocation)
                stepScope["timerRecipeDataId"] = timerRecipeDataId
                logger.infof("The timer recipe data id is: %d using %s - %s", timerRecipeDataId, timerLocation, timerKey)
    
                configJson =  getStepProperty(stepProperties, PV_MONITOR_CONFIG)
                config = getPVMonitorConfig(configJson)
    
                # initialize each input
                maxPersistence = 0
                monitorActiveCount = 0
                watchOnly = True
                
                recipeDataLocation = getStepProperty(stepProperties, RECIPE_LOCATION)
<<<<<<< HEAD
                targetStepUUID, stepName, keyAndAttribute = s88GetStep(chartScope, stepScope, recipeDataLocation, "")
=======
                targetStepUUID, stepName, unusedFillerVar = s88GetStep(chartScope, stepScope, recipeDataLocation, "")
>>>>>>> 009773b8b16718bc5b620fe8435d5c0dd1a4e887
                
                for configRow in config.rows:
                    logger.trace("PV Key: %s - Target Type: %s - Target Name: %s - Strategy: %s - Deadtime: %s" % 
                                 (configRow.pvKey, configRow.targetType, configRow.targetNameIdOrValue, configRow.strategy, str(configRow.deadTime)))

                    configRow.status = MONITORING
                    pvKey = configRow.pvKey
                    
                    if configRow.strategy == MONITOR:
                        watchOnly = False
                    
                    # This is a little clever - the type of the target determines where we will store the results.  These results are used by the 
                    # download GUI block.  The target of a PV monitoring  
                    # block can be just about anything.  If the target is an OUTPUT - then write results there, if the target is anything else then store the 
                    # results in the INPUT.
                    targetType = configRow.targetType
                    if targetType == SETPOINT:
                        targetKey = configRow.targetNameIdOrValue
                    else:
                        targetKey = configRow.pvKey
                        
                    logger.trace(" ...Target Type: %s - Target Key: %s" % (targetType, targetKey))
                        
                    targetRecipeDataId, targetRecipeDataType = s88GetRecipeDataIdFromStep(targetStepUUID, targetKey, database)
                    configRow.targetRecipeDataId = targetRecipeDataId
                    configRow.targetRecipeDataType = targetRecipeDataType
                    
                    logger.trace(" ...Target Recipe Id: %d - Recipe Data Type: %s" % (targetRecipeDataId, targetRecipeDataType))

                    configRow.lastPV = -999999.99
                    configRow.lastStatus = "UNKNOWN"
#                    targetRecipeDataId, targetRecipeDataType = s88GetRecipeDataId(chartScope, stepProperties, targetKey, recipeDataLocation)
#                    print "The target Recipe data id is: ", targetRecipeDataId, targetRecipeDataType
#                    configRow.targetRecipeDataId = targetRecipeDataId
#                    configRow.targetRecipeDataType = targetRecipeDataType
                    
                    if targetType == SETPOINT:
                        s88SetFromId(targetRecipeDataId, targetRecipeDataType, PV_VALUE, "Null", database)
                        s88SetFromId(targetRecipeDataId, targetRecipeDataType, SETPOINT_STATUS, "", database)

                    s88SetFromId(targetRecipeDataId, targetRecipeDataType, PV_MONITOR_STATUS, PV_MONITORING, database)
                    s88SetFromId(targetRecipeDataId, targetRecipeDataType, PV_MONITOR_ACTIVE, True, database)
                    
#                    dataType = s88GetFromId(targetRecipeDataId, targetRecipeDataType, RECIPE_DATA_TYPE, database)
                    configRow.isOutput = (targetRecipeDataType == 'Output')

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
                        targetKey = configRow.targetNameIdOrValue  # This is a different targetKey than we used above when we got the recipe data id
                        tagPath =    s88GetFromId(targetRecipeDataId, targetRecipeDataType, 'Tag', database)
                        outputType = s88GetFromId(targetRecipeDataId, targetRecipeDataType, 'OutputType', database)
                        logger.tracef("...Tagpath: %s, Output Type: %s", tagPath, outputType)
                        
                        # I'm not sure why I need to put this into the configrow PAH 2/19/17
                        configRow.targetValue = s88GetFromId(targetRecipeDataId, targetRecipeDataType, 'OutputValue', database)
                        
                    elif targetType == VALUE:
                        # The target value is hard coded in the config data
                        configRow.targetValue = float(configRow.targetNameIdOrValue)
                    elif targetType == TAG:
                        # Read the value from a tag
                        qv = system.tag.read("[" + providerName + "]" + configRow.targetNameIdOrValue)
                        configRow.targetValue = qv.value
                    elif targetType == RECIPE:
                        # This means that the target value will be in some property of the recipe data
                        print "Getting the target value from Recipe key:", recipeDataLocation, configRow.targetNameIdOrValue
                        configRow.targetValue = s88Get(chartScope, stepScope, configRow.targetNameIdOrValue, recipeDataLocation)           

                    logger.trace("...the target value is: %s" % (str(configRow.targetValue)))

                # Put the initialized config data back into step scope for the next iteration
                stepScope[PV_MONITOR_CONFIG] = config
                stepScope[MONITOR_ACTIVE_COUNT] = monitorActiveCount
                stepScope[PERSISTENCE_PENDING] = False
                stepScope[MAX_PERSISTENCE] = maxPersistence
                stepScope[WATCH_ONLY] = watchOnly
                
                durationStrategy = getStepProperty(stepProperties, STRATEGY)
                if durationStrategy == STATIC:
                    timeLimitMin = getStepProperty(stepProperties, VALUE)
                else:
                    durationKey = getStepProperty(stepProperties, KEY)
                    durationLocation = getStepProperty(stepProperties, DATA_LOCATION)
                    timeLimitMin = s88Get(chartScope, stepScope, durationKey + ".value", durationLocation)
                    
                stepScope["timeLimitMinutes"] = timeLimitMin
                
                # Look for a custom activation callback
                activationCallback = getStepProperty(stepProperties, ACTIVATION_CALLBACK)
                if activationCallback <> "":
                    logger.tracef("Calling custom activationCallback: %s", ACTIVATION_CALLBACK)
    
                    keys = ['scopeContext', 'stepProperties', 'config']
                    values = [scopeContext, stepProperties, config]
                    try:
                        config = callMethodWithParams(activationCallback, keys, values)
                        stepScope[PV_MONITOR_CONFIG] = config
                    except Exception, e:
                        try:
                            cause = e.getCause()
                            errMsg = "Error dispatching gateway message %s: %s" % (activationCallback, cause.getMessage())
                        except:
                            errMsg = "Error dispatching gateway message %s: %s" % (activationCallback, str(e))

                        logger.errorf(errMsg)

                # This will clear and/or set the timer if the block is configured to do so               
                startTimer = getStepProperty(stepProperties, TIMER_SET)
                if startTimer:
                    handleTimer(timerRecipeDataId, START_TIMER, logger, database)
                    stepScope["timerStarted"] = True
                else:
                    stepScope["timerStarted"] = False

                # If there are no rows configured to monitor, then the block is done, even though the block is probably misconfigured
                if monitorActiveCount <= 0:
                    logger.warn("PV Monitoring block is not configured to monitor anything")
                    complete = True

                logger.tracef("Completed the initialization phase of PV monitoring")
            
            else:    
                logger.trace("---(%s) monitoring---" % (stepName))
                
                timerRecipeDataId = stepScope["timerRecipeDataId"]
                timerStarted = stepScope["timerStarted"]
                timeLimitMin = stepScope["timeLimitMinutes"]
                    
                logger.tracef("(%s) PV Monitor time limit minutes: %s", stepName, str(timeLimitMin))
                    
                config = stepScope[PV_MONITOR_CONFIG]
                watchOnly = stepScope[WATCH_ONLY]
            
                # Wait until the timer starts before doing anything, once the timer has been started, we don't need to query it again.
                # It is possible that this block starts before some other block starts the timer
                if not(timerStarted):
                    startTime=s88GetFromId(timerRecipeDataId, TIMER, "StartTime", database)
                    if startTime == None:
                        logger.tracef("(%s) waiting for the timer to start...", stepName)
                        complete = False
                        return complete
                    stepScope["timerStarted"] = True
                
                elapsedMinutes = s88GetFromId(timerRecipeDataId, TIMER, "ELAPSEDMINUTES", database)
                logger.tracef("The elapsed minutes are: %s", str(elapsedMinutes))
                persistencePending = stepScope[PERSISTENCE_PENDING]
                monitorActiveCount = stepScope[MONITOR_ACTIVE_COUNT]
                maxPersistence = stepScope[MAX_PERSISTENCE]
                
                extendedDuration = timeLimitMin + maxPersistence # extra time allowed for persistence checks
                
                if monitorActiveCount > 0 and ((elapsedMinutes < timeLimitMin) or (persistencePending and elapsedMinutes < extendedDuration)) or watchOnly:
                    logger.tracef("(%s) Starting a PV monitor pass, (elapsed minutes: %s) ...", stepName, str(elapsedMinutes))
           
                    monitorActiveCount = 0
                    persistencePending = False
                    for configRow in config.rows:
                        if not configRow.enabled:
                            continue;
                        
                        targetRecipeDataId = configRow.targetRecipeDataId
                        targetRecipeDataType = configRow.targetRecipeDataType
                        
                        # REMOVE THESE TWO LINES
                        tolerance=configRow.tolerance
                        
                        # SUCCESS is a terminal state - once the criteria is met stop monitoring that PV
                        if configRow.status == PV_OK:
                            continue
                        
                        logger.tracef('(%s) PV: %s, Target type: %s, Target: %s, Strategy: %s', stepName, configRow.pvKey, configRow.targetType, configRow.targetNameIdOrValue, configRow.strategy)
    
                        pvKey = configRow.pvKey
 
                        # This is a little clever - the type of the target determines where we will store the results.  These results are used by the 
                        # download GUI block.  It appears that the PV of a PV monitoring block is always INPUT recipe data.  The target of a PV monitoring  
                        # block can be just about anything.  If the target is an OUTPUT - then write results there, if the target is anything else then store the 
                        # results in the INPUT.
                        targetType = configRow.targetType
                        if targetType == SETPOINT:
                            targetKey = configRow.targetNameIdOrValue
                        else:
                            targetKey = configRow.pvKey
    
                        monitorActiveCount = monitorActiveCount + 1
                        #TODO: how are we supposed to know about a download unless we have an Output??
                        if configRow.isOutput and not configRow.isDownloaded:
                            logger.tracef("(%s) The item is an output and it hasn't been downloaded...", stepName)
                            downloadStatus = s88GetFromId(targetRecipeDataId, targetRecipeDataType, DOWNLOAD_STATUS, database)
                            configRow.isDownloaded = (downloadStatus == STEP_SUCCESS or downloadStatus == STEP_FAILURE)
                            if configRow.isDownloaded:
                                logger.tracef("(%s) the download just completed!", stepName)
                                configRow.downloadTime = elapsedMinutes
            
                        # Display the PVs as soon as the block starts running, even before the SP has been written
                        tagPath = getMonitoredTagPath(targetRecipeDataId, targetRecipeDataType, providerName, database)
                        qv = system.tag.read(tagPath)
                        
                        logger.tracef("(%s) The present qualified value for %s is: %s-%s", stepName, tagPath, str(qv.value), str(qv.quality))
                        if not(qv.quality.isGood()):
                            logger.warnf("(%s) The monitored value for %s is bad: %s-%s", stepName, tagPath, str(qv.value), str(qv.quality))
                            continue
    
                        pv=qv.value
                        if pv != configRow.lastPV:
#                            s88Set(chartScope, stepScope, targetKey + ".pvValue", pv, recipeDataLocation)
                            s88SetFromId(targetRecipeDataId, targetRecipeDataType, "pvValue", pv, database)
                            configRow.lastPV = pv
                        else:
                            logger.tracef("Skipping update of pv")
    
                        # If we are configured to wait for the download and it hasn't been downloaded, then don't start to monitor
                        if configRow.download == WAIT and not configRow.isDownloaded:
                            logger.tracef("(%s) skipping because this output is designated to wait for a download and it has not been downloaded", stepName)
                            continue
                       
                        # if we're just reading for display purposes, we're done with this row
                        if configRow.strategy != MONITOR:
                            logger.tracef('(%s) skipping because the strategy is NOT monitor!', stepName)
                            continue
                        
                        target=configRow.targetValue
                        toleranceType=configRow.toleranceType
                        tolerance=configRow.tolerance
                        limitType=configRow.limits
                        
                        # Check if the value is within the limits

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
                            logger.tracef("(%s) Using the timer elapsed minutes (%s) to check if the dead time (%s) has been exceeded.", stepName, str(elapsedMinutes), str(configRow.deadTime) )
                            deadTimeExceeded = elapsedMinutes > configRow.deadTime
                        else:
                            logger.tracef("(%s) Setting the reference time as the download time", stepName)
                            referenceTime = configRow.downloadTime
                            deadTimeExceeded = (elapsedMinutes - referenceTime) > configRow.deadTime 

                        logger.tracef("(%s) Checking if the dead time has been exceeded: %s", stepName, str(deadTimeExceeded))

                        # print '   pv', presentValue, 'target', configRow.targetValue, 'low limit',  configRow.lowLimit, 'high limit', configRow.highLimit   
                        # print '   inToleranceTime', configRow.inToleranceTime, 'outToleranceTime', configRow.outToleranceTime, 'deadTime',configRow.deadTime  
                        # SUCCESS, WARNING, MONITORING, NOT_PERSISTENT, NOT_CONSISTENT, OUT_OF_RANGE, ERROR, TIMEOUT
                        if valueOk:
                            if isPersistent:
                                configRow.status = PV_OK
#                                s88Set(chartScope, stepScope, targetKey + "." + PV_MONITOR_ACTIVE, False, recipeDataLocation)
                                s88SetFromId(targetRecipeDataId, targetRecipeDataType, PV_MONITOR_ACTIVE, False, database)
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
            
                        if configRow.status == PV_ERROR and string.upper(targetRecipeDataType) == OUTPUT:
                            # Set the setpoint status to PROBLEM - this cannot be reset
#                            s88Set(chartScope, stepScope, targetKey + "." + SETPOINT_STATUS, SETPOINT_PROBLEM, recipeDataLocation)
                            print "Setting the setpoint status for a ", targetRecipeDataType
                            s88SetFromId(targetRecipeDataId, targetRecipeDataType, SETPOINT_STATUS, SETPOINT_PROBLEM, database)
            
                        logger.tracef("(%s) Status: %s", stepName, configRow.status)
                        if configRow.status != configRow.lastStatus:
#                            s88Set(chartScope, stepScope, targetKey + "." + PV_MONITOR_STATUS, configRow.status, recipeDataLocation)        
                            s88SetFromId(targetRecipeDataId, targetRecipeDataType, PV_MONITOR_STATUS, configRow.status, database)
                            configRow.lastStatus = configRow.status
                
                logger.tracef("(%s) Checking end conditions...", stepName)
                if monitorActiveCount == 0:
                    logger.infof("(%s) The PV monitor is finished because there is nothing left to monitor...", stepName)
                    complete = True
                
                # If the maximum time has been exceeded then count how many items did not complete their monitoring, aka Timed-Out 
                if ((elapsedMinutes > timeLimitMin) or (persistencePending and elapsedMinutes > extendedDuration)) and not(watchOnly):
                    logger.infof("(%s) The PV monitor is finished because the max run time has been reached...", stepName)
                    complete = True
                
                if complete:
                    logger.tracef("(%s) The PV Monitoring step is done, counting up the number of timeouts...", stepName)
                    numTimeouts = 0
                    for configRow in config.rows:
                        if not configRow.enabled:
                            continue;
                        
                        logger.tracef("(%s) checking row whose status is: %s", stepName, configRow.status)

                        targetRecipeDataId = configRow.targetRecipeDataId
                        targetRecipeDataType = configRow.targetRecipeDataType
    
                        if configRow.status in [PV_ERROR, PV_WARNING, PV_BAD_NOT_CONSISTENT]:
                            numTimeouts = numTimeouts + 1
                            if string.upper(targetRecipeDataType) == OUTPUT:
                                ''' This could be redundant (and an unnecessary database transaction, I'm not sure how this could escape being set above. '''
                                s88SetFromId(targetRecipeDataId, targetRecipeDataType, SETPOINT_STATUS, SETPOINT_PROBLEM, database)
                            s88SetFromId(targetRecipeDataId, targetRecipeDataType, PV_MONITOR_STATUS, PV_ERROR, database)
    
                        s88SetFromId(targetRecipeDataId, targetRecipeDataType, PV_MONITOR_ACTIVE, 0, database)
                        
                    errorCountScope = getStepProperty(stepProperties, ERROR_COUNT_SCOPE)
                    errorCountKey = getStepProperty(stepProperties, ERROR_COUNT_KEY)
                    errorCountMode = getStepProperty(stepProperties, ERROR_COUNT_MODE)
                    
                    logger.tracef("(%s) Number of timeouts:  %s", stepName, str(numTimeouts))
                    
                    if errorCountScope == CHART_SCOPE:
                        logger.tracef("(%s) Setting a chart scope error counter for a PV monitor step...", stepName)
                        if errorCountMode == COUNT_ABSOLUTE:
                            chartScope[errorCountKey] = numTimeouts
                        else:
                            cnt = chartScope[errorCountKey]
                            chartScope[errorCountKey] = cnt + numTimeouts
                    
                    elif errorCountScope == STEP_SCOPE:
                        ''' For stepScope counters the mode is implicitly incremental because the data is transient '''
                        logger.tracef("(%s) Setting a step scope error counter for a PV monitor step...", stepName)
                        stepScope[errorCountKey] = numTimeouts
                    
                    elif errorCountScope in [LOCAL_SCOPE, PRIOR_SCOPE, SUPERIOR_SCOPE, PHASE_SCOPE, OPERATION_SCOPE, GLOBAL_SCOPE]:
                        logger.tracef("(%s) Setting a recipe data scope (%s) error counter for a PV monitor step...", stepName, errorCountScope)
                        if errorCountMode == COUNT_ABSOLUTE:
                            s88Set(chartScope, stepScope, errorCountKey + ".Value", numTimeouts, errorCountScope)
                        else:
                            cnt = s88Get(chartScope, stepScope, errorCountKey + ".Value", errorCountScope)
                            s88Set(chartScope, stepScope, errorCountKey + ".Value", numTimeouts + cnt, errorCountScope)
    
                    logger.infof("(%s) there were %d PV monitoring timeouts!", stepName, numTimeouts)
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in monitorPV.py', logger)
    finally:
        # do cleanup here
        pass
    
    if complete:
        logger.info("** (%s) PV Monitoring is done! **" % (stepName))
        
    return complete