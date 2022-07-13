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
from ils.io.util import confirmWrite, readTag, getProviderFromTagPath

from ils.log import getLogger
log = getLogger(__name__)

class OPCConditionalOutput(opcoutput.OPCOutput):
    PERMISSIVE_LATENCY_TIME = 0.0
    
    def __init__(self,path):
        tagProvider = getProviderFromTagPath(path)
        self.PERMISSIVE_LATENCY_TIME = readTag("[%s]Configuration/Common/opcPermissiveLatencySeconds" % (tagProvider)).value
        opcoutput.OPCOutput.__init__(self,path)

    # Reset the memory tags - this does not write to OPC!
    def reset(self):
        # reset all of the inherited memory tags
        opcoutput.OPCOutput.reset(self)

        # reset the permissive related memory tags
        system.tag.writeBlocking([self.path + '/permissiveAsFound', self.path + '/permissiveConfirmation'], ['', False])

        return True, ""

    # This check doesn't make sense for a simple OPC tag, always return True. 
    def confirmControllerMode(self, newVal, testForZero, checkPathToValve, outputType):
        success = True
        errorMessage = ""
        itemId = ""
        return success, errorMessage, itemId
    
    def writeWithNoCheck(self, val, valueType=""):
        log.tracef("In %s.writeWithNoCheck()...", __name__)      
        status, msg = self.writer(val, False, valueType)
        return status, msg
    
    # Write with confirmation.
    # Assume the UDT structure of an OPC Output
    def writeDatum(self, val, valueType=""):
        log.tracef("In %s.writeDatum()...", __name__)
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
        system.tag.writeBlocking([self.path + "/writeConfirmed", self.path + "/writeStatus", self.path + "/writeErrorMessage"], [False, "", ""])
                               
        status,reason = self.checkConfig()
        if status == False :              
            system.tag.writeBlocking([self.path + "/writeStatus", self.path + "/writeErrorMessage"], ["Failure", reason])
            log.info("Aborting write to %s, checkConfig failed due to: %s" % (self.path, reason))
            return status,reason
 
        # Update the status to "Writing"
        log.tracef("   %s - writing permissive...", self.path)
        system.tag.writeBlocking([self.path + "/writeStatus"], ["Writing Permissive"])
 
        # Read the current permissive so that we can put it back the way is was when we are done
        permissiveAsFound = readTag(self.path + "/permissive").value
        log.info("   %s - the permissive as found is: <%s>" % (self.path, permissiveAsFound))
        time.sleep(1)
        log.info("Return from 1 second sleep...")
        
        # Get from the configuration of the UDT the value to write to the permissive and whether or not it needs to be confirmed
        permissiveValue = readTag(self.path + "/permissiveValue").value
        permissiveConfirmation = readTag(self.path + "/permissiveConfirmation").value
        
        # Write the permissive value to the permissive tag and wait until it gets there
        log.info("   %s - writing permissive %s" % (self.path, permissiveValue))
        system.tag.writeBlocking([self.path + "/permissive"], [permissiveValue])
        
        # Confirm the permissive if necessary.  If the UDT is configured for confirmation, then it MUST be confirmed 
        # for the write to proceed
        if permissiveConfirmation:
            confirmed, errorMessage = confirmWrite(self.path + "/permissive", permissiveValue)
 
            if confirmed:
                log.trace("Confirmed Permissive write: %s - %s" % (self.path, permissiveValue))
            else:
                log.error("Failed to confirm permissive write of <%s> to %s because %s" % (str(permissiveValue), self.path, errorMessage))
                system.tag.writeBlocking([self.path + "/writeStatus", self.path + "/writeErrorMessage"], ["Failure", errorMessage])
                return confirmed, errorMessage
        else:
            log.info("...dwelling in lieu of permissive confirmation...")
            time.sleep(self.PERMISSIVE_LATENCY_TIME)
            
        # If we got this far, then the permissive was successfully written (or we don't care about confirming it, so
        # write the value to the OPC tag
        log.trace("  Writing value <%s> to %s/tag" % (str(val), self.path))
        system.tag.writeBlocking([self.path + "/value", self.path + "/writeStatus"], [val, "Writing value"])
        status = True

        if confirm:
            # Determine if the write was successful
            confirmTagPath = self.path + "/value"
            log.infof("Confirming write of %s to %s...", str(val), confirmTagPath)
            confirmed, errorMessage = self.confirmWrite(val, confirmTagPath)
     
            if confirmed:
                log.trace("Confirmed: %s - %s" % (self.path, str(val)))
                system.tag.writeBlocking([self.path + "/writeStatus", self.path + "/writeConfirmed"], ["Success", True])
                status = True
                msg = ""
            else:
                log.error("Failed to confirm write of <%s> to %s because %s" % (str(val), self.path, errorMessage))
                system.tag.writeBlocking([self.path + "/writeStatus", self.path + "/writeErrorMessage"], ["Failure", errorMessage])
                status = False
                msg = errorMessage   
        else:
            ''' If this was a write with no confirm then if we got this far we were successful.  '''
            system.tag.writeBlocking([self.path + "/writeStatus"], ["Success"])
            
        # Return the permissive to its original value
        # Write the permissive value to the permissive tag and wait until it gets there
        time.sleep(self.PERMISSIVE_LATENCY_TIME)
        log.info("  Restoring permissive to <%s>" % (permissiveAsFound))

        system.tag.writeBlocking([self.path + "/permissive"], [permissiveAsFound])
        if permissiveConfirmation:
            confirmed, errorMessage = confirmWrite(self.path + "/permissive", permissiveAsFound)

            if confirmed:
                status = True
                msg = ""
                log.tracef("Confirmed Permissive restore: %s - %s", self.path, status)
            else:
                status = False
                log.error("Failed to confirm permissive write of <%s> to %s because %s" % (str(val), self.path, errorMessage))
                system.tag.writeBlocking([self.path + "/writeStatus", self.path + "/writeErrorMessage"], ["Failure", errorMessage])
                return status, errorMessage
        
        return status, msg