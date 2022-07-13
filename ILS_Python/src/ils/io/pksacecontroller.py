'''
Created on Dec 3, 2015

@author: Pete
'''
import system
import ils.io.pkscontroller as pkscontroller
from ils.io.util import readTag, writeTag
from ils.log import getLogger
log = getLogger(__name__)

class PKSACEController(pkscontroller.PKSController):
    def __init__(self, path):
        # print "Initializing a PKS ACE controller..."
        pkscontroller.PKSController.__init__(self,path)
    
    def writeDatum(self, val, valueType):
        log.tracef("%s.writeDatum() %s - %s - %s", __name__, self.path, str(val), valueType)
        
        # Read the value that we want to write to the Processing command
        processingCommandWait = readTag(self.path + "/processingCommandWait").value

        print "Calling PKSController.writeDatum() for a PKS-ACE controller..."
        status, errorMessage = pkscontroller.PKSController.writeDatum(self, val, valueType)
        if not(status):
            return status, errorMessage
        
        log.trace("... back in PKS ACE writeDatum()!")
        
        # Write the new delay - no need to confirm this.  The is a delay in seconds.  The DCS will reset it to 0 or none after it has been processed,
        # so I don't need to reset it.
        log.tracef("Writing wait value %s to the processing command...", str(processingCommandWait))
        writeTag(self.path + "/processingCommand", processingCommandWait)
        
#        confirmed, txt = confirmWrite(self.path + "/processingCommand", processingCommandWait, timeout=60, frequency=1)
#        print "Confirmation state: ", confirmed
#        if not(confirmed):
#            return False, "Failed to confirm write of %s to %s - %s" % (str(processingCommandWait), self.path + "/processingCommand", txt)


#        log.trace("managing the processingCommand for a PKS ACE controller")

        # Restore the original delay
#        writeTag(self.path + "/processingCommand", processingCommandWaitOriginal)
#        confirmed, txt = confirmWrite(self.path + "/processingCommand", processingCommandWaitOriginal, timeout=60, frequency=1)
#        print "Confirmation state: ", confirmed
#        if not(confirmed):
#            return False, "Failed to confirm write restoring  %s to %s - %s" % (str(processingCommandWaitOriginal), self.path + "/processingCommand", txt)

        return status, errorMessage
    