'''
All SFC Client Message Handlers.
These message handlers all run in the client (the client receives the message from the gateway)
'''

import system, string
from ils.sfc.common.constants import WINDOW, WINDOW_PATH, WINDOW_ID, CONTROL_PANEL_NAME, ORIGINATOR, MESSAGE, SCALE, POSITION, \
    IS_SFC_WINDOW, DATABASE, CONTROL_PANEL_ID, CONTROL_PANEL_WINDOW_PATH
from ils.sfc.client.windowUtil import shouldShowWindow, fetchWindowInfo
from ils.common.windowUtil import positionWindow, openWindowInstance
from ils.common.config import getDatabaseClient
log = system.util.getLogger("com.ils.sfc.client.msgHandlers")

'''
This is the worst name in the history of bad names.  This is the handler in the client that catches the message, not the sender!
'''
def dispatchMessage(payload):
    '''call the appropriate method in this module and pass it the payload'''
    from ils.sfc.common.constants import HANDLER
    log.infof("In %s.dispatchMessage() received a message, payload: %s", __name__, str(payload))
    handlerMethod = payload[HANDLER]
    
    try:
        if handlerMethod == "sfcOpenWindow":
            sfcOpenWindow(payload) 
        elif handlerMethod == "sfcOpenControlPanel":
            sfcOpenControlPanel(payload)
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
    log.infof("In %s.sfcUnexpectedError...", __name__)

    # Check if this error is relevant to this client
    if not shouldShowWindow(payload):
        return

    msg = payload.get(MESSAGE, '<no message>')
    window = system.nav.openWindowInstance('SFC/ErrorPopup', {"message": msg})
    system.nav.centerWindow(window)


def sfcDialogMessage(payload):
    '''Open the DialogMessage window'''
    log.infof("In %s.sfcDialogMessage(), the payload is: %s", __name__, str(payload))
    
    windowPath = "SFC/DialogMessage"
    windowId = payload[WINDOW_ID]

    if not(shouldShowWindow(payload)):
        log.tracef("The control panel is not open and the originator is not this user so do not show the window here!")
        return
    
    record = fetchWindowInfo(windowId)
    if record == None:
        return
    
    position = record[POSITION]
    scale = record[SCALE]
    
    SQL = "select message from SfcDialogMessage where windowId = '%s'" % (windowId)
    log.tracef(SQL)
    message = system.db.runScalarQuery(SQL)
    log.tracef(message)
    
    window = system.nav.openWindowInstance(windowPath, {"windowId": windowId, "theMessage": message})
    positionWindow(window, position, scale)
    log.tracef("Done!")


''' This handles windows that are know to the SFC system'''
def sfcOpenWindow(payload):
    log.infof("In %s.sfcOpenWindow() with %s...", __name__, str(payload))
    
    windowPath = payload[WINDOW_PATH]
    windowId = payload[WINDOW_ID]
    isSfcWindow = payload[IS_SFC_WINDOW]
    controlPanelName = payload[CONTROL_PANEL_NAME]
    
    log.tracef("...checking if the window should be shown on this client...")
    if not(shouldShowWindow(payload)):
        return
    
    log.tracef("...the window is meant for this client...")
    record = fetchWindowInfo(windowId)
    if record == None:
        log.tracef("Unable to find window info, using defaults...")
        position = "center"
        scale = 1.0
    else:
        position = record[POSITION]
        scale = record[SCALE]
        
    log.tracef("Path: %s, Position: %s, Scale: %s", windowPath, position, str(scale)) 
    
    if isSfcWindow:    
        log.tracef("The window is an SFC window, passing the WindowId: <%s>...", str(windowId))
        windowPayload = {WINDOW_ID: windowId}
        
        ''' I really hate this implementation, if there is something extra on the payload ovr the entries that messaging need, then pass them on to the window '''
        if windowPath == "SFC/SaveData":
            windowPayload =  {WINDOW_ID: windowId, "simpleValue": payload["simpleValue"], "output": payload["output"], "header":  payload["header"]}

        log.tracef("Opening <%s>", windowPath)
        log.tracef("Window Payload: %s", str(windowPayload))
        window = openWindowInstance(windowPath, windowPayload, position, scale)
    else:
        log.tracef("The window is a plain window...")
        log.tracef("Opening <%s>", windowPath)
        window = system.nav.openWindowInstance(windowPath)
        positionWindow(window, position, scale)

''' This opens the control panel.  This is generally used when starting an SFC from a tag change script running in the gateway. '''
def sfcOpenControlPanel(payload):
    log.tracef("In sfcOpenControlPanel() with %s...", str(payload))

    controlPanelWindowPath = payload.get(CONTROL_PANEL_WINDOW_PATH, "SFC/ControlPanel")
    windowNames = system.gui.getOpenedWindowNames()
    for windowName in windowNames:
        log.tracef("Checking: %s", windowName)
        ''' This may need an enhancement to support multiple control panels for different consoles on the same window. '''
        if windowName == controlPanelWindowPath:
            log.tracef("The control panel is already open...")
            return
    
    controlPanelName = payload.get(CONTROL_PANEL_NAME, "")
    controlPanelId = payload.get(CONTROL_PANEL_ID, -1)
    originator = payload.get(ORIGINATOR, "")
    database = payload.get(DATABASE, "")
    clientDatabase = getDatabaseClient()
    
    log.tracef("...checking if the control panel should be shown on this client...")
    if database <> clientDatabase:
        log.tracef("...the window should NOT be shown because the client database (%s) does not match the message database (%s)", clientDatabase, database)
        return
     
    if string.upper(originator) <> string.upper(system.security.getUsername()):
        log.tracef("...the window should NOT be shown because the user does not match!")
        return
    
    log.tracef("...the control panel should be shown on this client...")

    position = payload[POSITION]
    scale = payload[SCALE]    
    window = system.nav.openWindowInstance(controlPanelWindowPath, {"controlPanelName": controlPanelName, "controlPanelId": controlPanelId})
    positionWindow(window, position, scale)


def sfcCloseWindow(payload):
    log.infof("In %s.sfcCloseWindow() with %s", __name__, str(payload))
    windowId = payload[WINDOW_ID]
    database = payload[DATABASE]
    clientDatabase = getDatabaseClient()
    if database <> clientDatabase:
        log.tracef("Ignoring closeWindow message because database does not match (%s vs %s)", database, clientDatabase)
        
    log.tracef("Attempting to close window with id: %d", windowId)
    if windowId <> None:
        openWindows = system.gui.getOpenedWindows()
        for window in openWindows:
            # Not all windows have a windowId, so be careful
            rootContainer = window.getRootContainer()
            openWindowId = rootContainer.getPropertyValue("windowId")
            if str(openWindowId) == str(windowId):
                system.nav.closeWindow(window)


def sfcCloseWindowByName(payload):
    log.infof("In %s.sfcCloseWindowByName() with %s", __name__, str(payload))
    windowPath = payload[WINDOW]
    log.tracef("Attempting to close: %s", windowPath)
    windows = system.gui.findWindow(windowPath)
    log.tracef("...found %d windows matching the path...", len(windows))
    for window in windows:
        log.tracef("...closing %s...", window)
        system.nav.closeWindow(window)
        
    print "Checking the open windows:"
    openWindows = system.gui.getOpenedWindows()
    for window in openWindows:
        print "   window: ", window.getPath()


def sfcShowQueue(payload):
    log.infof("In %s.sfcShowQueue with %s", str(payload))
    queueKey=payload['queueKey']
    originator = payload[ORIGINATOR]
    controlPanelName = payload[CONTROL_PANEL_NAME]
    showOverride = payload.get("showOverride", False)
    position = payload.get("position", "")
    scale = payload.get("scale", 1.0)
    
    log.tracef("...checking if the queue should be shown on this client...")
    if not(shouldShowWindow(payload)):
        return
    
#    if not(controlPanelOpen(controlPanelName)) and (originator != system.security.getUsername()) and not(showOverride):
#        print "The control panel is not open and the originator is not this user so do not show the window here!"
#        return

    from ils.queue.message import view
    view(queueKey, useCheckpoint=True, silent=True, position=position, scale=scale)
        
def sfcPrintWindow(payload):
    log.infof("In %s.sfcPrintWindow with %s", __name__, str(payload))
    from ils.common.util import okToPrint

    if okToPrint():
        windowName = payload['window']
        showPrintDialog = payload['showPrintDialog']
        windows = system.gui.findWindow(windowName)
        for window in windows:
            printJob = system.print.createPrintJob(window)
            printJob.showPrintDialog = showPrintDialog
            printJob.print()
    else:
        log.infof("--- IT IS NOT OK TO PRINT BECAUSE THE PRINTERS HAVE NOT BEEN SET UP ---")