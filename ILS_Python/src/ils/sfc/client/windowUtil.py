'''
Created on May 3, 2015

@author: rforbes
'''

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
    return window.getRootContainer().windowId

def getWindowPath(window):
    return window.path

def getRootContainer(event):
    from system.gui import getParentWindow
    return getParentWindow(event).rootContainer
    
def updateClockField(window):  
    '''Update clock time in a field called 'clockField' '''
    import time
    from ils.sfc.common.util import formatTime
    import system.util
   
    rootContainer = window.getRootContainer()    
    clockField = rootContainer.getComponent('clockField')
    clockField.text = formatTime(time.time())

def controlPanelOpen(controlPanelId):
    import system.gui
    controlPanels = system.gui.findWindow('SFC/ControlPanel')
    for controlPanel in controlPanels:
        if controlPanel.getRootContainer().controlPanelId == controlPanelId:
            return True
        else:
            return False
    
def openDbWindow(windowId, database):
    '''A generic helper method for message handlers to open a window in the 
       control panel that has an associated toolbar button'''
    import system.nav, system.security
    from ils.sfc.common.constants import POSITION, SCALE, WINDOW_ID
    pyWindowData = system.db.runQuery("select * from SfcWindow, SfcControlPanel where SfcWindow.windowId = '%s' and SfcControlPanel.controlPanelId = SfcWindow.controlPanelId" % (windowId), database)
    controlPanelId = pyWindowData[0]['controlPanelId']
    originator = pyWindowData[0]['originator']
    if not controlPanelOpen(controlPanelId) and (originator != system.security.getUsername()):
        # this client should not see windows from this run
        return
    
    windowType = pyWindowData[0]['type']
    position = pyWindowData[0][POSITION]
    scale = pyWindowData[0][SCALE]
    title = pyWindowData[0]['title']
    window = system.nav.openWindowInstance(windowType, {WINDOW_ID:windowId})
    window.title = title
    positionWindow(window, position, scale)
    
def closeDbWindow(targetId):
    import system.gui, system.nav
    for window in system.gui.getOpenedWindows():
        try:
            windowId = window.getRootContainer().windowId
            if windowId == targetId:
                system.nav.closeWindow(window)
        except:
            # no window id property
            pass
