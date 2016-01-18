'''
Created on Nov 3, 2014

@author: rforbes
'''

def dispatchMessage(payload):
    from ils.sfc.common.util import callMethodWithParams
    from ils.sfc.common.constants import HANDLER
    methodName = payload[HANDLER]
    methodPath = 'ils.sfc.gateway.msgHandlers.' + methodName
    keys = ['payload']
    values = [payload]
    try:
        callMethodWithParams(methodPath, keys, values)
    except Exception, e:
        try:
            cause = e.getCause()
            errMsg = "Error dispatching gateway message %s: %s" % (methodName, cause.getMessage())
        except:
            errMsg = "Error dispatching gateway message %s: %s" % (methodName, str(e))
        #TODO: whats the right logger here?
        print errMsg
                              
def sfcResponse(payload):
    '''Handle a message that is a response to a request sent from the Gateway'''
    from system.ils.sfc import setResponse
    from ils.sfc.common.constants import WINDOW_ID
    windowId = payload[WINDOW_ID]
    setResponse(windowId, payload)
        
def sfcUpdateDownloads(payload):
    from ils.sfc.common.constants import ID, INSTANCE_ID
    from ils.sfc.gateway.monitoring import getMonitoringMgr
    timerId = payload[ID]
    chartRunId = payload[INSTANCE_ID]
    monitoringMgr = getMonitoringMgr(chartRunId, timerId)
    if monitoringMgr != None:
        monitoringMgr.sendClientUpdate()
    # else chart probably ended
    
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
