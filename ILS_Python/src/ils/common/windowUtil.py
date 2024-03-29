'''
Created on Jan 12, 2016

@author: ils
'''
import system, math, string
from ils.log import getLogger
log =getLogger(__name__)

def bringWindowToFront(windowName):
    windows = system.gui.findWindow(windowName)
    for window in windows:
        window.toFront()
        system.nav.centerWindow(window)

def setTableColumnHeading(table, columnName, columnLabel):
    ds = table.columnAttributesData
    for row in range(ds.rowCount):
        if ds.getValueAt(row, "name") == columnName:
            ds = system.dataset.setValue(ds, row, "label", columnLabel)
    table.columnAttributesData = ds

def getRootContainer(component):
    if component==None:
        return None
    elif component.name == "Root Container":
        return component
    else:
        return getRootContainer(component.parent)
    
def clearTable(table):
    ds = table.data
    rows=[]
    for i in range(0, ds.rowCount):
        rows.append(i)
    ds = system.dataset.deleteRows(ds, rows)
    table.data = ds

def clearTree(tree):
    ds = tree.data
    rows=[]
    for i in range(0, ds.rowCount):
        rows.append(i)
    ds = system.dataset.deleteRows(ds, rows)
    tree.data = ds

# Open a window instance with additional capability to TILE, STACK, CENTER or position the 
# window in the standard well-known positions.
def openWindowInstance(windowPath, props={}, mode="CENTER", scale=1.0):
    '''Position and size a window within the main window''' 
    window = system.nav.openWindowInstance(windowPath, props)
    
    mode=string.upper(mode)
    
    if mode == "TILE": 
        tileWindow(window, scale)
    elif mode == "STACK":
        stackWindow(window, scale)
    elif mode == "CENTER":
        system.nav.centerWindow(window)
    elif mode in ['UPPER-LEFT', 'TOPLEFT', 'UPPER-CENTER', 'TOPCENTER', 'UPPER-RIGHT', 'TOPRIGHT', 'LOWER-LEFT', 'BOTTOMLEFT', 'LOWER-CENTER', 'BOTTOMCENTER','LOWER-RIGHT', 'BOTTOMRIGHT']:
        positionWindow(window, mode, scale)
        
    # Scale the window if necessary
    if scale != 1.0:
        width = window.getWidth()
        height = window.getHeight()
        window.setSize(int(width * scale), int(height * scale))

'''
Position the upper left corner of the window.
'''
def positionWindow(window, mode, scale=1.0):
    log.tracef("%s.Positioning the window to: %s", __name__, mode)
    mainWindow = window.parent
    mainWidth = mainWindow.getWidth()
    mainHeight = mainWindow.getHeight()
    log.tracef("Main window is %d X %d (Width X Height)", mainWidth, mainHeight)
    width = window.getWidth()
    height = window.getHeight()
    log.tracef("This window is %d X %d (Width X Height)", width, height)
    window.setSize(int(width * scale), int(height * scale))
    xOffset,yOffset=getDockOffset()
    log.tracef("Dock Offset is (%d, %d)", xOffset, yOffset)

    mode = string.upper(mode)
    if mode in ['UPPER-LEFT', 'UPPERLEFT', 'TOPLEFT']:
        ulx = xOffset
        uly = 0
        log.tracef("...positioning window at %d X %d (Width X Height)", ulx, uly)
        window.setLocation(ulx, uly)
    elif mode in ['UPPER-CENTER', 'UPPERCENTER', 'TOPCENTER']:
        ulx = xOffset + (mainWidth - xOffset) / 2 - (width * scale) / 2
        uly = 0
        log.tracef("...positioning window at %d X %d (Width X Height)", ulx, uly)
        window.setLocation(int(ulx), uly)
    elif mode in ['UPPER-RIGHT', 'UPPERRIGHT', 'TOPRIGHT']:
        ulx = mainWidth - (width * scale) 
        uly = 0
        log.tracef("...positioning window at %d X %d (Width X Height)", ulx, uly)
        window.setLocation(int(ulx), uly)
    elif mode in ['LOWER-LEFT', 'LOWERLEFT', 'BOTTOMLEFT']:
        ulx = xOffset
        uly = mainHeight - int(height * scale)
        log.tracef("...positioning window at %d X %d (Width X Height)", ulx, uly)
        window.setLocation(int(ulx), int(uly))
    elif mode in ['LOWER-CENTER', 'LOWERCENTER', 'BOTTOMCENTER']:
        ulx = xOffset + (mainWidth - xOffset) / 2 - (width * scale) / 2
        uly = mainHeight - int(height * scale)
        log.tracef("...positioning window at %d X %d (Width X Height)", ulx, uly)
        window.setLocation(int(ulx), int(uly))
    elif mode in ['LOWER-RIGHT', 'LOWERRIGHT', 'BOTTOMRIGHT']:
        ulx = mainWidth - (width * scale)
        uly = mainHeight - int(height * scale)
        log.tracef("...positioning window at %d X %d (Width X Height)", ulx, uly)
        window.setLocation(int(ulx), int(uly))
    elif mode in ['CENTER']:
        system.nav.centerWindow(window)   

# Tile windows that allow multiple instances.  This was specifically developed for the SQC plot window but is generic.
# It will support docked windows that have the word "CONSOLE" and are WEST
# This does not support scaling, although that is a reasonable extension
def tileWindow(window, scale=1.0): 
    mainWindow = window.parent
    mainWidth = mainWindow.getWidth()
    mainHeight = mainWindow.getHeight()
    thisWindowPath=window.getPath()
    print "==========="
    print "Main window size: %i X %i" % (mainWidth, mainHeight)
    
    width = window.getWidth()
    height = window.getHeight()
    print "User window size: %i X %i" % (width, height)

    # The origin is used to compensate for a west docked window
    originX=0
    originY=0
    
    # Determine how many of these windows are open on this client
    instanceCount = 0
    windows = system.gui.getOpenedWindows()
    for w in windows:
        windowPath = w.getPath()
        dockPosition = w.getDockPosition()
        print windowPath, ": Dock Position: ", dockPosition
        if windowPath == thisWindowPath:
            instanceCount = instanceCount + 1
            if w != window:
                firstWindow = w
        elif dockPosition == 3: 
            print "Resetting the origin for a WEST docked window..."
            originX = w.getWidth()
#            originY = w.getHeight()
#            print "The console is %i X %i (W X H)" % (w.getWidth(), w.getHeight())
        elif dockPosition == 1: 
            print "Resetting the origin for a North docked window..."
            originY = w.getHeight()
                
    if originX != 0 or originY != 0:
        mainWidth = mainWidth - originX
        mainHeight = mainHeight - originY
        print "The main window size adjusted for docked windows is : %i X %i" % (mainWidth, mainHeight)

    # The first window is always centered.    
    if instanceCount == 1:
        system.nav.centerWindow(window)
    else:
        print "Need to do some tiling!!!!"
        
        # Since the first window is never tiled, when the second window is posted move the first 
        # window to the first position
        if instanceCount == 2:
            print "Need to reposition the first window..."
            firstWindow.setLocation(originX, originY)
            if scale != 1.0:
                # I'm not sure if this returns the scaled height/width or the displayed height and width.  
                # This works if the window is originally displayed at full size, I'm not sure what it does
                # if it is originally scaled.
                width = firstWindow.getWidth()
                height = firstWindow.getHeight()
                firstWindow.setSize(int(width * scale), int(height * scale))
            
        ''' Figure out a grid based on the main window size and the child window size '''
        rows = math.floor(mainHeight / (height * scale))
        cols = math.floor(mainWidth / (width * scale))
        print "The main window has room for %i rows by %i columns" % (rows, cols) 

        row = math.ceil(instanceCount / cols)
        col = instanceCount - ((row - 1) * cols)
        
        print "This window should be placed in row: %i, column %i" % (row, col)
        ulx=originX + (col - 1) * width * scale
        uly=originY + (row - 1) * height * scale
        
        ''' These limits shouldn't be violated but check just in case to make sure the window is visible. '''
        ulx, uly = validateWindowLocation(ulx, uly, mainWidth, mainHeight)
        
        window.setLocation(int(ulx), int(uly))


def stackWindow(window, scale=1.0): 
    '''
    Tile windows that allow multiple instances.  This was specifically developed for the SQC plot window but is generic.
    It will support docked windows that have the word "CONSOLE" and are WEST
    This does not support scaling, although that is a reasonable extension
    '''
    mainWindow = window.parent
    mainWidth = mainWindow.getWidth()
    mainHeight = mainWindow.getHeight()
    thisWindowPath=window.getPath()
    stackOffset = 30
    
    log.tracef("===========")
    log.tracef("Main window size: %d X %d", mainWidth, mainHeight)
    
    width = window.getWidth()
    height = window.getHeight()
    log.tracef("User window size: %d X %d", width, height)

    ''' The origin is used to compensate for a west docked window '''
    originX=0
    originY=0
    
    ''' Determine how many of these windows are open on this client '''
    instanceCount = 0
    windows = system.gui.getOpenedWindows()
    for w in windows:
        windowPath = w.getPath()
        if windowPath == thisWindowPath:
            instanceCount = instanceCount + 1
            if w != window:
                firstWindow = w
                
        elif string.upper(windowPath).find("CONSOLE") > 0:
            '''  I'm not sure how to determine where the window is docked, so assume West for now  '''
            log.tracef("Resetting the origin for a docked console window...")
            originX = w.getWidth()
            log.tracef("The console is %d X %d (W X H)", w.getWidth(), w.getHeight())
                
    if originX != 0 or originY != 0:
        mainWidth = mainWidth - originX
        mainHeight = mainHeight - originY
        log.tracef("The main window size adjusted for a docked window is : %d X %d", mainWidth, mainHeight)

    ''' The first window is always centered. '''
    if instanceCount == 1:
        system.nav.centerWindow(window)
    else:
        log.tracef("Need to do some stacking!!!!")
        
        '''
        Since the first window is never tiled, when the second window is posted move the first window to the first position.
        '''
        if instanceCount == 2:
            log.tracef("Need to reposition the first window...")
            firstWindow.setLocation(originX, originY)
        
        ''' Calculate the location of the upper-left corner of the window so that the windows are stacked. '''
        ulx=originX + (instanceCount - 1) * stackOffset
        uly=originY + (instanceCount - 1) * stackOffset
        
        '''  These limits shouldn't be violated but check just in case to make sure the window is visible. '''
        ulx, uly = validateWindowLocation(ulx, uly, mainWidth, mainHeight)
        
        window.setLocation(int(ulx), int(uly))

def getDockOffset():
    xOffset=0
    yOffset=0
    
    windows = system.gui.getOpenedWindows()
    for w in windows:
        windowPath = w.getPath()
        if string.upper(windowPath).find("CONSOLE") > 0:
            ''' I'm not sure how to determine where the window is docked, so assume West for now '''
            log.tracef("Resetting the origin for a docked console window...")
            xOffset = w.getWidth()
            log.tracef("The console is %d X %d (W X H)", w.getWidth(), w.getHeight())
    return xOffset, yOffset

def validateWindowLocation(ulx, uly, mainWidth, mainHeight):
    '''
    These limits shouldn't be violated but check just in case to make sure the window is visible.
    '''
    if ulx < 0:
        log.tracef("Overriding min x = %d", ulx)
        ulx = 0
        
    if ulx > mainWidth:
        log.tracef("Overriding max x = %d", ulx)
        ulx = 0
        
    if uly < 0:
        log.tracef("Overriding min y = %d", uly)
        uly = 0
        
    if uly > mainHeight:
        log.tracef("Overriding max y = %d", uly)
        uly = 0
    
    return ulx, uly