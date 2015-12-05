'''
Created on Dec 3, 2015

@author: Pete
'''
import system
import ils.io.pkscontroller as pkscontroller
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.io")

class PKSACEController(pkscontroller.PKSController):
    def __init__(self,path):
        pkscontroller.PKSController.__init__(self,path)
    
    def writeDatum(self):
        print "Specializing writeDatum for a PKS-ACE controller..."
        pkscontroller.PKSController.writeDatum(self)
        print "... back in PKS ACE writeDatum()!"

        # Read the value that we want to write from the UDT
        processingCommandWait = system.tag.read(self.path + "/processingCommandWait").value
        
        # Write the value to the controller
        system.tag.write(self.path + "/processingCommand/value", processingCommandWait)
