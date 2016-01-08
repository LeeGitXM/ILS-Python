'''
All SFC Client Message Handlers
'''
def sfcUnexpectedError(payload):
    from ils.sfc.common.util import handleUnexpectedClientError
    from ils.sfc.common.constants import MESSAGE
    msg = payload.get(MESSAGE, '<no message>')
    handleUnexpectedClientError(msg)

def sfcOpenWindow(payload):
    from ils.sfc.common.constants import WINDOW_ID
    from ils.sfc.client.windowUtil import openDbWindow
    windowId = payload[WINDOW_ID]
    openDbWindow(windowId)

def sfcCloseWindow(payload):
    from ils.sfc.common.constants import WINDOW_ID
    from ils.sfc.client.windowUtil import closeDbWindow
    windowId = payload[WINDOW_ID]
    closeDbWindow(windowId)

def sfcShowQueue(payload):
    import system
    from ils.sfc.common.constants import MSG_QUEUE_WINDOW
    # Note: the control panel logic will take care of setting the current msg queue on this window
    system.nav.openWindow(MSG_QUEUE_WINDOW)
        
def sfcPrintWindow(payload):
    import system
    windowName = payload['window']
    showPrintDialog = payload['showPrintDialog']
    windows = system.gui.findWindow(windowName)
    for window in windows:
        printJob = system.print.createPrintJob(window)
        printJob.showPrintDialog = showPrintDialog
        printJob.print()
                
def dispatchMessage(payload):
    '''call the appropriate method in this module and pass it the payload'''
    from ils.sfc.common.util import callMethodWithParams
    from ils.sfc.common.constants import HANDLER
    import system.gui
    # print 'dispatchMessage: payload:', payload
    handlerMethod = payload[HANDLER]
    methodPath = 'ils.sfc.client.msgHandlers.' + handlerMethod
    keys = ['payload']
    values = [payload]
    try:
        callMethodWithParams(methodPath, keys, values)
    except Exception, e:
        try:
            cause = e.getCause()
            errMsg = "Error dispatching client message %s: %s" % (handlerMethod, cause.getMessage())
        except:
            errMsg = "Error dispatching client message %s: %s" % (handlerMethod, str(e))
        system.gui.errorBox(errMsg)


