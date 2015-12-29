'''
All SFC Client Message Handlers
'''
def sfcUnexpectedError(payload):
    from ils.sfc.common.util import handleUnexpectedClientError
    from ils.sfc.common.constants import MESSAGE
    msg = payload[MESSAGE]
    handleUnexpectedClientError(msg)

def sfcOpenWindow(payload):
    from ils.sfc.common.constants import DATABASE, WINDOW_ID
    from ils.sfc.client.windowUtil import openDbWindow
    windowId = payload[WINDOW_ID]
    database = payload[DATABASE]
    openDbWindow(windowId, database)

def sfcCloseWindow(payload):
    from ils.sfc.common.constants import WINDOW_ID
    from ils.sfc.client.windowUtil import closeDbWindow
    windowId = payload[WINDOW_ID]
    closeDbWindow(windowId)
    
def dispatchMessage(payload):
    from ils.sfc.common.util import callMethodWithParams
    from ils.sfc.common.constants import MESSAGE
    import system.gui
    # print 'dispatchMessage: payload:', payload
    msgName = payload[MESSAGE]
    methodPath = 'ils.sfc.client.msgHandlers.' + msgName
    keys = ['payload']
    values = [payload]
    try:
        callMethodWithParams(methodPath, keys, values)
    except Exception, e:
        try:
            cause = e.getCause()
            errMsg = "Error dispatching client message %s: %s" % (msgName, cause.getMessage())
        except:
            errMsg = "Error dispatching client message %s: %s" % (msgName, str(e))
        system.gui.errorBox(errMsg)


