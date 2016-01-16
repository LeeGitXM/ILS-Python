'''
Created on Nov 3, 2014

@author: rforbes
'''
from ils.sfc.common.constants import MESSAGE_ID

def dispatchMessage(payload):
    from ils.sfc.common.util import callMethodWithParams
    from ils.sfc.common.constants import MESSAGE
    msgName = payload[MESSAGE]
    methodPath = 'ils.sfc.gateway.msgHandlers.' + msgName
    keys = ['payload']
    values = [payload]
    try:
        callMethodWithParams(methodPath, keys, values)
    except Exception, e:
        try:
            cause = e.getCause()
            errMsg = "Error dispatching gateway message %s: %s" % (msgName, cause.getMessage())
        except:
            errMsg = "Error dispatching gateway message %s: %s" % (msgName, str(e))
        #TODO: whats the right logger here?
        print errMsg
                              
def sfcResponse(payload):
    '''Handle a message that is a response to a request sent from the Gateway'''
    from system.ils.sfc import setResponse
    messageId = payload[MESSAGE_ID]
    setResponse(messageId, payload)
        
def sfcUpdateDownloads(payload):
    from ils.sfc.common.constants import ID, INSTANCE_ID
    from ils.sfc.gateway.monitoring import getMonitoringMgr
    timerId = payload[ID]
    chartRunId = payload[INSTANCE_ID]
    monitoringMgr = getMonitoringMgr(chartRunId, timerId)
    if monitoringMgr != None:
        monitoringMgr.sendClientUpdate()
    # else chart probably ended

def sfcCancelChart(payload):
    from ils.sfc.common.constants import INSTANCE_ID
    from ils.sfc.gateway.util import basicCancelChart
    topChartRunId = payload[INSTANCE_ID]
    basicCancelChart(topChartRunId)

def sfcPauseChart(payload):
    from ils.sfc.common.constants import INSTANCE_ID
    from ils.sfc.gateway.util import basicPauseChart    
    topChartRunId = payload[INSTANCE_ID]
    basicPauseChart(topChartRunId)
    
def sfcResumeChart(payload):
    from ils.sfc.common.constants import INSTANCE_ID
    from ils.sfc.gateway.util import basicResumeChart    
    topChartRunId = payload[INSTANCE_ID]
    basicResumeChart(topChartRunId)
    
def sfcCloseWindow(payload):
    '''close an open window. this is not usually called, as the step methods delete their own 
       windows. The client only needs to message a close window request when the window persists
       beyond the step scope, like for MessageDialog'''
    from ils.sfc.common.constants import DATABASE, WINDOW_ID, TABLE, PROJECT
    from ils.sfc.gateway.util import deleteAndSendClose
    import system.db
    table = payload[TABLE]
    project = payload[PROJECT]
    windowId = payload[WINDOW_ID]
    database = payload[DATABASE]
    system.db.runUpdateQuery("delete from %s where windowId = '%s'" % (table, windowId), database)   
    deleteAndSendClose(project, windowId, database)
