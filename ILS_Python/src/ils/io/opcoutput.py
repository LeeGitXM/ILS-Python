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
        log.tracef("In OPCOutput.checkConfig()...")
        
        # Check that the tag exists - 
        # TODO there should be a better way to call next method
        tagExists, reason = opctag.OPCTag.checkConfig(self)
        # TODO: Check if there is an item ID and an OPC server
                                               
        return tagExists, reason
 
     # This check doesn't make sense for a simple OPC tag, always return True. 
    def confirmControllerMode(self, newVal, testForZero, checkPathToValve, outputType):
        success = True
        errorMessage = ""
        return success, errorMessage
 
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
        log.tracef("%s - Confirming the write of <%s> to %s...", __name__, str(val), self.path)
 
        from ils.io.util import confirmWrite as confirmWriteUtil
        system.tag.write(self.path + '/writeStatus', 'Confirming')
        confirmation, errorMessage = confirmWriteUtil(self.path + "/value", val)
        return confirmation, errorMessage
   
    
    # Write with confirmation.
    # Assume the UDT structure of an OPC Output
    def writeDatum(self, val, valueType=""):
        log.infof("%s - Writing <%s>, <%s> to %s, an OPCOutput", __name__, str(val), str(valueType), self.path)

        if val == None or string.upper(str(val)) == 'NAN':
            val = float("NaN")

        system.tag.write(self.path + "/writeConfirmed", False)
        system.tag.write(self.path + "/writeStatus", "")
        system.tag.write(self.path + "/writeErrorMessage", "")
                               
        status,reason = self.checkConfig()
        if status == False :              
            system.tag.write(self.path + "/writeStatus", "Failure")
            system.tag.write(self.path + "/writeErrorMessage", reason)
            log.warnf("%s - Aborting write to %s, checkConfig failed due to: %s", __name__, self.path, reason)
            return status,reason
 
        # Update the status to "Writing"
        system.tag.write(self.path + "/writeStatus", "Writing Value")
 
        # Write the value to the OPC tag
        log.tracef("%s - Writing value <%s> to %s/value", __name__, str(val), self.path)
        status = system.tag.write(self.path + "/value", val)
        log.tracef("%s - Write status: %s", __name__, status)
                               
        status, msg = self.confirmWrite(val)
 
        if status:
            log.tracef("%s - Confirmed: %s - %s - %s", __name__, self.path, status, msg)
            system.tag.write(self.path + "/writeStatus", "Success")
            system.tag.write(self.path + "/writeConfirmed", True)
        else:
            log.errorf("%s - Failed to confirm write of <%s> to %s because %s", __name__, str(val), self.path, msg)
            system.tag.write(self.path + "/writeStatus", "Failure")
            system.tag.write(self.path + "/writeMessage", msg)
 
        return status, msg
    
    # Write with NO confirmation.
    # Assume the UDT structure of an OPC Output
    def writeWithNoCheck(self, val, valueType=""):
        
        if val == None or string.upper(str(val)) == 'NAN':
            val = float("NaN")

        log.infof("%s.writeWithNoCheck() - Writing <%s> to %s, an OPCOutput with no confirmation", __name__, str(val), self.path)

        system.tag.write(self.path + "/writeConfirmed", False)
        system.tag.write(self.path + "/writeStatus", "")
        system.tag.write(self.path + "/writeErrorMessage", "")
                               
        status,reason = self.checkConfig()

        if status == False :              
            system.tag.write(self.path + "/writeStatus", "Failure")
            system.tag.write(self.path + "/writeErrorMessage", reason)
            log.warnf("%s - Aborting write to %s, checkConfig failed due to: %s", __name__, self.path, reason)
            return status,reason
 
        # Update the status to "Writing"
        system.tag.write(self.path + "/writeStatus", "Writing Value")
 
        # Write the value to the OPC tag
        log.tracef("%s - Writing value <%s> to %s/value", __name__, str(val), self.path)
        status = system.tag.write(self.path + "/value", val)
        log.tracef("%s - Write status: %s", __name__, status)
                               
        if status == 0:
            success = False
            errorMessage = "Write failed immediately"
            system.tag.write(self.path + "/writeStatus", "Failure")
        else:
            success = True
            errorMessage = ""
            system.tag.write(self.path + "/writeStatus", "Success")
            
        log.tracef("%s - Write Status: %s - %s - %s", __name__, self.path, str(success), errorMessage)
 
        return success, errorMessage