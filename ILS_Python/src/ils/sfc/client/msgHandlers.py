'''
All SFC Client Message Handlers
'''
def sfcUnexpectedError(payload):
    from ils.sfc.common.util import handleUnexpectedClientError
    from ils.sfc.common.constants import MESSAGE, CONTROL_PANEL_ID, ORIGINATOR
    from ils.sfc.client.windowUtil import shouldShowWindow
    msg = payload.get(MESSAGE, '<no message>')
    controlPanelId = payload[CONTROL_PANEL_ID]
    originator = payload[ORIGINATOR]
    if not shouldShowWindow(controlPanelId, originator):
        return
    handleUnexpectedClientError(msg)

def sfcOpenWindow(payload):
    from ils.sfc.common.constants import WINDOW_ID
    from ils.sfc.client.windowUtil import openDbWindow
    windowId = payload[WINDOW_ID]
    openDbWindow(windowId)

def sfcOpenOrdinaryWindow(payload):
    '''Open a plain Vision window that doesn't have all the special SFC window stuff'''
    from ils.sfc.common.constants import WINDOW, CONTROL_PANEL_ID, ORIGINATOR
    from ils.sfc.client.windowUtil import controlPanelOpen
    import system.nav
    windowPath = payload[WINDOW]
    controlPanelId = payload[CONTROL_PANEL_ID]
    originator = payload[ORIGINATOR]
    controlPanelOpen = controlPanelOpen(controlPanelId)
    print 'controlPanelOpen', controlPanelOpen, 'originator', originator
    if not controlPanelOpen and (originator != system.security.getUsername()):
        # this client should not see windows from this run
        return
    system.nav.openWindowInstance(windowPath)

def sfcCloseWindow(payload):
    from ils.sfc.common.constants import WINDOW_ID
    from ils.sfc.client.windowUtil import closeDbWindow, getOpenWindow
    windowId = payload[WINDOW_ID]
    closeDbWindow(windowId)
                                              
def sfcCloseWindowByName(payload):
    from ils.sfc.common.constants import WINDOW
    from ils.sfc.common.windowUtil import isSfcWindow
    from ils.sfc.client.windowUtil import closeDbWindow, getWindowId
    import system.gui, system.nav
    windowPath = payload[WINDOW]
    windows = system.gui.findWindow(windowPath)
    for window in windows:
        if isSfcWindow(windowPath):
            windowId = getWindowId(window)
            closeDbWindow(windowId)
        else:
            system.nav.closeWindow(window)

def sfcShowQueue(payload):
    queueKey=payload['queueKey']
    from ils.queue.message import view
    view(queueKey, useCheckpoint=True)
        
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
    from ils.sfc.client.windowUtil import openErrorPopup
    # print 'dispatchMessage() received a message, payload:', payload
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
        openErrorPopup(errMsg)


