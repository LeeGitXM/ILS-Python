'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):
    from  system.ils.sfc.common.Constants import ENABLE_PAUSE, ENABLE_RESUME, ENABLE_CANCEL
    from ils.sfc.gateway.util import getStepProperty, getControlPanelId
    import system.db
    chartScope = scopeContext.getChartScope()
    enablePause = getStepProperty(stepProperties, ENABLE_PAUSE)
    enableResume = getStepProperty(stepProperties, ENABLE_RESUME)
    enableCancel = getStepProperty(stepProperties, ENABLE_CANCEL)
    controlPanelId = getControlPanelId(chartScope)
    system.db.runUpdateQuery("update SfcControlPanel set enablePause = %d,  enableResume = %d,  enableCancel = %d where controlPanelId = '%s'" % (enablePause, enableResume, enableCancel, controlPanelId))