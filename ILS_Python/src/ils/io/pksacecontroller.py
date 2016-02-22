'''
Created on Dec 3, 2015

@author: Pete
'''
import system
import ils.io.pkscontroller as pkscontroller
log = system.util.getLogger("com.ils.io")

class PKSACEController(pkscontroller.PKSController):
    def __init__(self, path):
        # print "Initializing a PKS ACE controller..."
        pkscontroller.PKSController.__init__(self,path)
    
    def writeDatum(self):
        #print "Specializing writeDatum for a PKS-ACE controller..."
        status, errorMessage = pkscontroller.PKSController.writeDatum(self)
        #print "... back in PKS ACE writeDatum()!"

        log.trace("managing the processingCommand for a PKS ACE controller")
        # Read the value that we want to write from the UDT
        tagPath=self.path + "/processingCommandWait"
        processingCommandWait = system.tag.read(tagPath).value

        # Write the value to the controller
        system.tag.write(self.path + "/processingCommand/value", processingCommandWait)
        
        return status, errorMessage