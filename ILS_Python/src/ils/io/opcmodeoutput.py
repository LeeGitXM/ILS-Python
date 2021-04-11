'''
Created on Apr 9, 2021

@author: phass

This class is provided as work around to a problem found on certain DCS systems that have the annoying "feature"
of automatically setting the "Normal Mode" tag of a controller to the value of the mode tag whnever we set the mode tag.
This means that when the operator presses his "Return to Normal Mode" button it doesn't do what it should.  So this class,
which is used for the mode attribute of every controller.This class adds two attributes to an OPC Output class:  the normal 
mode opc tag and a returnToNormal boolean memory tag.  The return to normal strategy will only be employed if the 
quality of normal mode is good AND the returnToNormal tag is True (the default is False).  We restore the tag in an 
asynchronous thread so as not to slow down the write operation.  Because there is some mechanism in the DCS that 
moves the mode value from the mode tag to the normal mode tag, and we don't know how long that takes, we will put a 
dwell before we restore just to make sure we do it AFTER the DCS is done doing its thing. 
'''

import ils
import ils.io
import ils.io.opcoutput as opcoutput
import system, string, time

from ils.log.LogRecorder import LogRecorder
log = LogRecorder(__name__)

class OPCModeOutput(opcoutput.OPCOutput):
    '''
    classdocs
    '''  
    def __init__(self, path):
        self.normalValueAsFound = None
        opcoutput.OPCOutput.__init__(self, path)
    
    def writeDatum(self, val, valueType="", confirmTagPath=""):
        log.tracef("%s.writeDatum() - Writing <%s>, <%s> to %s, an OPCModeOutput", __name__, str(val), str(valueType), self.path)
        
        self.normalValueAsFound = system.tag.read(self.path + '/normalValue')
        log.tracef("The mode as found is: %s", self.normalValueAsFound.value)
        
        status, msg = opcoutput.OPCOutput.writeDatum(self, val, valueType, confirmTagPath)
        
        returnToNormal = system.tag.read(self.path + '/returnToNormal').value
        
        if returnToNormal and self.normalValueAsFound.quality.isGood():

            def restore(path=self.path + '/normalValue', val=self.normalValueAsFound.value):
                OPC_LATENCY_TIME = system.tag.read("[XOM]Configuration/Common/opcTagLatencySeconds").value
                log.tracef("sleeping before restoring...")
                time.sleep(OPC_LATENCY_TIME)
                log.tracef("Restoring the NORMAL mode value <%s> to <%s>...", val, path)
                system.tag.write(path, val)
            
            log.tracef("Calling restore asynchronously...")
            system.util.invokeAsynchronous(restore)
            log.tracef("...done calling...")

        log.tracef("Leaving %s.writeDatum()", __name__) 
        return status, msg
    
    def writeWithNoCheck(self, val, valueType=""):
        log.tracef("%s.writeWithNoCheck() - Writing <%s>, <%s> to %s, an OPCModeOutput", __name__, str(val), str(valueType), self.path)
    
        self.normalValueAsFound = system.tag.read(self.path + '/normalValue')
        log.tracef("The mode as found is: %s", self.normalValueAsFound.value)
        
        status, msg = opcoutput.OPCOutput.writeWithNoCheck(self, val, valueType)
        
        returnToNormal = system.tag.read(self.path + '/returnToNormal').value
        
        if returnToNormal and self.normalValueAsFound.quality.isGood():

            def restore(path=self.path + '/normalValue', val=self.normalValueAsFound.value):
                OPC_LATENCY_TIME = system.tag.read("[XOM]Configuration/Common/opcTagLatencySeconds").value
                log.tracef("sleeping before restoring...")
                time.sleep(OPC_LATENCY_TIME)
                log.tracef("Restoring the NORMAL mode value <%s> to <%s>...", val, path)
                system.tag.write(path, val)
            
            log.tracef("Calling restore asynchronously...")
            system.util.invokeAsynchronous(restore)
            log.tracef("...done calling...")
                
        log.tracef("Leaving %s.writeWithNoCheck()", __name__) 
        return status, msg