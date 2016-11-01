'''
Created on Dec 17, 2015

@author: rforbes
'''
import system
from ils.sfc.gateway.util import transferStepPropertiesToMessage, sendMessageToClient, handleUnexpectedGatewayError
from ils.sfc.gateway.api import getProject, getChartLogger
from ils.sfc.gateway.util import getTopChartRunId, getStepName
    
def activate(scopeContext, stepProperties, state):       
    try:
        stepName = getStepName(stepProperties)
        chartScope = scopeContext.getChartScope()    
        chartRunId = getTopChartRunId(chartScope)
        logger = getChartLogger(chartScope)
        payload = dict()
        transferStepPropertiesToMessage(stepProperties, payload)
        project = getProject(chartScope)
        
        logger.tracef("In %s.activate for step: %s, the payload is: %s", __name__, stepName, str(payload))
        
        sendMessageToClient(project, 'sfcCloseWindowByName', payload)
        
        windowPath = payload.get("window")
        SQL = "delete from SfcWindow where windowPath = '%s'" % (windowPath)
        print SQL
        rows=system.db.runUpdateQuery(SQL)
        logger.tracef("   ...deleted %d window records/toolbar buttons...", rows)
        
        logger.tracef("   ...leaving %s", __name__)
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in closeWindow.py', logger)
    finally:
        return True