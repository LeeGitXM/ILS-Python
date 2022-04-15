'''
Created on Apr 15, 2022

@author: ils
'''

import system
from ils.common.config import getDatabaseClient

from ils.log import getLogger
log = getLogger(__name__)

CONTAINER_WIDTH = 680
CONTAINER_HEIGHT = 400
CENTER_X = 10
CENTER_Y = 50
RIGHT_X = 700
DURATION = 5000
MAX_INDEX = 3

def internalFrameOpened(event):
    log.infof("In %s.internalFrameOpened()", __name__)
    db = getDatabaseClient()
    rootContainer = event.source.rootContainer

def saveCallback(event):
    log.infof("In %s.internalFrameOpened()", __name__)
    
def resetPages(rootContainer):
    print "resetPages()"
    container = rootContainer.getComponent("Page1")
    system.gui.transform(container, newX=CENTER_X, newY=CENTER_Y, newWidth=CONTAINER_WIDTH, newHeight=CONTAINER_HEIGHT)
    for page in ["Page2", "Page3"]:
        container = rootContainer.getComponent(page)
        system.gui.transform(container, newX=RIGHT_X, newY=CENTER_Y, newWidth=CONTAINER_WIDTH, newHeight=CONTAINER_HEIGHT)
    rootContainer.pageIndex = 1
    
def pageRight(rootContainer):
    '''
    Move the top page to the right
    '''
    print "pageRight()"
    pageIndex = rootContainer.pageIndex
    if pageIndex == 0:
        system.gui.messageBox("No more pages")
        return
    
    container = rootContainer.getComponent("Page" + str(pageIndex))
    system.gui.transform(container, newX=RIGHT_X, duration=DURATION)
    rootContainer.pageIndex = pageIndex - 1

def pageLeft(rootContainer):
    print "pageLeft()"
    pageIndex = rootContainer.pageIndex + 1
    if pageIndex > MAX_INDEX:
        system.gui.messageBox("No more pages")
        return
    
    container = rootContainer.getComponent("Page" + str(pageIndex))
    system.gui.transform(container, newX=CENTER_X, duration=DURATION)
    rootContainer.pageIndex = pageIndex
