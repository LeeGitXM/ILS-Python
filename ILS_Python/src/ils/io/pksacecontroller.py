'''
Created on Dec 3, 2015

@author: Pete
'''
import system, string, time
import ils.io.pkscontroller as pkscontroller
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
from java.util import Date
log = LogUtil.getLogger("com.ils.io")

class PKSACEController(pkscontroller.PKSController):
    def __init__(self,path):
        pkscontroller.PKSController.__init__(self,path)
    
    