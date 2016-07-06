'''
Created on Dec 17, 2015

@author: rforbes
'''
from system.ils.sfc.common.Constants import CONFIRM_CONTROLLERS_CONFIG, RECIPE_LOCATION
from ils.sfc.common.constants import NUMBER_OF_ERRORS
from ils.sfc.gateway.api import getChartLogger
from ils.sfc.gateway.util import getStepProperty, handleUnexpectedGatewayError
from system.ils.sfc import getConfirmControllerConfig

def activate(scopeContext, stepProperties, state):    
    chartScope = scopeContext.getChartScope()
    stepScope = scopeContext.getStepScope()
    chartLogger = getChartLogger(chartScope)
    logger = getChartLogger(chartScope)
    
    try:
        pass
        numberOfErrors = 0
        stepScope[NUMBER_OF_ERRORS] = numberOfErrors
        
        configJson = getStepProperty(stepProperties, CONFIRM_CONTROLLERS_CONFIG)
        config = getConfirmControllerConfig(configJson)
        logger.trace("Block Configuration: %s" % (str(config)))
        outputRecipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION)
        logger.trace("Using recipe location: %s" % (outputRecipeLocation))

        for row in config.rows:
            print row
            print row.key
        
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in confirmControllers.py', chartLogger)
    finally:
        return True