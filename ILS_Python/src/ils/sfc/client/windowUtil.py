'''
Created on May 3, 2015

@author: rforbes
'''

def createPositionedWindow(payload, windowProps = dict()):
    '''A generic helper method for message handlers to open a window in the 
       control panel that has an associated toolbar button'''
    from ils.sfc.client.controlPanel import getController
    # We expect these keys in the payload:
    from ils.sfc.common.constants import POSITION, SCALE, WINDOW, WINDOW_TITLE, INSTANCE_ID, BUTTON_LABEL
    window = createWindow(payload[WINDOW], payload[WINDOW_TITLE], payload[INSTANCE_ID], windowProps)
    positionWindow(window, payload[POSITION],  payload[SCALE])
    controlPanel = getController(payload[INSTANCE_ID])
    buttonLabel = payload.get(BUTTON_LABEL, None)
    if controlPanel != None:
        controlPanel.addWindow(buttonLabel, window) 
    else:
        print 'couldnt find control panel for run ', payload[INSTANCE_ID]
    return window

def createWindow(windowName, windowTitle, chartRunId, windowProps = dict()):
    '''Create an instance of the given window.
       "Instance" implies multiple windows of this type may be open at once.
       ALL windows must be created with this method.
       windowProps contains any extra (ie beyond basic) properties; it may be defaulted'''
    from ils.sfc.common.constants import WINDOW_ID, INSTANCE_ID
    from ils.sfc.common.util import createUniqueId
    import system.nav
    windowProps[INSTANCE_ID] = chartRunId
    windowProps[WINDOW_ID] = createUniqueId()
    window = system.nav.openWindowInstance(windowName, windowProps)
    window.title = windowTitle
    return window

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

def getChartRunId(window):
    return window.getRootContainer().instanceId

def getMessageId(window):
    return window.getRootContainer().messageId

def getWindowPath(window):
    return window.name

def responseWindowClosed(event, response):
    '''standard actions when a window representing a response is closed by the user'''
    from ils.sfc.client.util import sendResponse
    from ils.sfc.client.controlPanel import getController
    import system.gui.getParentWindow
    window = system.gui.getParentWindow(event)
        
    messageId = getMessageId(window)
    sendResponse(messageId, response)
    
    chartRunId = getChartRunId(window)
    windowId = getWindowId(window)
    controller = getController(chartRunId)
    controller.removeWindow(windowId)    
    system.nav.closeWindow(window)
    
def updateClockField(window):  
    '''Update clock time in a field called 'clockField' '''
    import time
    from ils.sfc.common.util import formatTime
    import system.util
   
    rootContainer = window.getRootContainer()    
    clockField = rootContainer.getComponent('clockField')
    clockField.text = formatTime(time.time())
        