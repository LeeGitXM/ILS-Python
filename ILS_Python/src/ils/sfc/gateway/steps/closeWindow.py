'''
Created on Dec 17, 2015

@author: rforbes
'''
import system
from ils.sfc.gateway.util import transferStepPropertiesToMessage, sendMessageToClient, handleUnexpectedGatewayError
from ils.sfc.gateway.api import getProject, getChartLogger,getDatabaseName, getPostForControlPanelName
from ils.sfc.gateway.util import getTopChartRunId, getStepProperty
from ils.sfc.common.constants import NAME

def activate(scopeContext, stepProperties, state):       
    try:
        stepName = getStepProperty(stepProperties, NAME)
        chartScope = scopeContext.getChartScope()
        database = getDatabaseName(chartScope)  
        logger = getChartLogger(chartScope)
        payload = dict()
        transferStepPropertiesToMessage(stepProperties, payload)
        
        logger.tracef("In %s.activate for step: %s, the payload is: %s", __name__, stepName, str(payload))
        
        sendMessageToClient(chartScope, 'sfcCloseWindowByName', payload)
        
        windowPath = payload.get("window")
        SQL = "delete from SfcWindow where windowPath = '%s'" % (windowPath)
        rows=system.db.runUpdateQuery(SQL, database)
        logger.tracef("   ...deleted %d window records/toolbar buttons...", rows)
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in closeWindow.py', logger)
    finally:
        return True