'''
Created on Dec 17, 2015

@author: rforbes
'''

from ils.sfc.common.constants import NAME, NUMBER_OF_ERRORS, MSG_STATUS_ERROR, CONFIRM_CONTROLLERS_CONFIG, RECIPE_LOCATION, TAG_PATH, VALUE, OUTPUT_TYPE
from ils.sfc.gateway.api import getChartLogger, getIsolationMode
from ils.sfc.gateway.util import getStepProperty, handleUnexpectedGatewayError, notifyGatewayError, queueMessage
from system.ils.sfc import getConfirmControllersConfig, getProviderName
from ils.io.api import confirmControllerMode
from ils.sfc.recipeData.api import s88Get

def activate(scopeContext, stepProperties, state):
    from ils.sfc.gateway.recipe import RecipeData  
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
        stepScope[NUMBER_OF_ERRORS] = numberOfErrors
        
        configJson = getStepProperty(stepProperties, CONFIRM_CONTROLLERS_CONFIG)
        config = getConfirmControllersConfig(configJson)
        stepName = getStepProperty(stepProperties, NAME)
        logger.tracef("In %s, step: %s", __name__, stepName)

        for row in config.rows:
            testForZero = row.checkSPFor0
            checkPathToValve = row.checkPathToValve
            recipeScope = row.location
            key = row.key

            tagPath = s88Get(chartScope, stepScope, key + ".Tag", recipeScope)
            tagPath = "[" + providerName + "]" + tagPath
#            val = rd.get(VALUE)
            val = 0.0
            outputType = s88Get(chartScope, stepScope, key + ".OutputType", recipeScope)
            logger.trace("Confirming controller for tagPath: %s, Check SP for 0: %s, Check Path to Valve: %s, Output type: %s" % (tagPath, str(testForZero), str(checkPathToValve), outputType))
            
            try:
                success, errorMessage = confirmControllerMode(tagPath, val, testForZero, checkPathToValve, outputType)
                if not(success):
                    numberOfErrors = numberOfErrors + 1
                    txt = "Confirm Controller Mode Error: %s - %s.  %s" % (row.key, tagPath, errorMessage)
                    logger.warnf("Confirm Controller Mode failed for %s because %s", tagPath, errorMessage)
                    queueMessage(chartScope, txt, MSG_STATUS_ERROR)
            except:
                notifyGatewayError(chartScope, 'Trapped an error in confirmControllers.py', chartLogger)
                numberOfErrors = numberOfErrors + 1

                        
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in confirmControllers.py', chartLogger)
    finally:
        stepScope[NUMBER_OF_ERRORS] = numberOfErrors
        return True