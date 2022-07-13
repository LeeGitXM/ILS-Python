'''
Created on Dec 1, 2014

@author: Pete
'''

from ils.io.util import readTag, writeTag
import ils.io.tdccontroller as tdccontroller
import system, string, time
import ils.io.opcoutput as opcoutput
from ils.log import getLogger
log = getLogger(__name__)

class TDCAMController(tdccontroller.TDCController):
    
    def __init__(self,path):
        tdccontroller.TDCController.__init__(self,path)
    
    '''
    For now this will inherit everything from the TDC controller
    '''
    
    def writeDatum(self, val, valueType):
        '''
        Use the TDC Controller method with the addition of an intial write to the processingCommand  
        '''
        tagPath = self.path + "/processingCommandWait"
        processingCommandWait = readTag(tagPath)
        if not(processingCommandWait.quality.isGood()):
            return False, "The quality of the Processing Command Wait <%s> was bad" % (tagPath)
        
        writeTag(self.path + "/processingCommand", processingCommandWait.value)
        
        confirmed, errorMessage = tdccontroller.TDCController.writeDatum(self, val, valueType)         
        return confirmed, errorMessage


    def writeRamp(self, val, valType, rampTime, updateFrequency, writeConfirm):
        '''
        Use the TDC Controller method with the addition of an intial write to the processingCommand  
        '''
        tagPath = self.path + "/processingCommandWait"
        processingCommandWait = readTag(tagPath)
        if not(processingCommandWait.quality.isGood()):
            return False, "The quality of the Processing Command Wait <%s> was bad" % (tagPath)
        
        writeTag(self.path + "/processingCommand", processingCommandWait.value)
        
        confirmed, errorMessage = tdccontroller.TDCController.writeRamp(self, val, valType, rampTime, updateFrequency, writeConfirm)    
        return confirmed, errorMessage
    

    def writeWithNoCheck(self, val, valueType):
        '''
        WiteWithNoCheck for a controller supports writing values to the OP, SP, or MODE, one at a time.
        '''   
        tagPath = self.path + "/processingCommandWait"
        processingCommandWait = readTag(tagPath)
        if not(processingCommandWait.quality.isGood()):
            return False, "The quality of the Processing Command Wait <%s> was bad" % (tagPath)
        
        writeTag(self.path + "/processingCommand", processingCommandWait.value)
        
        log.tracef("%s.writeWithNoCheck() %s - %s - %s", __name__, self.path, str(val), valueType)
        confirmed, errorMessage = tdccontroller.TDCController.writeWithNoCheck(self, val, valueType)  
        
        return confirmed, errorMessage