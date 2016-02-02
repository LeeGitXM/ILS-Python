'''
Created on May 3, 2015

@author: rforbes
'''
from ils.sfc.client.util import getDatabase

def sendWindowResponse(window, response):
    '''standard actions when a window representing a response is closed by the user'''
    from ils.sfc.common.constants import RESPONSE, WINDOW_ID
    from ils.sfc.client.util import sendMessageToGateway
    rootContainer = window.getRootContainer()
    windowId = rootContainer.windowId
    import system.util, system.nav
    replyPayload = dict() 
    replyPayload[RESPONSE] = response
    replyPayload[WINDOW_ID] = windowId    
    project = system.util.getProjectName()
    sendMessageToGateway(project, 'sfcResponse', replyPayload)
    system.nav.closeWindow(window)
    
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
#    window.setSize(int(width), int(height))
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

def controlPanelOpen(controlPanelId):
    import system.gui
    controlPanels = system.gui.findWindow('SFC/ControlPanel')
    for controlPanel in controlPanels:
        if controlPanel.getRootContainer().controlPanelId == controlPanelId:
            return True
        else:
            return False

def getOpenWindowByPath(path):
    '''Get the open window with the given path, or None if there isnt one'''
    import system.gui
    openWindows = system.gui.findWindow(path)
    if len(openWindows) > 0:
        return openWindows[0]
    else:
        return None

def getOpenWindow(windowId):
    '''Get the open window with the given id, or None if there isnt one'''
    import system.gui
    openWindows = system.gui.getOpenedWindows()
    for window in openWindows:
        openWindowId = getWindowId(window)
        if openWindowId == windowId:
            return window
    return None
       
def openDbWindow(windowId):
    '''A generic helper method for message handlers to open a window in the 
       control panel that has an associated toolbar button'''
    import system.nav, system.security
    from ils.sfc.client.util import getDatabase
    from ils.sfc.common.constants import POSITION, SCALE, WINDOW_ID
    existingWindow = getOpenWindow(windowId)
    if existingWindow != None:
        print "Bringing an open window to the front..."
        existingWindow.toFront()
        return
    
    database = getDatabase()
    SQL = "select * from SfcWindow, SfcControlPanel where SfcWindow.windowId = '%s' and SfcControlPanel.controlPanelId = SfcWindow.controlPanelId" % (windowId)
    pyWindowData = system.db.runQuery(SQL, database)
    if len(pyWindowData) == 0:
        # window closed already; ignore
        print "...window has been closed..."
        return
    
    controlPanelId = pyWindowData[0]['controlPanelId']
    originator = pyWindowData[0]['originator']
    if not controlPanelOpen(controlPanelId) and (originator != system.security.getUsername()):
        # this client should not see windows from this run
        print "don't display the window because there isn't a control panel"
        return
    
    windowType = pyWindowData[0]['type']
    position = pyWindowData[0][POSITION]
    scale = pyWindowData[0][SCALE]
    title = pyWindowData[0]['title']
    window = system.nav.openWindowInstance(windowType, {WINDOW_ID:windowId})
    window.title = title
    positionWindow(window, position, scale)
    
def closeDbWindow(windowId):
    import system.nav
    window = getOpenWindow(windowId)
    if window != None:
        system.nav.closeWindow(window)

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
    window = system.nav.openWindow('SFC/ErrorPopup')
    textArea = window.getRootContainer().getComponent("textArea")
    textArea.text = msg
