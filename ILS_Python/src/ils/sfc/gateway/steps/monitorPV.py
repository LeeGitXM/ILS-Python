'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties, deactivate):
    '''see the G2 procedures S88-RECIPE-INPUT-DATA__S88-MONITOR-PV.txt and 
    S88-RECIPE-OUTPUT-DATA__S88-MONITOR-PV.txt'''
    from ils.sfc.gateway.util import getStepProperty, handleUnexpectedGatewayError
    from ils.sfc.gateway.api import getChartLogger, s88Get
    import system.tag
    
    from system.ils.sfc.common.Constants import PV_MONITOR_CONFIG, MONITOR, \
    IMMEDIATE, CLASS, DOWNLOAD_STATUS,  STEP_TIME,  RECIPE_LOCATION, VALUE, KEY, \
    DATA_LOCATION, PV_MONITOR_ACTIVE, PV_VALUE, STRATEGY, STATIC, TAG, RECIPE, SETPOINT,\
    MONITORING, WAIT, TIMEOUT
    
    from ils.sfc.common.constants import NUMBER_OF_TIMEOUTS, PV_MONITOR_STATUS, PV_MONITORING, PV_WARNING, PV_OK_NOT_PERSISTENT, PV_OK, \
    PV_BAD_NOT_CONSISTENT, PV_ERROR, SETPOINT_STATUS, SETPOINT_OK, SETPOINT_PROBLEM, \
    STEP_SUCCESS, STEP_FAILURE, SLEEP_INCREMENT
    
    import time
    from ils.sfc.common.util import getMinutesSince
    from ils.sfc.gateway.api import getIsolationMode
    from system.ils.sfc import getProviderName, getPVMonitorConfig
    from ils.sfc.gateway.downloads import handleTimer, getTimerStart
    from ils.sfc.gateway.recipe import RecipeData
    from ils.io.api import getMonitoredTagPath
    
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
        
        logger = getChartLogger(chartScope)
        logger.trace("+++++++++++++++++++++++++++")
        logger.info("In monitorPV.activate()...")
        
        # Everything will have the same tag provider - check isolation mode and get the provider
        isolationMode = getIsolationMode(chartScope)
        providerName = getProviderName(isolationMode)
    
        # This does not initially exist in the step scope dictionary, so we will get a value of False
        initialized = stepScope.get(INITIALIZED, False)   
        if deactivate:
            logger.trace("*** A deactivate has been detected ***")
            complete=True
        
        elif not initialized:
            logger.trace("...initializing...")
            stepScope[NUMBER_OF_TIMEOUTS] = 0
            stepScope[INITIALIZED]=True
            stepScope["workDone"]=False
            
            # Clear and/or start the timer
            handleTimer(chartScope, stepScope, stepProperties, logger)

            configJson =  getStepProperty(stepProperties, PV_MONITOR_CONFIG)
            config = getPVMonitorConfig(configJson)

            # initialize each input
            maxPersistence = 0
            logger.trace("...initializing PV monitor recipe data...")
            monitorActiveCount = 0
            for configRow in config.rows:
                logger.trace("PV Key: %s - Target Type: %s - Target Name: %s - Strategy: %s" % (configRow.pvKey, configRow.targetType, configRow.targetNameIdOrValue, configRow.strategy))
                configRow.status = MONITORING
                rd = RecipeData(chartScope, stepScope, recipeLocation, configRow.pvKey)
                print "The recipe data is: ", rd
                rd.set(PV_MONITOR_STATUS, PV_MONITORING)
                rd.set(SETPOINT_STATUS, SETPOINT_OK)
                rd.set(PV_MONITOR_ACTIVE, True)
                rd.set("advice", "Take two advil and call me in the morning")
#                rd.set(PV_VALUE, None)
                dataType = rd.get(CLASS)
                print "The data type is: ", dataType
                configRow.isOutput = (dataType == 'Output')
                configRow.isDownloaded = False
                configRow.persistenceOK = False
                configRow.inToleranceTime = 0
                configRow.outToleranceTime = time.time()
                monitorActiveCount = monitorActiveCount + 1
                
                if configRow.persistence > maxPersistence:
                    maxPersistence = configRow.persistence
                    
                # we assume the target value won't change, so we get it once:
                if configRow.targetType == SETPOINT:
                    configRow.targetValue = s88Get(chartScope, stepScope, configRow.targetNameIdOrValue + '/value', recipeLocation)
                elif configRow.targetType == VALUE:
                    configRow.targetValue = configRow.targetNameIdOrValue
                elif configRow.targetType == TAG:
                    qualVal = system.tag.read("[" + providerName + "]" + configRow.targetNameIdOrValue)
                    configRow.targetValue = qualVal.value
                elif configRow.targetType == RECIPE:
                    configRow.targetValue = s88Get(chartScope, stepScope, configRow.targetNameIdOrValue, recipeLocation)           
                
                logger.trace("...the target value is: %s" % (str(configRow.targetValue)))

            # Put the initialized config data back into step scope for the next iteration
            print "stashing configuration: ", config
            stepScope[PV_MONITOR_CONFIG] = config
            stepScope[MONITOR_ACTIVE_COUNT] = monitorActiveCount
            stepScope[PERSISTENCE_PENDING] = False
            stepScope[MAX_PERSISTENCE] = maxPersistence
            print "The initialized configuration is: ", config
            
            handleTimer(chartScope, stepScope, stepProperties, logger)
        
        else:    
            logger.trace("...starting to monitor...")
            
            durationLocation = getStepProperty(stepProperties, DATA_LOCATION)
            durationStrategy = getStepProperty(stepProperties, STRATEGY)
            if durationStrategy == STATIC:
                timeLimitMin = getStepProperty(stepProperties, VALUE) 
            else:
                durationKey = getStepProperty(stepProperties, KEY)
                timeLimitMin = s88Get(chartScope, stepScope, durationKey, durationLocation)
                
            logger.trace("   PV Monitor time limit strategy: %s - minutes: %s" % (durationStrategy, str(timeLimitMin)))
                
            config = stepScope[PV_MONITOR_CONFIG]
            print "Using configuration: ", config
        
            # Monitor for the specified period, possibly extended by persistence time
            timerStart=getTimerStart(chartScope, stepScope, stepProperties)
            elapsedMinutes = getMinutesSince(timerStart)
#            startTime = time.time()

            persistencePending = stepScope[PERSISTENCE_PENDING]
            monitorActiveCount = stepScope[MONITOR_ACTIVE_COUNT]
            maxPersistence = stepScope[MAX_PERSISTENCE]
            
            extendedDuration = timeLimitMin + maxPersistence # extra time allowed for persistence checks
            
            if monitorActiveCount > 0 and ((elapsedMinutes < timeLimitMin) or (persistencePending and elapsedMinutes < extendedDuration)):
                logger.trace("Starting a PV monitor pass...")
       
                monitorActiveCount = 0
                persistencePending = False
                for configRow in config.rows:
                    rd = RecipeData(chartScope, stepScope, recipeLocation, configRow.pvKey)
                    print "The recipe data is: ", rd
                    rd.set("errorCode", "This ain't no stinkin error")
                    if not configRow.enabled:
                        continue;
                    
                    # SUCCESS is a terminal state - once the criteria is met stop monitoring that PV
                    if configRow.status == PV_OK:
                        continue
                    
                    logger.trace('PV monitoring: %s' % (configRow.pvKey))
                    
                    monitorActiveCount = monitorActiveCount + 1
                    #TODO: how are we supposed to know about a download unless we have an Output??
                    if configRow.isOutput and not configRow.isDownloaded:
                        logger.trace("The item is an output and it hasn't been downloaded...")
                        downloadStatus = rd.get(DOWNLOAD_STATUS)
                        configRow.isDownloaded = (downloadStatus == STEP_SUCCESS or downloadStatus == STEP_FAILURE)
                        if configRow.isDownloaded:
                            logger.trace("...the download just completed!")
                            configRow.downloadTime = rd.get(STEP_TIME)
        
                    # Display the PVs as soon as the block starts running, even before the SP has been written
                    tagPath = getMonitoredTagPath(rd, providerName)
                    qv = system.tag.read(tagPath)
                    
                    logger.trace("The present qualified value for %s is: %s-%s" % (tagPath, str(qv.value), str(qv.quality)))
                    if not(qv.quality.isGood()):
                        logger.warn("The monitored value is bad: %s-%s" % (str(qv.value), str(qv.quality)))
                        continue

                    pv=qv.value
                    rd.set(PV_VALUE, pv)
                    print "...writing ", pv, " to the PV to the pvValue of the OUTPUT recipe data..."
        
                    # If we are configured to wait for the download and it hasn't been downloaded, then don't start to monitor
                    if configRow.download == WAIT and not configRow.isDownloaded:
                        logger.trace('   skipping because this output is designated to wait for a download and it has not been downloaded')
                        continue
                   
                    # if we're just reading for display purposes, we're done with this pvInput:
                    if configRow.strategy != MONITOR:
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
                            isPersistent = getMinutesSince(configRow.inToleranceTime) > configRow.persistence                    
                        else:
                            configRow.inToleranceTime = time.time()
                            if configRow.persistence > 0.0:
                                isPersistent = False
                            else:
                                isPersistent = True
                    else:
                        configRow.inToleranceTime = 0
                        isPersistent = False
                        if configRow.outToleranceTime != 0:
                            isConsistentlyOutOfTolerance = getMinutesSince(configRow.outToleranceTime) > configRow.consistency
                        else:
                            isConsistentlyOutOfTolerance = False
                            configRow.outToleranceTime = time.time()  
                            
                    # check dead time - assume that immediate writes coincide with starting the timer.      
                    if configRow.download == IMMEDIATE:
                        referenceTime = timerStart
                    else:
                        referenceTime = configRow.downloadTime
                    # print 'minutes since reference', getMinutesSince(referenceTime)
                    deadTimeExceeded = getMinutesSince(referenceTime) > configRow.deadTime 
                    # print '   pv', presentValue, 'target', configRow.targetValue, 'low limit',  configRow.lowLimit, 'high limit', configRow.highLimit   
                    # print '   inToleranceTime', configRow.inToleranceTime, 'outToleranceTime', configRow.outToleranceTime, 'deadTime',configRow.deadTime  
                    # SUCCESS, WARNING, MONITORING, NOT_PERSISTENT, NOT_CONSISTENT, OUT_OF_RANGE, ERROR, TIMEOUT
                    if valueOk:
                        if isPersistent:
                            configRow.status = PV_OK
                            rd.set(PV_MONITOR_ACTIVE, False)
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
                        rd.set(SETPOINT_STATUS, SETPOINT_PROBLEM)
        
                    logger.trace("  Status: %s" % configRow.status)  
                    rd.set(PV_MONITOR_STATUS, configRow.status)        
            
            if monitorActiveCount == 0:
                logger.info("The PV monitor is finished because there is nothing left to monitor...")
                complete = True
            
            # If the maximum time has been exceeded then count how many items did not complete their monitoring, aka Timed-Out 
            if (elapsedMinutes > timeLimitMin) or (persistencePending and elapsedMinutes > extendedDuration):
                logger.info("The PV monitor is finished because the max run time has been reached...")
                complete = True
                
                numTimeouts = 0
                for configRow in config.rows:
                    if configRow.status == PV_ERROR:
                        numTimeouts = numTimeouts + 1
                        configRow.status = TIMEOUT
                        rd.set(PV_MONITOR_STATUS, configRow.status)
                    rd.set(PV_MONITOR_ACTIVE, False)
                stepScope[NUMBER_OF_TIMEOUTS] = numTimeouts
                logger.info("...there were %i PV monitoring timeouts " % (numTimeouts))
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in monitorPV.py', logger)
    finally:
        # do cleanup here
        pass

    print "Returning complete = ", complete
        
    return complete