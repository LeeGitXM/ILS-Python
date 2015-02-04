'''
Created on Feb 4, 2015

@author: Pete
'''

import system, string
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.diagToolkit.downlload")

#
def downloadCallback(rootContainer):
    log.info("In downloadCallback()")
    repeater=rootContainer.getComponent("Template Repeater")
    ds = repeater.templateParams
    