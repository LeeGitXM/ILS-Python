'''
Created on Dec 17, 2015

@author: rforbes
'''

import system
from ils.sfc.common.constants import ENABLE_PAUSE, ENABLE_RESUME, ENABLE_CANCEL, ENABLE_START, ENABLE_RESET, STEP_NAME
from ils.sfc.gateway.api import getChartLogger, getDatabaseName, handleUnexpectedGatewayError, getStepProperty, getControlPanelId
    
def activate(scopeContext, stepProperties, state):
    
    try:
        chartScope = scopeContext.getChartScope()
        logger = getChartLogger(chartScope)
        logger.trace("In %s with step %s" % (__name__, getStepProperty(stepProperties, STEP_NAME)))

        enablePause = getStepProperty(stepProperties, ENABLE_PAUSE)
        enableResume = getStepProperty(stepProperties, ENABLE_RESUME)
        enableCancel = getStepProperty(stepProperties, ENABLE_CANCEL)
        enableStart = getStepProperty(stepProperties, ENABLE_START)
        enableReset = getStepProperty(stepProperties, ENABLE_RESET)
    
        controlPanelId = getControlPanelId(chartScope)
        database = getDatabaseName(chartScope)

        SQL = "update SfcControlPanel set enablePause = %d,  enableResume = %d,  enableCancel = %d, "\
            "enableStart = %d, enableReset = %d where controlPanelId = %s" % \
            (enablePause, enableResume, enableCancel, enableStart, enableReset, controlPanelId)

        rows = system.db.runUpdateQuery(SQL, database)
        logger.trace("Updated %i rows" % (rows))
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in enableDisable.py', logger)
    finally:
        return True