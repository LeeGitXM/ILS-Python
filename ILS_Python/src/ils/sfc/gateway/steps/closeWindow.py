'''
Created on Dec 17, 2015

@author: rforbes
'''
import system

def activate(scopeContext, stepProperties, state):   
    from ils.sfc.gateway.util import transferStepPropertiesToMessage, sendMessageToClient, handleUnexpectedGatewayError
    from ils.sfc.gateway.api import getProject, getChartLogger
    from ils.sfc.gateway.util import getTopChartRunId
    
    try:
        chartScope = scopeContext.getChartScope()    
        chartRunId = getTopChartRunId(chartScope)
        logger = getChartLogger(chartScope)
        payload = dict()
        transferStepPropertiesToMessage(stepProperties, payload)
        project = getProject(chartScope)
        
        logger.trace("In %s.activate, the payload is: %s" % (__name__, str(payload)))
        
        sendMessageToClient(project, 'sfcCloseWindowByName', payload)
        
        windowPath = payload.get("window")
        SQL = "delete from SfcWindow where windowPath = '%s'" % (windowPath)
        rows=system.db.runUpdateQuery(SQL)
        logger.trace("...deleted %i toolbar buttons..." % (rows))
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in closeWindow.py', logger)
    finally:
        return True