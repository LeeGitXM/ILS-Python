'''
Created on Mar 29, 2018

@author: phass
'''

import system
import ils.io.pkscontroller as pkscontroller
import ils.io.pksacecontroller as pksacecontroller
import ils.io.pksrampcontroller as pksrampcontroller
import ils.io.opcoutput as opcoutput
log = system.util.getLogger("com.ils.io")

class PKSACERampController(pksrampcontroller.PKSRampController):
    
    def __init__(self,path):
        pksrampcontroller.PKSRampController.__init__(self,path)
        
    '''
    For now this will inherit everything from the pks ramp controller
    '''
    
    def writeDatum(self, val, valueType):
        log.tracef("%s.writeDatum() %s - %s - %s", __name__, self.path, str(val), valueType)
        
        # Read the value that we want to write to the Processing command
        processingCommandWait = system.tag.read(self.path + "/processingCommandWait").value

        log.trace("Calling PKSController.writeDatum() for a PKS-ACE controller...")
        status, errorMessage = pksrampcontroller.PKSRampController.writeDatum(self, val, valueType)
        if not(status):
            return status, errorMessage
        
        log.trace("... back in PKS ACE writeDatum()!")
        
        # Write the new delay - no need to confirm this.  The is a delay in seconds.  The DCS will reset it to 0 or none after it has been processed,
        # so I don't need to reset it.
        log.tracef("Writing wait value %s to the processing command...", str(processingCommandWait))
        system.tag.write(self.path + "/processingCommand", processingCommandWait)
        
        # Write the new delay - no need to confirm this.  The is a delay in seconds.  The DCS will reset it to 0 or none after it has been processed,
        # so I don't need to reset it.
        log.tracef("Writing wait value %s to the processing command...", str(processingCommandWait))
        system.tag.write(self.path + "/processingCommand", processingCommandWait)
        return status, errorMessage
    
    
    def writeRamp(self, val, valueType, rampTime, updateFrequency, writeConfirm):       
        log.tracef("%s.writeRamp() %s - %s - %s", __name__, self.path, str(val), valueType)
        
        # Read the value that we want to write to the Processing command
        processingCommandWait = system.tag.read(self.path + "/processingCommandWait").value

        log.tracef("Calling PKSRampController.writeRamp() for a PKS ACE Ramp controller...")
        status, errorMessage = pksrampcontroller.PKSRampController.writeRamp(self, val, valueType, rampTime, updateFrequency, writeConfirm)
        if not(status):
            return status, errorMessage
        
        log.tracef("... back in %s.writeRamp()!", __name__)
        
        # Write the new delay - no need to confirm this.  The is a delay in seconds.  The DCS will reset it to 0 or none after it has been processed,
        # so I don't need to reset it.
        log.tracef("Writing wait value %s to the processing command...", str(processingCommandWait))
        system.tag.write(self.path + "/processingCommand", processingCommandWait)
        
        return status, errorMessage