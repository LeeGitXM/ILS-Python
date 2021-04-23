'''
Created on May 3, 2015

@author: rforbes
'''
import system
from ils.common.config import getDatabaseClient
from ils.sfc.common.constants import SFC_WINDOW_LIST, DATABASE

def getWindowId(window):
    '''get the id of a window. Return None if it doesn't have a window id'''
    try:
        return window.getRootContainer().windowId
    except:
        return None

def getWindowPath(window):
    return window.path

def getRootContainer(event):
    from system.gui import getParentWindow
    return getParentWindow(event).rootContainer

def controlPanelOpen(controlPanelName):
    import system.gui
    controlPanels = system.gui.findWindow('SFC/ControlPanel')
    for controlPanel in controlPanels:
        if controlPanel.getRootContainer().controlPanelName == controlPanelName:
            return True
    return False

def consoleWindowOpen(post, db):
    SQL = "select windowName from TKConsole C, TkPost P "\
        "where C.PostId = P.PostId "\
        " and P.Post = '%s' " % (post)
    consoleWindow = system.db.runScalarQuery(SQL, db)
    #print "The console window for post <%s> is : %s" % (post, consoleWindow)
      
    consoleWindows = system.gui.findWindow(consoleWindow)
    if len(consoleWindows) > 0:
        #print "Found the console window"
        return True
    
    #print "Did not find the console window"
    return False

def getOpenWindow(windowId):
    '''Get the open window with the given id, or None if there isnt one'''
    import system.gui
    openWindows = system.gui.getOpenedWindows()
    for window in openWindows:
        openWindowId = getWindowId(window)
        if openWindowId == windowId:
            return window
    return None

def shouldShowWindow(payload):
    '''return True if a window from the chart with given control panel and originator should show in this client'''    
    from ils.sfc.common.constants import WINDOW, CONTROL_PANEL_NAME, ORIGINATOR, SECURITY, PRIVATE, POST

    originator = payload.get(ORIGINATOR, "")
    controlPanelName = payload.get(CONTROL_PANEL_NAME, "")
    security = payload.get(SECURITY, PRIVATE)
    post = payload.get(POST, "")
    showOverride = payload.get("showOverride", False)
    database = payload.get(DATABASE, "")
    clientDatabase = getDatabaseClient()
    
    if showOverride and database == clientDatabase:
        print "...the window should be shown because the showOverride flag is True and isolation mode matches!"
        return True
    
    if database <> clientDatabase:
        print "...the window should not be shown because the client database (%s) does not match the message database (%s)" % (clientDatabase, database)
        return False
    
    if security != PRIVATE:
        print "...the window should be shown because it is PUBLIC!"
        return True

    if controlPanelOpen(controlPanelName):
        print "...the window should be shown because the control panel (%s) is open!" % (controlPanelName)
        return True
    
    if consoleWindowOpen(post, database):
        print "...the window should be shown because the console window for post (%s) is open!" % (post)
        return True
     
    if originator == system.security.getUsername():
        print "...the window should be shown because the user matches!"
        return True
    
    if post == system.security.getUsername():
        print "...the window should be shown because the post matches the username!"
        return True
    
    print "   The window should NOT be shown because it is private, the control panel is not open and the originator is not this user!"
    return False
    
def openDbWindow(windowId):
    reopenWindow(windowId)
    
def fetchWindowInfo(windowId):
    database = getDatabaseClient()
    SQL = "select * from SfcWindow, SfcControlPanel where SfcWindow.windowId = '%s' "\
        " and SfcControlPanel.controlPanelId = SfcWindow.controlPanelId" % (windowId)
    pds = system.db.runQuery(SQL, database)
    
    if len(pds) == 0:
        return None
    
    return pds[0]

def reopenWindow(windowId):
    '''This is called from the button on the control panel.'''
    from ils.sfc.common.constants import POSITION, SCALE, WINDOW_ID
    from ils.common.windowUtil import positionWindow
    
    print "In %s.reopenWindow(), the windowId is: %s" % (__name__, windowId)

    database = getDatabaseClient()
    SQL = "select * from SfcWindow where windowId = '%s' " % (windowId)
    pds = system.db.runQuery(SQL, database)
    if len(pds) == 0:
        print "...window has been closed..."
        return
    
    record = pds[0]
    windowPath = record['windowPath']
    position = record[POSITION]
    scale = record[SCALE]
    title = record['title']
    
    print "Attempting to reopen %s- %s - %s - %s - %s" % (windowPath, position, str(scale), title, str(windowId))
    
    # Check if the window is already open.  If the window is an SFC window then we can support multiple distinct
    # instances of the window being open.  If it is a plain window, then we really don't support multiple instances
    # of the same window because we don't have a mechanism to pass data to initialize it.
    openWindows = system.gui.findWindow(windowPath)
    if len(openWindows) > 0:
        for window in openWindows:
            rootContainer = window.rootContainer
            if int(rootContainer.windowId) == int(windowId):
                print "...the window is already open, bringing it to the front..."
                window.toFront()
                return
    
    '''
    I used to have a list of SFC windows, all of these were required to have a property "windowId" which was the key to the table sfcWindow.
    I also allowed vanilla windows to be displayed but this caused problems when trying to reopen the window from the control panel window button.
    It makes more sense that every window that is going to be shown from an SFC requires the property "windowId". 
    '''

    payload = {"windowId": windowId}
    print "...reopening a SFC window %s with payload: %s" % (windowPath, str(payload))

    window = system.nav.openWindowInstance(windowPath, payload)
    positionWindow(window, position, scale)
    
    window.title = title

def sendCloseWindow(window, table):
    from ils.sfc.common.constants import DATABASE, WINDOW_ID, TABLE, PROJECT
    from ils.sfc.client.util import sendMessageToGateway
    import system.util
    windowId = window.getRootContainer().windowId
    database = getDatabaseClient()
    project = system.util.getProjectName()
    payload = {WINDOW_ID:windowId, DATABASE: database, TABLE: table, PROJECT: project}
    sendMessageToGateway(project, 'sfcCloseWindow', payload)
    system.nav.closeWindow(window)

