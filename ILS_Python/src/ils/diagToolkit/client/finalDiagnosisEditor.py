'''
Created on Apr 15, 2022

@author: ils
'''

import system
from ils.common.config import getDatabaseClient

from ils.log import getLogger
log = getLogger(__name__)

def internalFrameOpened(event):
    log.infof("In %s.internalFrameOpened()", __name__)
    db = getDatabaseClient()
    rootContainer = event.source.rootContainer

def saveCallback(event):
    log.infof("In %s.internalFrameOpened()", __name__)
