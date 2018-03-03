'''
Created on Dec 17, 2015

@author: rforbes
'''

from ils.sfc.common.constants import NAME, MSG_STATUS_ERROR, CONFIRM_CONTROLLERS_CONFIG, ERROR_COUNT_KEY, ERROR_COUNT_MODE, ERROR_COUNT_SCOPE, COUNT_ABSOLUTE, \
    CHART_SCOPE, STEP_SCOPE, LOCAL_SCOPE, PRIOR_SCOPE, SUPERIOR_SCOPE, PHASE_SCOPE, OPERATION_SCOPE, GLOBAL_SCOPE
from ils.sfc.gateway.api import getChartLogger, getIsolationMode, notifyGatewayError, handleUnexpectedGatewayError, getStepProperty, postToQueue
from system.ils.sfc import getConfirmControllersConfig, getProviderName
from ils.io.api import confirmControllerMode
from ils.sfc.recipeData.api import s88Get, s88Set

def activate(scopeContext, stepProperties, state):
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    chartLogger = getChartLogger(chartScope)
    logger = getChartLogger(chartScope)

    # Everything will have the same tag provider - check isolation mode and get the provider
    isolationMode = getIsolationMode(chartScope)
    providerName = getProviderName(isolationMode)
    logger.tracef("Isolation mode: %s, provider: %s", isolationMode, providerName)

    try:
        numberOfErrors = 0
        
        configJson = getStepProperty(stepProperties, CONFIRM_CONTROLLERS_CONFIG)
        config = getConfirmControllersConfig(configJson)
        stepName = getStepProperty(stepProperties, NAME)
        errorCountScope = getStepProperty(stepProperties, ERROR_COUNT_SCOPE)
        errorCountKey = getStepProperty(stepProperties, ERROR_COUNT_KEY)
        errorCountMode = getStepProperty(stepProperties, ERROR_COUNT_MODE)
        logger.infof("In %s, step: %s", __name__, stepName)

        '''
        We pretty much require the recipe data that is referenced by the confirm controller configuration to be OUTPUT recipe data.
        '''
        for row in config.rows:
            testForZero = row.checkSPFor0
            checkPathToValve = row.checkPathToValve
            recipeScope = row.location
            key = row.key

            tagPath = s88Get(chartScope, stepScope, key + ".Tag", recipeScope)
            tagPath = "[" + providerName + "]" + tagPath
#            val = rd.get(VALUE)
            newVal = s88Get(chartScope, stepScope, key + ".OutputValue", recipeScope)
            outputType = s88Get(chartScope, stepScope, key + ".OutputType", recipeScope)
            logger.trace("Confirming controller for tagPath: %s, Check SP for 0: %s, Check Path to Valve: %s, Output type: %s, New Value: %s" % (tagPath, str(testForZero), str(checkPathToValve), outputType, str(newVal)))
            
            try:
                success, errorMessage = confirmControllerMode(tagPath, newVal, testForZero, checkPathToValve, outputType)
                if success:
                    logger.tracef("...%s mode is correct!",tagPath)
                else:
                    numberOfErrors = numberOfErrors + 1
                    txt = "Confirm Controller Mode Error: %s - %s.  %s" % (row.key, tagPath, errorMessage)
                    logger.warnf("Confirm Controller Mode failed for %s because %s", tagPath, errorMessage)
                    postToQueue(chartScope, MSG_STATUS_ERROR, txt)
            except:
                notifyGatewayError(chartScope, stepProperties, 'Trapped an error in confirmControllers.py', chartLogger)
                numberOfErrors = numberOfErrors + 1

        logger.infof("...%s completed with %d errors!", stepName, numberOfErrors)
        
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in confirmControllers.py', chartLogger)
    finally:
        #stepScope[NUMBER_OF_ERRORS] = numberOfErrors
        logger.tracef("Setting error count: %s - %s - %s...", errorCountScope, errorCountKey, errorCountMode)
        
        if errorCountScope == CHART_SCOPE:
            logger.tracef("Setting a chart scope error counter...")
            if errorCountMode == COUNT_ABSOLUTE:
                chartScope[errorCountKey] = numberOfErrors
            else:
                cnt = chartScope[errorCountKey]
                chartScope[errorCountKey] = cnt + numberOfErrors
        
        elif errorCountScope == STEP_SCOPE:
            ''' For stepScope counters the mode is implicitly incremental because the data is transient '''
            logger.tracef("Setting a step scope error counter...")
            stepScope[errorCountKey] = numberOfErrors
        
        elif errorCountScope in [LOCAL_SCOPE, PRIOR_SCOPE, SUPERIOR_SCOPE, PHASE_SCOPE, OPERATION_SCOPE, GLOBAL_SCOPE]:
            if errorCountMode == COUNT_ABSOLUTE:
                s88Set(chartScope, stepScope, errorCountKey + ".Value", numberOfErrors, errorCountScope)
            else:
                cnt = s88Get(chartScope, stepScope, errorCountKey + ".Value", errorCountScope)
                s88Set(chartScope, stepScope, errorCountKey + ".Value", numberOfErrors + cnt, errorCountScope)
        
        else:
            logger.errorf("*** UNEXPECTED ErrorCountScope <%s> ***", str(errorCountScope))
        
        return True