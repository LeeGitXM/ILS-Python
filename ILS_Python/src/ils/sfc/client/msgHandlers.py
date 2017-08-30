'''
All SFC Client Message Handlers.
These message handlers all run in the client (the client receives the message from the gateway)
'''

import system
from ils.sfc.common.constants import WINDOW, WINDOW_PATH, WINDOW_ID, CONTROL_PANEL_NAME, ORIGINATOR, MESSAGE, SCALE, POSITION, SECURITY, PRIVATE, \
    TARGET_STEP_UUID, KEY, IS_SFC_WINDOW, DATABASE
from ils.sfc.client.windowUtil import controlPanelOpen, shouldShowWindow, fetchWindowInfo
from ils.common.windowUtil import positionWindow, openWindowInstance
from ils.common.config import getDatabaseClient

'''
This is the worst name in the history of bad names.  This is the handler in the client that catches the message, not the sender!
'''
def dispatchMessage(payload):
    '''call the appropriate method in this module and pass it the payload'''
    from ils.sfc.common.constants import HANDLER
    print "In %s.dispatchMessage() received a message, payload: %s" % (__name__, payload)
    handlerMethod = payload[HANDLER]
    
    try:
        if handlerMethod == "sfcOpenWindow":
            sfcOpenWindow(payload) 
        elif handlerMethod == "sfcCloseWindow":
            sfcCloseWindow(payload)
        elif handlerMethod == "sfcShowQueue":
            sfcShowQueue(payload)
        elif handlerMethod == "sfcCloseWindowByName":
            sfcCloseWindowByName(payload)
        elif handlerMethod == "sfcPrintWindow":
            sfcPrintWindow(payload)
        elif handlerMethod == "sfcUnexpectedError":
            sfcUnexpectedError(payload)
        else:
            raise ValueError, "Unexpected message handler <%s>" % handlerMethod

    except Exception, e:
        try:
            cause = e.getCause()
            errMsg = "Error dispatching client message %s: %s" % (handlerMethod, cause.getMessage())
        except:
            errMsg = "Error dispatching client message %s: %s" % (handlerMethod, str(e))
        openErrorPopup(errMsg)


def openErrorPopup(msg):
    import system.nav
    window = system.nav.openWindowInstance('SFC/ErrorPopup', {"message": msg})
    system.nav.centerWindow(window)
    
 
def sfcUnexpectedError(payload):
    print "In sfcUnexpectedError..."

    # Check if this error is relevant to this client
    if not shouldShowWindow(payload):
        return

    msg = payload.get(MESSAGE, '<no message>')
    window = system.nav.openWindowInstance('SFC/ErrorPopup', {"message": msg})
    system.nav.centerWindow(window)


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


''' This handles windows that are know to the SFC system'''
def sfcOpenWindow(payload):
    print "In sfcOpenWindow()..."
    
    windowPath = payload[WINDOW_PATH]
    windowId = payload[WINDOW_ID]
    isSfcWindow = payload[IS_SFC_WINDOW]
    
    print "...checking if the window should be shown on this client..."
    if not(shouldShowWindow(payload)):
        return
    
    print "...the window is meant for this client..."
    record = fetchWindowInfo(windowId)
    if record == None:
        print "Unable to find window info, using defaults..."
        position = "center"
        scale = 1.0
    else:
        position = record[POSITION]
        scale = record[SCALE]
        
    print "Path: %s, Position: %s, Scale: %s" % (windowPath, position, str(scale)) 
    
    if isSfcWindow:    
        print "The window is an SFC window, passing the WindowId: <%s>..." % (str(windowId))
        payload = {WINDOW_ID: windowId}
        print "Opening <%s>" % (windowPath)
        print "Payload: ", payload
        window = openWindowInstance(windowPath, payload, position, scale)
    else:
        print "The window is a plain window..."
        print "Opening <%s>" % (windowPath)
        window = system.nav.openWindowInstance(windowPath)
        positionWindow(window, position, scale)


def sfcCloseWindow(payload):
    windowId = payload[WINDOW_ID]
    database = payload[DATABASE]
    clientDatabase = getDatabaseClient()
    if database <> clientDatabase:
        print "Ignoring closeWindow message because database does not match (%s vs %s)" % (database, clientDatabase)
        
    print "Attempting to close window with id: ", windowId
    if windowId <> None:
        openWindows = system.gui.getOpenedWindows()
        for window in openWindows:
            # Not all windows have a windowId, so be careful
            rootContainer = window.getRootContainer()
            openWindowId = rootContainer.getPropertyValue("windowId")
            if str(openWindowId) == str(windowId):
                system.nav.closeWindow(window)

           
def sfcCloseWindowByName(payload):
    windowPath = payload[WINDOW]
    windows = system.gui.findWindow(windowPath)
    for window in windows:
        system.nav.closeWindow(window)

def sfcShowQueue(payload):
    queueKey=payload['queueKey']
    originator = payload[ORIGINATOR]
    controlPanelName = payload[CONTROL_PANEL_NAME]
    showOverride = payload.get("showOverride", False)
    print "Payload: ", payload
    print "...checking if the queue should be shown on this client..."
    if not(shouldShowWindow(payload)):
        return
    
#    if not(controlPanelOpen(controlPanelName)) and (originator != system.security.getUsername()) and not(showOverride):
#        print "The control panel is not open and the originator is not this user so do not show the window here!"
#        return

    from ils.queue.message import view
    view(queueKey, useCheckpoint=True, silent=True)
        
def sfcPrintWindow(payload):
    windowName = payload['window']
    showPrintDialog = payload['showPrintDialog']
    windows = system.gui.findWindow(windowName)
    for window in windows:
        printJob = system.print.createPrintJob(window)
        printJob.showPrintDialog = showPrintDialog
        printJob.print()

