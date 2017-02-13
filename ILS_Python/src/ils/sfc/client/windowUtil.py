'''
Created on May 3, 2015

@author: rforbes
'''
import system
from ils.sfc.client.util import getDatabase
from ils.sfc.common.constants import SFC_WINDOW_LIST
    
def positionWindow(window, position, scale):
    '''Position and size a window within the main window''' 
    from ils.sfc.common.constants import LEFT, CENTER, TOP
    mainWindow = window.parent
    position = position.lower()
    
#    width = mainWindow.getWidth() * scale
#    height = mainWindow.getHeight() * scale    
    # Scale of 1 should be w.r.t. how the window was designed, not the size of the parent, but this is an interesting idea
    width = window.getWidth() * scale
    height = window.getHeight() * scale
    if position.endswith(LEFT):
        ulx = 0
    elif position.endswith(CENTER):
        ulx = .5 * mainWindow.getWidth() - .5 * width
    else:
        ulx = mainWindow.getWidth() - width

    if position.startswith(TOP):
        uly = 0
    elif position.startswith(CENTER):
        uly = .5 * mainWindow.getHeight() - .5 * height
    else:
        uly = mainWindow.getHeight() - height
    window.setSize(int(width), int(height))
    window.setLocation(int(ulx), int(uly))

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
    '''return if a window from the chart with given control panel and originator should show in this client'''    
    from ils.sfc.common.constants import WINDOW, CONTROL_PANEL_NAME, ORIGINATOR, SECURITY, PRIVATE

    originator = payload[ORIGINATOR]
    controlPanelName = payload[CONTROL_PANEL_NAME]
    security = payload.get(SECURITY, PRIVATE)

    if security == PRIVATE and not controlPanelOpen(controlPanelName) and (originator != system.security.getUsername()):
        print "The control panel is not open and the originator is not this user so do not show the window here!"
        return False
    
    return True
    
def openDbWindow(windowId):
    reopenWindow(windowId)
    
def fetchWindowInfo(windowId):
    database = getDatabase()
    SQL = "select * from SfcWindow, SfcControlPanel where SfcWindow.windowId = '%s' "\
        " and SfcControlPanel.controlPanelId = SfcWindow.controlPanelId" % (windowId)
    pds = system.db.runQuery(SQL, database)
    
    if len(pds) == 0:
        return None
    
    return pds[0]

def reopenWindow(windowId):
    '''This is called from the button on the control panel.'''
    import system.nav, system.security
    from ils.sfc.client.util import getDatabase
    from ils.sfc.common.constants import POSITION, SCALE, WINDOW_ID
    
    print "In %s.reopenWindow(), the windowId is: %s" % (__name__, windowId)

    database = getDatabase()
    SQL = "select * from SfcWindow, SfcControlPanel where SfcWindow.windowId = '%s' and SfcControlPanel.controlPanelId = SfcWindow.controlPanelId" % (windowId)
    pds = system.db.runQuery(SQL, database)
    if len(pds) == 0:
        # window closed already; ignore
        print "...window has been closed..."
        return
    
    record = pds[0]
    windowPath = record['windowPath']
    position = record[POSITION]
    scale = record[SCALE]
    title = record['title']
    windowId = record['windowId']
    
    # Check if the window is already open.  If the window is an SFC window then we can support multiple distinct
    # instances of the window being open.  If it is a plain window, then we really don't support multiple instances
    # of the same window because we don't have a mechanism to pass data to initialize it.
    openWindows = system.gui.findWindow(windowPath)
    if len(openWindows) > 0:
        if windowPath in SFC_WINDOW_LIST:
            for window in openWindows:
                rootContainer = window.rootContainer
                if rootContainer.windowId == windowId:
                    print "...the window is already open, bringing it to the front..."
                    window.toFront()
                    return
            
        else:
            for window in openWindows:
                print "...the window is already open, bringing it to the front..."
                window.toFront()
            return

    payload = {}
    if windowPath in SFC_WINDOW_LIST:
        print "...reopening a SFC window..."
        payload = {"windowId": windowId}
    else:
        payload = {}
        print "...reopening an ordinary window: ", windowPath

    
    window = system.nav.openWindowInstance(windowPath, payload)
    window.title = title
    positionWindow(window, position, scale)

def sendCloseWindow(window, table):
    from ils.sfc.common.constants import DATABASE, WINDOW_ID, TABLE, PROJECT
    from ils.sfc.client.util import sendMessageToGateway
    import system.util
    windowId = window.getRootContainer().windowId
    database = getDatabase()
    project = system.util.getProjectName()
    payload = {WINDOW_ID:windowId, DATABASE: database, TABLE: table, PROJECT: project}
    sendMessageToGateway(project, 'sfcCloseWindow', payload)
    system.nav.closeWindow(window)

def openErrorPopup(msg):
    import system.nav
    window = system.nav.openWindowInstance('SFC/ErrorPopup', {"message": msg})
    system.nav.centerWindow(window)
