'''
Copyright 2014 ILS Automation

This can be a float or a text

Created on Jul 9, 2014

@author: phassler
'''
import ils.io.opcoutput as opcoutput
import ils.io.opctag as basicio
import string
import system
import time
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
from ils.io.util import confirmWrite

log = LogUtil.getLogger("com.ils.io")


class OPCConditionalOutput(opcoutput.OPCOutput):
    def __init__(self,path):
        opcoutput.OPCOutput.__init__(self,path)

    # Reset the memory tags - this does not write to OPC!
    def reset(self):
        # reset all of the inherited memory tags
        status, msg = opcoutput.OPCOutput.reset(self)

        # reset the permissive related memory tags
        system.tag.write(self.path + '/permissiveAsFound', '')
        system.tag.write(self.path + '/permissiveConfirmation', False)

        return True, ""


    # Write with confirmation.
    # Assume the UDT structure of an OPC Output
    def writeDatum(self):
        
        # Get the value to be written - this must be there BEFORE the command is set       
        val = system.tag.read(self.path + "/writeValue").value
        if val == None:
            val = float("NaN")
        
        log.info("Writing <%s> to %s, an OPCConditionalOutput" % (str(val), self.path))

        log.trace("Initializing %s status and  to False" % (self.path))                   
        system.tag.write(self.path + "/writeConfirmed", False)
        system.tag.write(self.path + "/writeStatus", "")
        system.tag.write(self.path + "/writeErrorMessage", "")
                               
        status,reason = self.checkConfig()
        if status == False :              
            system.tag.write(self.path + "/writeStatus", "Failure")
            system.tag.write(self.path + "/writeErrorMessage", reason)
            log.info("Aborting write to %s, checkConfig failed due to: %s" % (self.path, reason))
            return status,reason
 
        # Update the status to "Writing"
        system.tag.write(self.path + "/writeStatus", "Writing Permissive")
 
        # Read the current permissive and save it so that we can put it back the way is was when we are donw
        permissiveAsFound = system.tag.read(self.path + "/permissive").value
        system.tag.write(self.path + "/permissiveAsFound", permissiveAsFound)
        
        # Get from the configuration of the UDT the value to write to the permissive and whether or not it needs to be confirmed
        permissiveValue = system.tag.read(self.path + "/permissiveValue").value
        permissiveConfirmation = system.tag.read(self.path + "/permissiveConfirmation").value
        
        # Write the permissive value to the permissive tag and wait until it gets there
        system.tag.write(self.path + "/permissive", permissiveValue)
        
        # Confirm the permissive if necessary.  If the UDT is configured for confirmation, then it MUST be confirmed 
        # for the write to proceed
        if permissiveConfirmation:
            confirmed, errorMessage = confirmWrite(self.path + "/permissive", permissiveValue)
 
            if confirmed:
                log.trace("Confirmed Permissive write: %s - %s" % (self.path, permissiveValue))
            else:
                log.error("Failed to confirm permissive write of <%s> to %s because %s" % (str(permissiveValue), self.path, errorMessage))
                system.tag.write(self.path + "/writeStatus", "Failure")
                system.tag.write(self.path + "/writeMessage", errorMessage)
                return confirmed, errorMessage
            
        # If we got this far, then the permissive was successfully written (or we don't care about confirming it, so
        # write the value to the OPC tag
        log.trace("  Writing value <%s> to %s/tag" % (str(val), self.path))
        status = system.tag.write(self.path + "/value", val)
        system.tag.write(self.path + "/writeStatus", "Writing value")
        log.trace("  Write status: %s" % (status))

        # Determine if the write was successful
        confirmed, errorMessage = self.confirmWrite(val)
 
        if confirmed:
            log.trace("Confirmed: %s - %s" % (self.path, str(val)))
            system.tag.write(self.path + "/writeStatus", "Success")
            system.tag.write(self.path + "/writeConfirmed", True)
            status = True
            msg = ""
        else:
            log.error("Failed to confirm write of <%s> to %s because %s" % (str(val), self.path, errorMessage))
            system.tag.write(self.path + "/writeStatus", "Failure")
            system.tag.write(self.path + "/writeMessage", errorMessage)
            status = False
            msg = errorMessage
            
        # Return the permissive to its original value
        # Write the permissive value to the permissive tag and wait until it gets there
        # TODO wait for a latency time
        log.trace("  Restoring permissive")
        system.tag.write(self.path + "/permissive", permissiveAsFound)
        if permissiveConfirmation:
            confirmed, errorMessage = confirmWrite(self.path + "/permissive", permissiveAsFound)
 
            if confirmed:
                log.trace("Confirmed Permissive restore: %s - %s - %s" % (self.path, status, msg))
            else:
                log.error("Failed to confirm permissive write of <%s> to %s because %s" % (str(val), self.path, errorMessage))
                system.tag.write(self.path + "/writeStatus", "Failure")
                system.tag.write(self.path + "/writeMessage", errorMessage)
                return status, errorMessage
        
        return status, msg
