'''
Created on Dec 1, 2014

@author: Pete
'''

import ils.io.controller as controller
#import system
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.io")

class TDCController(controller.Controller):
    def __init__(self,path):
        controller.Controller.__init__(self,path)

    # Reset the UDT in preparation for a write 
    def reset(self):
        log.trace('Resetting a TDCController...')
