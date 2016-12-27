'''
Copyright 2014 ILS Automation

Either a float or text output to OPC.

Created on Jul 9, 2014
@author: phassler
'''
import ils
import ils.io
import ils.io.opctag as opctag
import system, string

log = system.util.getLogger("com.ils.io")


class OPCOutput(opctag.OPCTag):
    def __init__(self,path):
        opctag.OPCTag.__init__(self,path)
        
    # Check some basic things about this OPC tag to determine if a write is likely to succeed!
    def checkConfig(self):
        log.trace("In OPCOutput.checkConfig()...")
        
        # Check that the tag exists - 
        # TODO there should be a better way to call next method
        tagExists, reason = opctag.OPCTag.checkConfig(self)
        # TODO: Check if there is an item ID and an OPC server
                                               
        return tagExists, reason
 
    # Reset the UDT in preparation for a write 
    def reset(self):
        status = True
        msg = ""
        system.tag.write(self.path + '/command', '')
        system.tag.write(self.path + '/badValue', False)
        system.tag.write(self.path + '/writeConfirmed', False)
        system.tag.write(self.path + '/writeErrorMessage', '')
        system.tag.write(self.path + '/writeStatus', 'Reset')
        return status, msg
 
 
    # Implement a simple write confirmation.  Use the standard utility routine to perform the check.
    def confirmWrite(self, val):  
        log.trace("Confirming the write of <%s> to %s..." % (str(val), self.path))
 
        from ils.io.util import confirmWrite
        system.tag.write(self.path + '/writeStatus', 'Confirming')
        confirmation, errorMessage = confirmWrite(self.path + "/value", val)
        return confirmation, errorMessage
   
    
    # Write with confirmation.
    # Assume the UDT structure of an OPC Output
    def writeDatum(self, val, valueType=""):
        log.info("Writing <%s>, <%s> to %s, an OPCOutput" % (str(val), str(valueType), self.path))

        if val == None or string.upper(str(val)) == 'NAN':
            val = float("NaN")

        system.tag.write(self.path + "/writeConfirmed", False)
        system.tag.write(self.path + "/writeStatus", "")
        system.tag.write(self.path + "/writeErrorMessage", "")
                               
        status,reason = self.checkConfig()
        if status == False :              
            system.tag.write(self.path + "/writeStatus", "Failure")
            system.tag.write(self.path + "/writeErrorMessage", reason)
            log.warn("* Aborting write to %s, checkConfig failed due to: %s" % (self.path, reason))
            return status,reason
 
        # Update the status to "Writing"
        system.tag.write(self.path + "/writeStatus", "Writing Value")
 
        # Write the value to the OPC tag
        log.trace("  Writing value <%s> to %s/value" % (str(val), self.path))
        status = system.tag.write(self.path + "/value", val)
        log.trace("  Write status: %s" % (status))
                               
        status, msg = self.confirmWrite(val)
 
        if status:
            log.trace("Confirmed: %s - %s - %s" % (self.path, status, msg))
            system.tag.write(self.path + "/writeStatus", "Success")
            system.tag.write(self.path + "/writeConfirmed", True)
        else:
            log.error("Failed to confirm write of <%s> to %s because %s" % (str(val), self.path, msg))
            system.tag.write(self.path + "/writeStatus", "Failure")
            system.tag.write(self.path + "/writeMessage", msg)
 
        return status, msg
    
    # Write with NO confirmation.
    # Assume the UDT structure of an OPC Output
    def writeWithNoCheck(self, val):
        if val == None:
            val = float("NaN")

        log.info("Writing <%s> to %s, an OPCOutput with no confirmation" % (str(val), self.path))

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
        system.tag.write(self.path + "/writeStatus", "Writing Value")
 
        # Write the value to the OPC tag
        log.trace("  Writing value <%s> to %s/tag" % (str(val), self.path))
        status = system.tag.write(self.path + "/value", val)
        log.trace("  Write status: %s" % (status))
                               
        if status == 0:
            success = False
            errorMessage = "Write failed immediately"
            system.tag.write(self.path + "/writeStatus", "Failure")
        else:
            success = True
            errorMessage = ""
            system.tag.write(self.path + "/writeStatus", "Success")
            
        log.trace("Write Status: %s - %s - %s" % (self.path, str(success), errorMessage))
 
        return success, errorMessage
