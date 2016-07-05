'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties, state):
    from  system.ils.sfc.common.Constants import ENABLE_PAUSE, ENABLE_RESUME, ENABLE_CANCEL
    from ils.sfc.gateway.util import getStepProperty, getControlPanelId, handleUnexpectedGatewayError
    from ils.sfc.gateway.api import getChartLogger, getDatabaseName
    import system.db
    
    try:
        chartScope = scopeContext.getChartScope()
        chartLogger = getChartLogger(chartScope)
        enablePause = getStepProperty(stepProperties, ENABLE_PAUSE)
        enableResume = getStepProperty(stepProperties, ENABLE_RESUME)
        enableCancel = getStepProperty(stepProperties, ENABLE_CANCEL)
        controlPanelId = getControlPanelId(chartScope)
        database = getDatabaseName(chartScope)
        system.db.runUpdateQuery("update SfcControlPanel set enablePause = %d,  enableResume = %d,  enableCancel = %d where controlPanelId = %s" % (enablePause, enableResume, enableCancel, controlPanelId), database)
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in enableDisable.py', chartLogger)
    finally:
        return True