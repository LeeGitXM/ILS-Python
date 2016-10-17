'''
All SFC Client Message Handlers
'''

import system
from ils.sfc.common.constants import WINDOW, WINDOW_PATH, WINDOW_ID, CONTROL_PANEL_NAME, ORIGINATOR, MESSAGE, SCALE, POSITION, SECURITY, PRIVATE, SFC_WINDOW_LIST
from ils.sfc.client.windowUtil import controlPanelOpen, positionWindow, shouldShowWindow,\
    fetchWindowInfo

def dispatchMessage(payload):
    '''call the appropriate method in this module and pass it the payload'''
    from ils.sfc.common.util import callMethodWithParams
    from ils.sfc.common.constants import HANDLER
    from ils.sfc.client.windowUtil import openErrorPopup
    print "In %s.dispatchMessage() received a message, payload: %s" % (__name__, payload)
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

 
def sfcUnexpectedError(payload):
    print "In %s" % (__name__)
    from ils.sfc.common.util import handleUnexpectedClientError

    from ils.sfc.client.windowUtil import shouldShowWindow
    msg = payload.get(MESSAGE, '<no message>')
    controlPanelName = payload[CONTROL_PANEL_NAME]
    originator = payload[ORIGINATOR]
    print "Checking if we should show..."
    if not shouldShowWindow(controlPanelName, originator):
        print " ** Don't Show **"
        return
    print "Show it!"
    handleUnexpectedClientError(msg)


def sfcDialogMessage(payload):
    '''Open the DialogMessage window'''
    print "In %s.sfcDialogMessage(), the payload is: %s" % (__name__, str(payload))
    
    windowPath = "SFC/DialogMessage"
    windowId = payload[WINDOW_ID]

    if not(shouldShowWindow(payload)):
        print "The control panel is not open and the originator is not this user so do not show the window here!"
        return
    
    record = fetchWindowInfo(windowId)
    if record == None:
        return
    
    position = record[POSITION]
    scale = record[SCALE]
    
    SQL = "select message from SfcDialogMessage where windowId = '%s'" % (windowId)
    print SQL
    message = system.db.runScalarQuery(SQL)
    print message
    
    window = system.nav.openWindowInstance(windowPath, {"windowId": windowId, "theMessage": message})
    positionWindow(window, position, scale)
    print "Done!"


def sfcOpenWindow(payload):
    '''Open a plain Vision window that doesn't have all the special SFC window stuff'''
    from ils.sfc.client.windowUtil import positionWindow, shouldShowWindow
    
    print "In %s.sfcOpenWindow, the payload is: %s" % (__name__, str(payload))
    
    windowPath = payload[WINDOW_PATH]
    windowId = payload[WINDOW_ID]
    
    if not(shouldShowWindow(payload)):
        print "The control panel is not open and the originator is not this user so do not show the window here!"
        return
    
    record = fetchWindowInfo(windowId)
    position = record[POSITION]
    scale = record[SCALE]
    
    print "Path: %s, Position: %s, Scale: %s" % (windowPath, position, str(scale)) 
    
    if windowPath in SFC_WINDOW_LIST:
        print "The window is an SFC window, passing the WindowId!"
        payload = {WINDOW_ID: windowId}
    else:
        print "The window is a plain window..."
        payload = {}   
    
    window = system.nav.openWindowInstance(windowPath, payload)
    positionWindow(window, position, scale)

def sfcCloseWindow(payload):
    from ils.sfc.common.constants import WINDOW_ID
    from ils.sfc.client.windowUtil import closeDbWindow, getOpenWindow
    windowId = payload[WINDOW_ID]
    closeDbWindow(windowId)
                                              
def sfcCloseWindowByName(payload):
    windowPath = payload[WINDOW]
    windows = system.gui.findWindow(windowPath)
    for window in windows:
        system.nav.closeWindow(window)

def sfcShowQueue(payload):
    queueKey=payload['queueKey']
    originator = payload[ORIGINATOR]
    controlPanelName = payload[CONTROL_PANEL_NAME]

    if not controlPanelOpen(controlPanelName) and (originator != system.security.getUsername()):
        print "The control panel is not open and the originator is not this user so do not show the window here!"
        return

    from ils.queue.message import view
    view(queueKey, useCheckpoint=True)
        
def sfcPrintWindow(payload):
    windowName = payload['window']
    showPrintDialog = payload['showPrintDialog']
    windows = system.gui.findWindow(windowName)
    for window in windows:
        printJob = system.print.createPrintJob(window)
        printJob.showPrintDialog = showPrintDialog
        printJob.print()

