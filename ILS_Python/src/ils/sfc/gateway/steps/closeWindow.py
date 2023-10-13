'''
Created on Dec 17, 2015

@author: rforbes
'''
import system
from ils.sfc.gateway.api import getChartLogger,getDatabaseName, handleUnexpectedGatewayError, getStepProperty, transferStepPropertiesToMessage, sendMessageToClient,\
    getControlPanelId
from ils.sfc.common.constants import NAME, WINDOW, WINDOW_ID

def activate(scopeContext, stepProperties, state):       
    try:
        stepName = getStepProperty(stepProperties, NAME)
        chartScope = scopeContext.getChartScope()
        database = getDatabaseName(chartScope)  
        logger = getChartLogger(chartScope)
        payload = dict()
        transferStepPropertiesToMessage(stepProperties, payload)
        windowPath = payload.get(WINDOW)
        controlPanelId = getControlPanelId(chartScope)
        
        SQL = "select windowId from SfcWindow where windowPath = '%s' and controlPanelId = %d" % (windowPath, controlPanelId) 
        windowId = system.db.runScalarQuery(SQL, database)
        payload[WINDOW_ID] = windowId
        
        logger.tracef("In %s.activate for step: %s, the payload is: %s", __name__, stepName, str(payload))
        
        sendMessageToClient(chartScope, 'sfcCloseWindowByName', payload)
        
        SQL = "delete from SfcWindow where windowPath = '%s'" % (windowPath)
        rows=system.db.runUpdateQuery(SQL, database)
        logger.tracef("   ...deleted %d window records/toolbar buttons...", rows)
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in closeWindow.py', logger)
    finally:
        return True