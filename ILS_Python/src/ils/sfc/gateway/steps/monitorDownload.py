'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties): 
    from system.ils.sfc.common.Constants import RECIPE_LOCATION, MONITOR_DOWNLOADS_CONFIG, DATA_ID, DOWNLOAD_STATUS, WRITE_CONFIRMED
    from ils.sfc.common.constants import PV_VALUE, PV_MONITOR_ACTIVE, PV_MONITOR_STATUS, STEP_PENDING,  PV_NOT_MONITORED
    from system.ils.sfc import getMonitorDownloadsConfig
    from ils.sfc.gateway.downloads import handleTimer
    from ils.sfc.gateway.monitoring import createMonitoringMgr
    from ils.sfc.gateway.util import sendMessageToClient, getStepProperty, transferStepPropertiesToMessage, handleUnexpectedGatewayError
    from system.ils.sfc import getProviderName
    from ils.sfc.gateway.api import getIsolationMode, getChartLogger, getProject
    from ils.sfc.gateway.recipe import RecipeData
    
    try:
        chartScope = scopeContext.getChartScope()
        stepScope = scopeContext.getStepScope()
        logger = getChartLogger(chartScope)
        timer, timerAttribute = handleTimer(chartScope, stepScope, stepProperties, logger)
        recipeLocation = getStepProperty(stepProperties, RECIPE_LOCATION)
        configJson = getStepProperty(stepProperties, MONITOR_DOWNLOADS_CONFIG)
        monitorDownloadsConfig = getMonitorDownloadsConfig(configJson)
        isolationMode = getIsolationMode(chartScope) 
        providerName = getProviderName(isolationMode)
        logger.info("Starting a download monitor...")
    
        # Reset the recipe data download and PV monitoring attributes
        for row in monitorDownloadsConfig.rows:
            logger.trace("Resetting recipe data with key: %s" % (row.key))
            rd = RecipeData(chartScope, stepScope, recipeLocation, row.key)
            # Initialze properties used by the write output process
            rd.set(DOWNLOAD_STATUS, STEP_PENDING)
            rd.set(WRITE_CONFIRMED, None)
            # Initialize properties used by a PV monitoring process
            rd.set(PV_MONITOR_ACTIVE, False)
            rd.set(PV_VALUE, None)
            rd.set(PV_MONITOR_STATUS, PV_NOT_MONITORED)
    
        mgr = createMonitoringMgr(chartScope, stepScope, recipeLocation, timer, timerAttribute, monitorDownloadsConfig, logger, providerName)
        payload = dict()
        payload[DATA_ID] = mgr.getTimerId()
        transferStepPropertiesToMessage(stepProperties, payload)
        project = getProject(chartScope)
        sendMessageToClient(project, 'sfcMonitorDownloads', payload)             
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in monitorDownload.py', logger)
    finally:
        return True