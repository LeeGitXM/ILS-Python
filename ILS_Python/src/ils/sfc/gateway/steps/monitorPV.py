'''
Created on Dec 17, 2015

@author: rforbes
'''

import system, string
from java.util import Date 
from ils.sfc.gateway.api import getIsolationMode, getProviderName, getDatabaseName, getChartLogger, handleUnexpectedGatewayError, \
    getStepProperty, compareValueToTarget, compareStringValueToTarget, postToQueue
from system.ils.sfc import getPVMonitorConfig
from ils.sfc.gateway.downloads import handleTimer, getElapsedMinutes
from ils.io.api import getMonitoredTagPath
from ils.io.util import stripProvider
from ils.common.cast import determineType

from ils.sfc.common.util import callMethodWithParams
from ils.sfc.recipeData.api import s88Get, s88Set, s88GetStep, s88GetRecipeDataId, s88GetRecipeDataIdFromStep, s88GetFromId, s88SetFromId
from ils.sfc.common.constants import TIMER_SET, TIMER_KEY, TIMER_LOCATION, ACTIVATION_CALLBACK, \
    START_TIMER, PAUSE_TIMER, RESUME_TIMER,  VALUE, SETPOINT, RECIPE, \
    STEP_SUCCESS, STEP_FAILURE, DOWNLOAD, TAG, \
    DATA_LOCATION, DOWNLOAD_STATUS, IMMEDIATE, KEY, MONITOR, MONITORING, STRATEGY, \
    RECIPE_LOCATION, PV_MONITOR_ACTIVE, PV_MONITOR_CONFIG, PV_VALUE, STATIC, NO_LIMIT, WAIT, \
    DEACTIVATED, PAUSED, RESUMED, \
    ERROR_COUNT_SCOPE, ERROR_COUNT_KEY, ERROR_COUNT_MODE, COUNT_ABSOLUTE, \
    LOCAL_SCOPE, PRIOR_SCOPE, SUPERIOR_SCOPE, PHASE_SCOPE, OPERATION_SCOPE, GLOBAL_SCOPE, CHART_SCOPE, STEP_SCOPE, REFERENCE_SCOPE, \
    NAME, PV_MONITOR_STATUS, PV_MONITORING, PV_WARNING, PV_OK_NOT_PERSISTENT, PV_OK, \
    PV_BAD_NOT_CONSISTENT, PV_ERROR, SETPOINT_STATUS, SETPOINT_PROBLEM, WATCH
from ils.sfc.recipeData.constants import TIMER, OUTPUT

from ils.sfc.common.constants import MSG_STATUS_INFO, MSG_STATUS_WARNING, MSG_STATUS_ERROR

NUMERIC_DATA_TYPE = "Numeric"
STRING_DATA_TYPE = "String"
BOOLEAN_DATA_TYPE = "Boolean"

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
        log = getChartLogger(chartScope)
        stepScope['tooltip'] = ""
        
        # This does not initially exist in the step scope dictionary, so we will get a value of False
        initialized = stepScope.get(INITIALIZED, False)   
        
        log.trace("In monitorPV.activate(), step: %s, state: %s, recipe location: %s, initialized: %s..." % (str(stepName), str(state), str(recipeLocation), str(initialized)))

        # Everything will have the same tag provider - check isolation mode and get the provider
        isolationMode = getIsolationMode(chartScope)
        providerName = getProviderName(chartScope)
        database = getDatabaseName(chartScope)
        
        recipeDataLocation = getStepProperty(stepProperties, RECIPE_LOCATION)
        if recipeDataLocation != REFERENCE_SCOPE:
            targetStepUUID, stepName, keyAndAttribute = s88GetStep(chartScope, stepScope, recipeDataLocation, "", database)

        # This does not initially exist in the step scope dictionary, so we will get a value of False
        initialized = stepScope.get(INITIALIZED, False)   
        if state == DEACTIVATED:
            log.trace("*** A deactivate has been detected ***")
            complete=True
        elif state == PAUSED:
            log.trace("The PV Monitor was paused")
            timerRecipeDataId = stepScope["timerRecipeDataId"]
            handleTimer(timerRecipeDataId, PAUSE_TIMER, log, database)
        elif state == RESUMED:
            log.trace("The PV Monitor was resumed")
            timerRecipeDataId = stepScope["timerRecipeDataId"]
            handleTimer(timerRecipeDataId, RESUME_TIMER, log, database)
        else:
            if not initialized:
                log.info("...initializing PV Monitor step %s ..." % (stepName))
                stepScope[INITIALIZED] = True
                stepScope["workDone"] = False
                
                timerLocation = getStepProperty(stepProperties, TIMER_LOCATION)
                timerKey = getStepProperty(stepProperties, TIMER_KEY)
                timerRecipeDataId, timerRecipeDataType = s88GetRecipeDataId(chartScope, stepScope, timerKey, timerLocation)
                stepScope["timerRecipeDataId"] = timerRecipeDataId
                log.tracef("The timer recipe data id is: %d using %s - %s", timerRecipeDataId, timerLocation, timerKey)
    
                configJson =  getStepProperty(stepProperties, PV_MONITOR_CONFIG)
                config = getPVMonitorConfig(configJson)
    
                # initialize each input
                maxPersistence = 0
                monitorActiveCount = 0
                watchOnly = True
                
                for configRow in config.rows:
                    log.tracef("----------------------")
                    log.trace("PV Key: %s - Target Type: %s - Target Name: %s - Strategy: %s - Deadtime: %s, Persistence: %s, tolerance: %s" % 
                                 (configRow.pvKey, configRow.targetType, configRow.targetNameIdOrValue, configRow.strategy, str(configRow.deadTime), str(configRow.persistence), str(configRow.tolerance)))

                    if recipeDataLocation == REFERENCE_SCOPE:
                        log.trace("...dereferencing a config row for the value...")
                        targetStepUUID, stepName, keyAndAttribute = s88GetStep(chartScope, stepScope, recipeDataLocation, configRow.pvKey, database)
                        pvRecipeDataId, pvRecipeDataType = s88GetRecipeDataIdFromStep(targetStepUUID, keyAndAttribute, database)
                        log.tracef("...Target Step: %s, stepName: %s, keyAndAttribute: %s", targetStepUUID, stepName, keyAndAttribute)
                    else:
                        pvRecipeDataId, pvRecipeDataType = s88GetRecipeDataIdFromStep(targetStepUUID, configRow.pvKey, database)
                    
                    ''' Read the PV now, before the monitoring phase starts, in order to determine that data type. ''' 
                    tagPath = getMonitoredTagPath(pvRecipeDataId, pvRecipeDataType, providerName, database)
                    qv = system.tag.read(tagPath)
                    valueType, val = determineType(qv.value)
                    log.tracef("  The current PV for %s is: %s-%s, the value type is: %s", tagPath, str(qv.value), str(qv.quality), valueType)
                        
                    configRow.status = MONITORING
                    configRow.pvRecipeDataId = pvRecipeDataId
                    configRow.pvRecipeDataType = pvRecipeDataType
                    
                    if configRow.strategy == MONITOR:
                        watchOnly = False
                        
                    '''
                    If we're just reading for display purposes (WATCH strategy), we're done with this row.
                    Do the minimum amount of configuration to facilitate the watch.
                    '''
                    if configRow.strategy != MONITOR:
                        log.tracef('  ...skipping target setup because the strategy is WATCH!')
                        configRow.targetRecipeDataType = pvRecipeDataType
                        configRow.targetRecipeDataId = pvRecipeDataId
                        
                        log.tracef("   ...initializing recipe data with id %d", pvRecipeDataId)
                        s88SetFromId(pvRecipeDataId, pvRecipeDataType, PV_VALUE, "Null", database)
                        s88SetFromId(pvRecipeDataId, pvRecipeDataType, PV_MONITOR_STATUS, PV_MONITORING, database)
                        s88SetFromId(pvRecipeDataId, pvRecipeDataType, PV_MONITOR_ACTIVE, True, database)
                        
                        # I'm not sure if we SHOULD use output in watch mode, but I guess if we can someone will
                        if pvRecipeDataType == OUTPUT:
                            s88SetFromId(pvRecipeDataId, pvRecipeDataType, SETPOINT_STATUS, "", database)
                        
                        ''' Even though we are watching this item we need to read the pv now so that we can establish the data type '''
                        tagPath = getMonitoredTagPath(pvRecipeDataId, pvRecipeDataType, providerName, database)
                        qv = system.tag.read(tagPath)
                        
                        log.tracef("Reading initial value to determine the type from <%s> value: %s", tagPath, str(qv))
                        
                        valueType, val = determineType(qv.value)
                        if valueType in ["Float", "Integer"]:
                            configRow.dataType = NUMERIC_DATA_TYPE
                        elif valueType in ["Boolean"]:
                            configRow.dataType = BOOLEAN_DATA_TYPE
                        else:
                            configRow.dataType = STRING_DATA_TYPE
        
                        log.tracef("...valueType: %s, dataType: %s", valueType, configRow.dataType)
                        continue
                    '''
                    This is a little clever - the type of the target determines where we will store the results.  These results are used by the 
                    download GUI block.  The target of a PV monitoring  
                    block can be just about anything.  If the target is an OUTPUT - then write results there, if the target is anything else then store the 
                    results in the INPUT.
                    '''
                    targetType = configRow.targetType
                    if targetType == SETPOINT:
                        targetKey = configRow.targetNameIdOrValue
                    else:
                        targetKey = configRow.pvKey
                        
                    log.trace(" ...Target Type: %s - Target Key: %s" % (targetType, targetKey))
                    
                    if recipeDataLocation == REFERENCE_SCOPE:
                        log.trace("...dereferencing a config row for the target...")
                        stepUUID, stepName, targetKey = s88GetStep(chartScope, stepScope, recipeDataLocation, targetKey, database)
                        targetRecipeDataId, targetRecipeDataType = s88GetRecipeDataIdFromStep(stepUUID, targetKey, database)
                        log.tracef("...Target Step: %s, stepName: %s, targetKey: %s, targetRecipeDataId: %s", targetStepUUID, stepName, targetKey, str(targetRecipeDataId))
                    else:    
                        targetRecipeDataId, targetRecipeDataType = s88GetRecipeDataIdFromStep(targetStepUUID, targetKey, database)
        
                    configRow.targetRecipeDataId = targetRecipeDataId
                    configRow.targetRecipeDataType = targetRecipeDataType
                    log.trace(" ...Target Recipe Id: %d - Recipe Data Type: %s" % (targetRecipeDataId, targetRecipeDataType))
                    
                    if string.upper(targetRecipeDataType) == "OUTPUT":
                        download = s88GetFromId(targetRecipeDataId, targetRecipeDataType, DOWNLOAD, database)
                        downloadMode =  configRow.download
                        log.tracef("The download flag is: %s and the PV monitor download mode is: %s", str(download), downloadMode) 
                        if not(download):
                            log.trace("---skipping this row because it is an output that is not slated to be downloaded---")
                            configRow.enabled = False  # Override the enabled flag in a transient way
                            pass
                    
                    if configRow.enabled:
                        log.tracef(" ...PV Recipe Id: %d - Recipe Data Type: %s", pvRecipeDataId, pvRecipeDataType)
    
                        configRow.lastPV = -999999.99
                        configRow.lastStatus = "UNKNOWN"
                        
                        if targetType == SETPOINT:
                            s88SetFromId(targetRecipeDataId, targetRecipeDataType, PV_VALUE, "Null", database)
                            s88SetFromId(targetRecipeDataId, targetRecipeDataType, SETPOINT_STATUS, "", database)
    
                        s88SetFromId(targetRecipeDataId, targetRecipeDataType, PV_MONITOR_STATUS, PV_MONITORING, database)
                        s88SetFromId(targetRecipeDataId, targetRecipeDataType, PV_MONITOR_ACTIVE, True, database)
        
                        ''' I'm not sure if this should look at the PV or the target?? '''
                        configRow.isOutput = (targetRecipeDataType in ['Output', 'Output Ramp'])
    
                        configRow.isDownloaded = False
                        configRow.persistenceOK = False
                        configRow.inToleranceTime = 0
                        configRow.outToleranceTime = Date().getTime()
                        
                        monitorActiveCount = monitorActiveCount + 1
                        
                        if configRow.persistence > maxPersistence:
                            maxPersistence = configRow.persistence
                            
                        '''
                        We initially assumed that the target value would not change, so we got it originally. This assumption 
                        changed in 5/2002.  It is reasonable that the setpoint is calculated later in the process after an 
                        initial complement of setpoints are written and some monitoring performed and the setpoint is recalculated.
                        So the setpoint is read initially, but it should also be updated as we monitor.
                        (This is storing the target into the config structure not recipe data)
                        The constants are all lower case so make this case insensitive by converting to lowercase
                        '''
                        targetType = string.lower(configRow.targetType)
                        configRow.targetType = targetType
                        
                        configRow, targetValue = getTargetValue(chartScope, stepScope, targetType, targetRecipeDataId, targetRecipeDataType, recipeDataLocation, configRow, database, providerName, log)
                            
                        log.tracef("...the target value is: %s (value type: %s)", str(targetValue), valueType)


                log.tracef("Summarizing the configuration (watch only: %s)", str(watchOnly))
                
                # Put the initialized config data back into step scope for the next iteration
                stepScope[PV_MONITOR_CONFIG] = config
                stepScope[MONITOR_ACTIVE_COUNT] = monitorActiveCount
                stepScope[PERSISTENCE_PENDING] = False
                stepScope[MAX_PERSISTENCE] = maxPersistence
                stepScope[WATCH_ONLY] = watchOnly
                
                durationStrategy = getStepProperty(stepProperties, STRATEGY)
                log.tracef("The duration strategy is: %s", durationStrategy)
                
                if durationStrategy == STATIC:
                    timeLimitMin = getStepProperty(stepProperties, VALUE)
                elif durationStrategy == NO_LIMIT:
                    timeLimitMin = -1.0
                else:
                    durationKey = getStepProperty(stepProperties, KEY)
                    log.tracef("Duration Key: <%s> (before)", durationKey)
                    # It is assumed that the duration limit is simple recipe data and must have attribute ".value"
                    if durationKey.rfind(".value") >= 0:
                        durationKey = durationKey[:durationKey.rfind(".value")]
                    log.tracef("Duration Key: <%s> (after)", durationKey)
                    
                    durationLocation = getStepProperty(stepProperties, DATA_LOCATION)
                    log.tracef("The duration location and key is: %s.%s", durationLocation, durationKey)
                    timeLimitMin = s88Get(chartScope, stepScope, durationKey + ".value", durationLocation)
                    
                stepScope["timeLimitMinutes"] = timeLimitMin
                
                # Look for a custom activation callback
                activationCallback = getStepProperty(stepProperties, ACTIVATION_CALLBACK)
                log.tracef("The activation callback is: %s", activationCallback)
                if activationCallback <> "":
                    log.tracef("Calling custom activationCallback: <%s>", activationCallback)
    
                    keys = ['scopeContext', 'stepProperties', 'config']
                    values = [scopeContext, stepProperties, config]
                    try:
                        config = callMethodWithParams(activationCallback, keys, values)
                        stepScope[PV_MONITOR_CONFIG] = config
                    except Exception, e:
                        try:
                            cause = e.getCause()
                            errMsg = "Error calling activation callback %s: %s" % (activationCallback, cause.getMessage())
                        except:
                            errMsg = "Error calling activation callback (2) %s: %s" % (activationCallback, str(e))

                        log.errorf(errMsg)

                # This will clear and/or set the timer if the block is configured to do so               
                startTimer = getStepProperty(stepProperties, TIMER_SET)
                if startTimer:
                    handleTimer(timerRecipeDataId, START_TIMER, log, database)
                    stepScope["timerStarted"] = True
                else:
                    stepScope["timerStarted"] = False

                ''' If the step is not in watch only mode AND there are no rows configured to monitor, then the block is done, even though the block is probably misconfigured. '''
                if not(watchOnly)  and monitorActiveCount <= 0:
                    log.warn("PV Monitoring block is not configured to monitor anything")
                    complete = True

                log.tracef("Completed the initialization phase of PV monitoring")
            
            else:
                log.trace("---(%s) monitoring---" % (stepName))
    
                timerRecipeDataId = stepScope["timerRecipeDataId"]
                timerStarted = stepScope["timerStarted"]
                timeLimitMin = stepScope["timeLimitMinutes"]
                    
                log.tracef("(%s) PV Monitor time limit minutes: %s", stepName, str(timeLimitMin))
                    
                config = stepScope[PV_MONITOR_CONFIG]
                watchOnly = stepScope[WATCH_ONLY]
                log.tracef("(%s) Watch only: %s", stepName, str(watchOnly))
            
                # Wait until the timer starts before doing anything, once the timer has been started, we don't need to query it again.
                # It is possible that this block starts before some other block starts the timer
                if not(timerStarted):
                    startTime=s88GetFromId(timerRecipeDataId, TIMER, "StartTime", database)
                    if startTime == None:
                        log.tracef("(%s) waiting for the timer to start...", stepName)
                        complete = False
                        return complete
                    stepScope["timerStarted"] = True
                
                elapsedMinutes = s88GetFromId(timerRecipeDataId, TIMER, "ELAPSEDMINUTES", database)
                persistencePending = stepScope[PERSISTENCE_PENDING]
                monitorActiveCount = stepScope[MONITOR_ACTIVE_COUNT]
                maxPersistence = stepScope[MAX_PERSISTENCE]
                
                if timeLimitMin > 0:
                    extendedDuration = timeLimitMin + maxPersistence # extra time allowed for persistence checks
                else:
                    extendedDuration = elapsedMinutes + 1.0
                
                log.tracef("  monitorActiveCount: %s, timeLimitMin: %s, elapsedMinutes: %s, persistencePending: %s, extendedDuration: %s", 
                              str(monitorActiveCount), str(), str(elapsedMinutes), str(persistencePending), str(extendedDuration))
                if monitorActiveCount > 0 and ((timeLimitMin < 0) or (elapsedMinutes < timeLimitMin) or (persistencePending and elapsedMinutes < extendedDuration)) or watchOnly:
                    log.tracef("(%s) Starting a PV monitor pass, (elapsed minutes: %s) ...", stepName, str(elapsedMinutes))
           
                    monitorActiveCount = 0
                    persistencePending = False
                    for configRow in config.rows:
                        if not configRow.enabled:
                            continue;
                        
                        targetRecipeDataId = configRow.targetRecipeDataId
                        targetRecipeDataType = configRow.targetRecipeDataType
                        pvRecipeDataId = configRow.pvRecipeDataId
                        pvRecipeDataType = configRow.pvRecipeDataType
                        
                        ''' Here are the new row properties supported to handle Strings '''                    
                        dataType = configRow.dataType
                        numericTargetValue = configRow.targetValue
                        stringTargetValue = configRow.targetStringValue
                        log.tracef("%s - %s - %s", dataType, str(numericTargetValue), str(stringTargetValue))
                        
                        # SUCCESS is a terminal state - once the criteria is met stop monitoring that PV
                        if configRow.status == PV_OK:
                            continue
                        
                        log.tracef('(%s) PV Key: %s, Target type: %s, Recipe Data Type: %s, Target: %s, Strategy: %s, Deadtime: %s, Persistence: %s, tolerance: %s', 
                                stepName, configRow.pvKey, configRow.targetType, targetRecipeDataType, configRow.targetNameIdOrValue, configRow.strategy, str(configRow.deadTime), str(configRow.persistence), str(configRow.tolerance))
 
                        '''
                        This is a little clever - the type of the target determines where we will store the results.  These results are used by the 
                        download GUI block.  It appears that the PV of a PV monitoring block is always INPUT recipe data.  The target of a PV monitoring  
                        block can be just about anything.  If the target is an OUTPUT - then write results there, if the target is anything else then store the 
                        results in the INPUT.  (I'm not sure this comment is correct! 5/8/19)
                        '''
                        targetType = configRow.targetType
                        if targetType == SETPOINT:
                            targetKey = configRow.targetNameIdOrValue
                        else:
                            targetKey = configRow.pvKey
    
                        monitorActiveCount = monitorActiveCount + 1
                        #TODO: how are we supposed to know about a download unless we have an Output??
                        if configRow.isOutput and not configRow.isDownloaded:
                            log.tracef("  (%s) The item is an output and it hasn't been downloaded...", stepName)
                            downloadStatus = s88GetFromId(targetRecipeDataId, targetRecipeDataType, DOWNLOAD_STATUS, database)
                            configRow.isDownloaded = (downloadStatus == STEP_SUCCESS or downloadStatus == STEP_FAILURE)
                            if configRow.isDownloaded:
                                log.tracef("  (%s) the download just completed!", stepName)
                                configRow.downloadTime = elapsedMinutes
                                configRow.outToleranceTime = 0.0
                                configRow.inToleranceTime = 0.0
                                
                            ''' Check for an updated target value if we have not already downloaded it (5/5/2022) '''
                            configRow, targetValue = getTargetValue(chartScope, stepScope, targetType, targetRecipeDataId, targetRecipeDataType, recipeDataLocation, configRow, database, providerName, log)
                            log.tracef("Current target value: %s", str(targetValue))
            
                        # Display the PVs as soon as the block starts running, even before the SP has been written
                        tagPath = getMonitoredTagPath(pvRecipeDataId, pvRecipeDataType, providerName, database)
                        qv = system.tag.read(tagPath)
                                                
                        if not(qv.quality.isGood()):
                            log.warnf("  (%s) The monitored value for %s is bad: %s-%s", stepName, tagPath, str(qv.value), str(qv.quality))
                            continue
    
                        pv=qv.value
    
                        if dataType == NUMERIC_DATA_TYPE:
                            log.tracef("  (%s) The current PV is: %s-%s (%s) (last PV: %s)", stepName, str(qv.value), str(qv.quality), tagPath, str(configRow.lastPV))
                        elif dataType == STRING_DATA_TYPE:
                            pv = pv.rstrip()
                            log.tracef("  (%s) The current PV (string) is: %s-%s (%s) (last PV: %s)", stepName, str(qv.value), str(qv.quality), tagPath, str(configRow.lastStringPV))
                        
                        if dataType == NUMERIC_DATA_TYPE and pv != configRow.lastPV:
                            log.tracef("  Updating the PV recipe for a changed numeric value (%s - %s - pvValue)...", str(targetRecipeDataId), targetRecipeDataType)
                            s88SetFromId(targetRecipeDataId, targetRecipeDataType, "pvValue", pv, database)
                            configRow.lastPV = pv
                        elif dataType == STRING_DATA_TYPE and pv != configRow.lastStringPV:
                            log.tracef("  Updating the PV recipe for a changed string value (%s - %s - pvValue)...", str(targetRecipeDataId), targetRecipeDataType)
                            s88SetFromId(targetRecipeDataId, targetRecipeDataType, "pvValue", pv, database)
                            configRow.lastStringPV = pv
                        else:
                            log.tracef("  Skipping update of pv because it has not changed")
    
                        # If we are configured to wait for the download and it hasn't been downloaded, then don't start to monitor
                        if configRow.download == WAIT and not configRow.isDownloaded:
                            log.tracef("  (%s) skipping because this output is designated to wait for a download and it has not been downloaded", stepName)
                            continue
                       
                        # if we're just reading for display purposes, we're done with this row
                        if configRow.strategy != MONITOR:
                            log.tracef('  (%s) skipping because the strategy is NOT monitor!', stepName)
                            continue
                        
                        target=configRow.targetValue
                        toleranceType=configRow.toleranceType
                        if toleranceType == None:
                            toleranceType = "Abs"
                        tolerance=configRow.tolerance
                        limitType=configRow.limits

                        # check dead time - assume that immediate monitors coincide with starting the timer.      
                        if configRow.download == IMMEDIATE:
                            log.tracef("  (%s) Using the timer elapsed minutes (%s) to check if the dead time (%s) has been exceeded.", stepName, str(elapsedMinutes), str(configRow.deadTime) )
                            deadTimeExceeded = elapsedMinutes > configRow.deadTime
                        else:
                            log.tracef("  (%s) Setting the reference time as the download time", stepName)
                            referenceTime = configRow.downloadTime
                            deadTimeExceeded = (elapsedMinutes - referenceTime) > configRow.deadTime 

                        log.tracef("  (%s) Checking if the dead time has been exceeded: %s", stepName, str(deadTimeExceeded))

                        # Check if the value is within the limits
                        strippedTagpath = stripProvider(tagPath)

                        if stepScope["tooltip"] == "":
                            stepScope['tooltip'] = "<HTML>Monitoring:<br>     %s, value: %s, target: %s" % (strippedTagpath, str(pv), str(target))
                        else:
                            stepScope['tooltip'] = "%s<br>     %s, value: %s, target: %s" % (stepScope["tooltip"], strippedTagpath, str(pv), str(target))

                        if dataType == STRING_DATA_TYPE:
                            valueOk, txt = compareStringValueToTarget(pv,  configRow.targetStringValue , log)
                        else:
                            valueOk, txt = compareValueToTarget(pv, target, tolerance, limitType, toleranceType, log)
                        
                        # check persistence and consistency
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
                            
                            if isPersistent:
                                log.tracef("  --- The value is persistent - this meets all monitoring requirements for this output ---")
                                configRow.status = PV_OK
                                s88SetFromId(targetRecipeDataId, targetRecipeDataType, PV_MONITOR_ACTIVE, False, database)
                                txt = "The PV of %s reached the target (PV = %s, SP = %s) +/- %s %s at %.2f min (dead time = %s)" % (strippedTagpath, str(pv), str(target), str(tolerance),  string.lower(toleranceType), elapsedMinutes, str(configRow.deadTime))
                                postToQueue(chartScope, MSG_STATUS_INFO, txt)
                            else:
                                configRow.status = PV_OK_NOT_PERSISTENT
                                persistencePending = True
                        else:
                            configRow.inToleranceTime = 0
                            isPersistent = False
                            
                            if deadTimeExceeded:
                                configRow.status = PV_ERROR
                                
                            elif configRow.status in [PV_OK, PV_OK_NOT_PERSISTENT]:
                                log.tracef("  the pv was OK and now isn't")
                                if configRow.outToleranceTime != 0:
                                    outToleranceTime=long(configRow.outToleranceTime)
                                    if getElapsedMinutes(Date(long(outToleranceTime))) > configRow.consistency:
                                        configRow.status = PV_WARNING
                                    else:
                                        configRow.status = PV_BAD_NOT_CONSISTENT
                                        
                                else:
                                    log.trace("The PV just went out of tolerance")
                                    isConsistentlyOutOfTolerance = False
                                    configRow.outToleranceTime = Date().getTime()
                                    
                            elif configRow.status in [MONITORING]:
                                configRow.status = PV_WARNING
                                
                            else:
                                log.tracef("  IN THE ELSE")
                               
            
                        if string.upper(configRow.status) == string.upper(PV_ERROR) and string.upper(targetRecipeDataType) == string.upper(OUTPUT):
                            # Set the setpoint status to PROBLEM - this cannot be reset
                            log.tracef("  Setting the setpoint status for a %s", targetRecipeDataType)
                            s88SetFromId(targetRecipeDataId, targetRecipeDataType, SETPOINT_STATUS, SETPOINT_PROBLEM, database)
            
                        log.tracef("  (%s) Status: %s", stepName, configRow.status)
                        if configRow.status != configRow.lastStatus:       
                            s88SetFromId(targetRecipeDataId, targetRecipeDataType, PV_MONITOR_STATUS, configRow.status, database)
                            configRow.lastStatus = configRow.status
                
                log.tracef("(%s) Checking end conditions...", stepName)
                if monitorActiveCount == 0:
                    log.infof("(%s) The PV monitor is finished because there is nothing left to monitor...", stepName)
                    complete = True
                
                # If the maximum time has been exceeded then count how many items did not complete their monitoring, aka Timed-Out 
                '''
                This used to include a check where it would ignore the time limit if it was just watching but that doesn't seem to make much sense - Pete 5/7/19
                if ((elapsedMinutes > timeLimitMin) or (persistencePending and elapsedMinutes > extendedDuration)) and not(watchOnly):
                '''
                if ((elapsedMinutes > timeLimitMin and timeLimitMin > 0) or (persistencePending and elapsedMinutes > extendedDuration)):
                    log.infof("(%s) The PV monitor is finished because the max run time has been reached...", stepName)
                    complete = True
                
                if complete:
                    log.tracef("(%s) The PV Monitoring step is done, counting up the number of timeouts...", stepName)
                    numTimeouts = 0
                    for configRow in config.rows:
                        if not configRow.enabled:
                            continue;
                        
                        log.tracef("(%s) checking row whose status is: %s", stepName, configRow.status)

                        ''' We got all of these values up above, but we are going through the structure again '''
                        targetRecipeDataId = configRow.targetRecipeDataId
                        targetRecipeDataType = configRow.targetRecipeDataType
                        
                        pvRecipeDataId = configRow.pvRecipeDataId
                        pvRecipeDataType = configRow.pvRecipeDataType
                        tagPath = getMonitoredTagPath(pvRecipeDataId, pvRecipeDataType, providerName, database)
                        strippedTagpath = stripProvider(tagPath)

                        qv = system.tag.read(tagPath)
                        pv=qv.value
                        target=configRow.targetValue
                        toleranceType=configRow.toleranceType
                        if toleranceType == None:
                            toleranceType = "Abs"
                        tolerance=configRow.tolerance
    
                        if configRow.status in [PV_ERROR, PV_WARNING, PV_BAD_NOT_CONSISTENT]:
                            numTimeouts = numTimeouts + 1
                            if string.upper(targetRecipeDataType) == OUTPUT:
                                ''' This could be redundant (and an unnecessary database transaction, I'm not sure how this could escape being set above. '''
                                s88SetFromId(targetRecipeDataId, targetRecipeDataType, SETPOINT_STATUS, SETPOINT_PROBLEM, database)
                            s88SetFromId(targetRecipeDataId, targetRecipeDataType, PV_MONITOR_STATUS, PV_ERROR, database)
                            
                            if configRow.status == PV_ERROR:
                                txt = "The PV of %s has not reached the target (PV = %s, SP = %s) +/- %s %s at %.2f min (dead time = %s)" % (strippedTagpath, str(pv), str(target), str(tolerance),  string.lower(toleranceType), elapsedMinutes, str(configRow.deadTime))
                                postToQueue(chartScope, MSG_STATUS_WARNING, txt)
                                
                            elif configRow.status == PV_WARNING:
                                txt = "The PV of %s has not reached the target (PV = %s, SP = %s) +/- %s %s at %.2fs min (dead time = %s)" % (strippedTagpath, str(pv), str(target), str(tolerance),  string.lower(toleranceType), elapsedMinutes, str(configRow.deadTime))
                                postToQueue(chartScope, MSG_STATUS_WARNING, txt)
                                
                            elif configRow.status == PV_BAD_NOT_CONSISTENT:
                                txt = "The PV of %s has not consistently reached the target (PV = %s, SP = %s) +/- %s %s at %.2f min (dead time = %s)" % (strippedTagpath, str(pv), str(target), str(tolerance),  string.lower(toleranceType), elapsedMinutes, str(configRow.deadTime))
                                postToQueue(chartScope, MSG_STATUS_WARNING, txt)
                                
                        elif configRow.status == PV_OK_NOT_PERSISTENT:
                            ''' I'm not sure why we don't treat this as a timeout, I guess because the PV is OK, but the block ended before we met the persistence criteria. '''
                            txt = "The PV of %s reached the target (PV = %s, SP = %s) +/- %s %s at %.2f min (dead time = %s) but did not meet the %s min persistence requirement." % (strippedTagpath, str(pv), str(target), str(tolerance),  string.lower(toleranceType), elapsedMinutes, str(configRow.deadTime), str(configRow.persistence))
                            postToQueue(chartScope, MSG_STATUS_INFO, txt)
                            
    
                        s88SetFromId(targetRecipeDataId, targetRecipeDataType, PV_MONITOR_ACTIVE, 0, database)
                        
                    errorCountScope = getStepProperty(stepProperties, ERROR_COUNT_SCOPE)
                    errorCountKey = getStepProperty(stepProperties, ERROR_COUNT_KEY)
                    errorCountMode = getStepProperty(stepProperties, ERROR_COUNT_MODE)
                    
                    log.tracef("(%s) Number of timeouts:  %s", stepName, str(numTimeouts))
                    
                    if errorCountScope == CHART_SCOPE:
                        log.tracef("(%s) Setting a chart scope error counter for a PV monitor step...", stepName)
                        if errorCountMode == COUNT_ABSOLUTE:
                            chartScope[errorCountKey] = numTimeouts
                        else:
                            cnt = chartScope[errorCountKey]
                            chartScope[errorCountKey] = cnt + numTimeouts
                    
                    elif errorCountScope == STEP_SCOPE:
                        ''' For stepScope counters the mode is implicitly incremental because the data is transient '''
                        log.tracef("(%s) Setting a step scope error counter for a PV monitor step...", stepName)
                        stepScope[errorCountKey] = numTimeouts
                    
                    elif errorCountScope in [LOCAL_SCOPE, PRIOR_SCOPE, SUPERIOR_SCOPE, PHASE_SCOPE, OPERATION_SCOPE, GLOBAL_SCOPE]:
                        log.tracef("(%s) Setting a recipe data scope (%s) error counter for a PV monitor step...", stepName, errorCountScope)
                        if errorCountMode == COUNT_ABSOLUTE:
                            s88Set(chartScope, stepScope, errorCountKey + ".Value", numTimeouts, errorCountScope)
                        else:
                            cnt = s88Get(chartScope, stepScope, errorCountKey + ".Value", errorCountScope)
                            s88Set(chartScope, stepScope, errorCountKey + ".Value", numTimeouts + cnt, errorCountScope)
    
                    log.infof("(%s) there were %d PV monitoring timeouts!", stepName, numTimeouts)
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in monitorPV.py', log)
    finally:
        # do cleanup here
        pass
    
    if complete:
        log.info(" (%s) PV Monitoring is done!" % (stepName))
        
    return complete

def getTargetValue(chartScope, stepScope, targetType, targetRecipeDataId, targetRecipeDataType, recipeDataLocation, configRow, database, providerName, log):
    if targetType == SETPOINT:
        # This means that the recipe data is an OUTPUT recipe data that points to some part of a controller I/O,
        # the recipe data will tell what
        log.tracef("Getting the target value using SETPOINT strategy...")
        targetKey = configRow.targetNameIdOrValue  # This is a different targetKey than we used above when we got the recipe data id
        tagPath =    s88GetFromId(targetRecipeDataId, targetRecipeDataType, 'Tag', database)
        outputType = s88GetFromId(targetRecipeDataId, targetRecipeDataType, 'OutputType', database)
        log.tracef("...Tagpath: %s, Output Type: %s", tagPath, outputType)
        log.tracef("get from id target id: %s target type: %s", targetRecipeDataId, targetRecipeDataType)
        targetValue = s88GetFromId(targetRecipeDataId, targetRecipeDataType, 'OutputValue', database)
        
    elif targetType == VALUE:
        # The target value is hard coded in the config data
        valueType, val = determineType(configRow.targetNameIdOrValue)
        log.tracef("The datatype of the target value is: %s and the value is: %s", valueType, str(val))
        if valueType == 'String':
            targetValue = configRow.targetNameIdOrValue
        else:
            targetValue = float(configRow.targetNameIdOrValue)
    
    elif targetType == TAG:
        # Read the value from a tag
        qv = system.tag.read("[" + providerName + "]" + configRow.targetNameIdOrValue)
        targetValue = qv.value
    
    elif targetType == RECIPE:
        # This means that the target value will be in some property of the recipe data
        log.tracef("Getting the target value from Recipe key: %s-%s", recipeDataLocation, configRow.targetNameIdOrValue)
        targetValue = s88Get(chartScope, stepScope, configRow.targetNameIdOrValue, recipeDataLocation) 

    else:
        log.errorf("Unexpected target type: <%s>", targetType)
        targetValue = None
        
    valueType, val = determineType(targetValue)
    if valueType in ["Float", "Integer"]:
        configRow.targetValue = targetValue
        configRow.dataType = NUMERIC_DATA_TYPE
    else:
        configRow.targetStringValue = str(targetValue)
        configRow.dataType = STRING_DATA_TYPE
        
    return configRow, targetValue