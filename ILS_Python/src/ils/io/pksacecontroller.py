'''
Created on Dec 3, 2015

@author: Pete
'''
import system
import ils.io.pkscontroller as pkscontroller
from ils.io.util import confirmWrite
log = system.util.getLogger("com.ils.io")

class PKSACEController(pkscontroller.PKSController):
    def __init__(self, path):
        # print "Initializing a PKS ACE controller..."
        pkscontroller.PKSController.__init__(self,path)
    
    def writeDatum(self, val, valueType):
        log.trace("pksAceController.writeDatum() %s - %s - %s" % (self.path, str(val), valueType))
        
        processingCommandWaitTagPath=self.path + "/processingCommandWait"
        processingCommandValueTagPath=self.path + "/processingCommand"
        
        # Read the value that we want to Processing command value and the value that is currently there that we will restore at the end
        processingCommandWait = system.tag.read(processingCommandWaitTagPath).value
        processingCommandWaitOriginal = system.tag.read(processingCommandValueTagPath).value
        
        log.trace("The current wait value is %s, the value we will write is %s" % (str(processingCommandWaitOriginal), str(processingCommandWait)))

        # Write the new delay
        system.tag.write(self.path + "/processingCommand", processingCommandWait)
        confirmed, txt = confirmWrite(self.path + "/processingCommand", processingCommandWait, timeout=60, frequency=1)
        print "Confirmation state: ", confirmed
        if not(confirmed):
            return False, "Failed to confirm write of %s to %s - %s" % (str(processingCommandWait), self.path + "/processingCommand", txt)
        
        print "Specializing writeDatum for a PKS-ACE controller..."
        status, errorMessage = pkscontroller.PKSController.writeDatum(self, val, valueType)
        if not(status):
            return status, errorMessage
        
        print "... back in PKS ACE writeDatum()!"

        log.trace("managing the processingCommand for a PKS ACE controller")

        # Restore the original delay
        system.tag.write(self.path + "/processingCommand", processingCommandWaitOriginal)
        confirmed, txt = confirmWrite(self.path + "/processingCommand", processingCommandWaitOriginal, timeout=60, frequency=1)
        print "Confirmation state: ", confirmed
        if not(confirmed):
            return False, "Failed to confirm write restoring  %s to %s - %s" % (str(processingCommandWaitOriginal), self.path + "/processingCommand", txt)

        return status, errorMessage