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
    PERMISSIVE_LATENCY_TIME = 0.0
    
    def __init__(self,path):
        self.PERMISSIVE_LATENCY_TIME = system.tag.read("[XOM]Configuration/Common/opcPermissiveLatencySeconds").value
        opcoutput.OPCOutput.__init__(self,path)

    # Reset the memory tags - this does not write to OPC!
    def reset(self):
        # reset all of the inherited memory tags
        status, msg = opcoutput.OPCOutput.reset(self)

        # reset the permissive related memory tags
        system.tag.write(self.path + '/permissiveAsFound', '')
        system.tag.write(self.path + '/permissiveConfirmation', False)

        return True, ""

    # This check doesn't make sense for a simple OPC tag, always return True. 
    def confirmControllerMode(self, newVal, testForZero, checkPathToValve, outputType):
        success = True
        errorMessage = ""
        return success, errorMessage
    
    def writeWithNoCheck(self, val, valueType=""):
        print "In %s.writeWithNoCheck()..." % (__name__)      
        status, msg = self.writer(val, False, valueType)
        return status, msg
    
    # Write with confirmation.
    # Assume the UDT structure of an OPC Output
    def writeDatum(self, val, valueType=""):
        print "In %s.writeDatum()..." % (__name__)
        status, msg = self.writer(val, True, valueType)
        return status, msg
    
    '''
    This is a private method that is used by both of the public methods (writeDatum and writeWithNoCheck)
    '''
    def writer(self, val, confirm, valueType=""):
        log.info("Writing <%s>, <%s>, <confirm: %s> to %s, an OPCConditionalOutput" % (str(val), str(valueType), str(confirm), self.path))
        msg = ""

        if val == None:
            val = float("NaN")

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
        log.tracef("   %s - writing permissive...", self.path)
        system.tag.write(self.path + "/writeStatus", "Writing Permissive")
 
        # Read the current permissive so that we can put it back the way is was when we are done
        permissiveAsFound = system.tag.read(self.path + "/permissive").value
        log.info("   %s - the permissive as found is: <%s>" % (self.path, permissiveAsFound))
        time.sleep(1)
        log.info("Return from 1 second sleep...")
        
        # Get from the configuration of the UDT the value to write to the permissive and whether or not it needs to be confirmed
        permissiveValue = system.tag.read(self.path + "/permissiveValue").value
        permissiveConfirmation = system.tag.read(self.path + "/permissiveConfirmation").value
        
        # Write the permissive value to the permissive tag and wait until it gets there
        log.info("   %s - writing permissive %s" % (self.path, permissiveValue))
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
        else:
            log.info("...dwelling in lieu of permissive confirmation...")
            time.sleep(self.PERMISSIVE_LATENCY_TIME)
            
        # If we got this far, then the permissive was successfully written (or we don't care about confirming it, so
        # write the value to the OPC tag
        log.trace("  Writing value <%s> to %s/tag" % (str(val), self.path))
        status = system.tag.write(self.path + "/value", val)
        system.tag.write(self.path + "/writeStatus", "Writing value")
        log.trace("  Write status: %s" % (status))

        if confirm:
            # Determine if the write was successful
            log.infof("Confirming write of %s to %s...", str(val), self.path)
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
        else:
            ''' If this was a write with no confirm then if we got this far we were successful.  '''
            system.tag.write(self.path + "/writeStatus", "Success")
            
        # Return the permissive to its original value
        # Write the permissive value to the permissive tag and wait until it gets there
        time.sleep(self.PERMISSIVE_LATENCY_TIME)
        log.info("  Restoring permissive to <%s>" % (permissiveAsFound))

        system.tag.write(self.path + "/permissive", permissiveAsFound)
        if permissiveConfirmation:
            confirmed, errorMessage = confirmWrite(self.path + "/permissive", permissiveAsFound)

            if confirmed:
                status = True
                msg = ""
                log.tracef("Confirmed Permissive restore: %s - %s", self.path, status)
            else:
                status = False
                log.error("Failed to confirm permissive write of <%s> to %s because %s" % (str(val), self.path, errorMessage))
                system.tag.write(self.path + "/writeStatus", "Failure")
                system.tag.write(self.path + "/writeMessage", errorMessage)
                return status, errorMessage
        
        return status, msg