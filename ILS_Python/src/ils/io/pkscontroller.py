'''
Created on Dec 1, 2014

@author: Pete
'''

import system, string, time
import ils.io.controller as controller
import ils.io.opcoutput as opcoutput
from java.util import Date
log = system.util.getLogger("com.ils.io")

class PKSController(controller.Controller):
    opTag = None
    spTag = None
    
    def __init__(self,path):
        controller.Controller.__init__(self,path)
        
        self.spTag = opcoutput.OPCOutput(path + '/sp')
        self.opTag = opcoutput.OPCOutput(path + '/op')

    # Reset the UDT in preparation for a write 
    def reset(self):
        success = True
        errorMessage = ""
        log.trace('Resetting a PKSController...')       
        
        system.tag.write(self.path + '/badValue', False)
        system.tag.write(self.path + '/writeErrorMessage', '')
        system.tag.write(self.path + '/writeConfirmed', False)
        system.tag.write(self.path + '/writeStatus', '')
        
        for embeddedTag in ['/mode', '/op', '/sp']:
            tagPath = self.path + embeddedTag
            system.tag.write(tagPath + '/badValue', False)
            system.tag.write(tagPath + '/writeErrorMessage', '')
            system.tag.write(tagPath + '/writeConfirmed', False)
            system.tag.write(tagPath + '/writeStatus', '')

        return success, errorMessage

    
    # writeDatum for a controller supports writing values to the OP, SP, or MODE, one at a time.
    def writeDatum(self, val, valueType):      
        log.trace("pkscontroller.writeDatum() %s - %s - %s" % (self.path, str(val), valueType))
        if string.upper(valueType) in ["SP", "SETPOINT"]:
            tagRoot = self.path + '/sp'
            targetTag = self.spTag
            valueType = 'sp'
        elif string.upper(valueType) in ["OP", "OUTPUT"]:
            tagRoot = self.path + '/op'
            targetTag = self.opTag
            valueType = 'op'
        elif string.upper(valueType) in ["MODE"]:
            tagRoot = self.path + '/mode'
            targetTag = self.modeTag
            valueType = 'mode'
        else:
            log.error("Unexpected value Type: <%s>" % (valueType))
            raise Exception("Unexpected value Type: <%s>" % (valueType))

        # Check the basic configuration of the tag we are trying to write to.
        success, errorMessage = self.checkConfig(tagRoot + "/value")
        if not(success):
            system.tag.write(self.path + "/writeStatus", "Failure")
            system.tag.write(self.path + "/writeErrorMessage", errorMessage)
            log.info("Aborting write to %s, checkConfig failed due to: %s" % (tagRoot, errorMessage))
            return False, errorMessage

        # Check the basic configuration of the permissive of the controller we are writing to.
        success, errorMessage = self.checkConfig(self.path + '/permissive')
        if not(success):
            system.tag.write(self.path + "/writeStatus", "Failure")
            system.tag.write(self.path + "/writeErrorMessage", errorMessage)
            log.info("Aborting write to %s, checkConfig failed due to: %s" % (self.path + '/permissive', errorMessage))
            return False, errorMessage
        
        # reset the UDT
        self.reset()
        time.sleep(1)
        
        #----------------------
        # Set the permissive
        #----------------------
        
        log.trace("Writing permissive...")
        
        # Update the status to "Writing"
        system.tag.write(self.path + "/writeStatus", "Writing Permissive")
 
        # Read the current permissive and save it so that we can put it back the way is was when we are done
        permissiveAsFound = system.tag.read(self.path + "/permissive").value
        log.trace("   permisive as found: %s" % (permissiveAsFound))
        
        # Get from the configuration of the UDT the value to write to the permissive and whether or not it needs to be confirmed
        permissiveValue = system.tag.read(self.path + "/permissiveValue").value
        permissiveConfirmation = system.tag.read(self.path + "/permissiveConfirmation").value
        
        # Write the permissive value to the permissive tag and wait until it gets there
        log.trace("   writing permissive value: %s" % (permissiveValue))
        system.tag.write(self.path + "/permissive", permissiveValue)
        
        # Confirm the permissive if necessary.  If the UDT is configured for confirmation, then it MUST be confirmed 
        # for the write to proceed
        if permissiveConfirmation:
            log.trace("   confirming permissive...")
            system.tag.write(self.path + "/writeStatus", "Confirming Permissive")
            from ils.io.util import confirmWrite
            confirmed, errorMessage = confirmWrite(self.path + "/permissive", permissiveValue)
 
            if confirmed:
                log.trace("   confirmed Permissive write: %s - %s" % (self.path, permissiveValue))
            else:
                errorMessage = "Failed to confirm permissive write of <%s> to %s because %s" % (str(permissiveValue), self.path, errorMessage)
                log.error(errorMessage)
                system.tag.write(self.path + "/writeStatus", "Failure")
                system.tag.write(self.path + "/writeErrorMessage", errorMessage)
                return confirmed, errorMessage
            
        # If we got this far, then the permissive was successfully written (or we don't care about confirming it, so
        # write the value to the OPC tag.  WriteDatum ALWAYS does a write confirmation.  The gateway is going to confirm 
        # the write so this needs to just wait around for the answer

        log.trace("Writing %s to %s" % (str(val), tagRoot))
        system.tag.write(self.path + "/writeStatus", "Writing %s to %s" % (str(val), tagRoot))       
        confirmed, errorMessage = targetTag.writeDatum(val, valueType)
         
        # Return the permissive to its original value.  Don't let the success or failure of this override the result of the 
        # overall write.
        # TODO wait for a latency time
        log.trace("Restoring permissive")
        system.tag.write(self.path + "/permissive", permissiveAsFound)
        if permissiveConfirmation:
            confirmed, confirmMessage = confirmWrite(self.path + "/permissive", permissiveAsFound)
            
            if confirmed:    
                log.trace("Confirmed Permissive restore: %s" % (self.path))
            else:
                txt = "Failed to confirm permissive write of <%s> to %s because %s" % (str(val), self.path, confirmMessage)
                log.error(txt)
                system.tag.write(self.path + "/writeStatus", "Failure")
                system.tag.write(self.path + "/writeErrorMessage", txt)
        
        return confirmed, errorMessage

    # Perform a really basic check of the configuration of a tag
    def checkConfig(self, tagRoot):
        log.trace("In pkscontroller.checkConfig, checking %s" % (tagRoot))
        
        from ils.io.util import checkConfig
        configOK, errorMsg = checkConfig(self.path)
        if not(configOK):
            return configOK, errorMsg
        
        itemPath = system.tag.getAttribute(tagRoot, "OPCItemPath")

        if itemPath == "":
            return False, "%s OPCItemPath is not configured" % (tagRoot)
        
        server = system.tag.getAttribute(tagRoot, "OPCServer")
        if server == "":
            return False, "%s OPCServer is not configured" % (tagRoot)
        
        return True, ""
    
    # Check if a controller is in the appropriate mode for writing to.  This does not attempt to change the 
    # mode of the controller.  Return True if the controller is in the correct mode for writing.
    # This is equivalent to s88-confirm-controller-mode in the old system. 
    def confirmControllerMode(self, newVal, testForZero, checkPathToValve, outputType):
        success = True
        errorMessage = ""
        
        log.trace("In %s checking the configuration of PKS controller %s for writing %s to %s" % (__name__, self.path, str(newVal), outputType))
        
        # Determine which tag in the controller we are seeking to write to
        if string.upper(outputType) in ["SP", "SETPOINT"]:
            tagRoot = self.path + '/sp'
        elif string.upper(outputType) in ["OP", "OUTPUT"]:
            tagRoot = self.path + '/op'
        else:
            raise Exception("Unexpected value Type: <%s> for a PKS controller %s" % (outputType, self.path))

        # Read the current values of all of the tags we need to consider to determine if the configuration is valid.
        currentValue = system.tag.read(tagRoot + '/value')

        # Check the quality of the tags to make sure we can trust their values
        if str(currentValue.quality) != 'Good': 
            log.warn("checkConfig failed for %s because the %s quality is %s" % (self.path, outputType, str(currentValue.quality)))
            return False, "The %s quality is %s" % (outputType, str(currentValue.quality))

        # The quality is good so not get the values in a convenient form
        currentValue = float(currentValue.value)

        # Check the Mode
        mode = system.tag.read(self.path + '/mode/value')
        
        if str(mode.quality) != 'Good': 
            log.warn("checkConfig failed for %s because the mode quality is %s" % (self.path, str(mode.quality)))
            return False, "The mode quality is %s" % (str(mode.quality))
        
        mode = string.strip(mode.value)
        
        # Check the Windup
        windup = system.tag.read(self.path + '/windup')
        
        # Check the quality of the tags to make sure we can trust their values
        if str(windup.quality) != 'Good': 
            log.warn("checkConfig failed for %s because the windup quality is %s" % (self.path, str(windup.quality)))
            return False, "The windup quality is %s" % (str(windup.quality))

        windup = string.strip(windup.value)        

        log.trace("%s: %s=%s, windup=%s, mode:%s" % (self.path, outputType, str(currentValue), windup, mode))

        # For outputs check that the mode is MANUAL - no other test is required
        if string.upper(outputType) in ["OP", "OUTPUT"]:
            if string.upper(mode) != 'MAN':
                success = False
                errorMessage = "%s is not in MAN (mode is actually %s)" % (self.path, mode)
        
        # For setpoints, check that there is a path to the valve, mode = auto and sp = 0.  The path to valve check is optional 
        elif string.upper(outputType) in ["SP", "SETPOINT"]:
            if string.upper(windup) == 'HILO' and checkPathToValve:
                success = False
                errorMessage = "%s has no path to valve" % (self.path)
        
            if string.upper(mode) != 'AUTO':
                success = False
                errorMessage = "%s %s is not in AUTO (mode is actually %s)" % (errorMessage, self.path, mode)
            
            # The testForZero check is used when we expect the starting point for the write to be 0, i.e. a closed valve.
            # If we expect the current SP to be 0, and it isn't, then the state of the plant is not what we expect so
            # warn the operator.  See s88-confirm-controller-mode(opc-pks-controller)
            if (currentValue > (float(newVal) * 0.03)) and testForZero:
                success = False
                errorMessage = "%s %s setpoint is not zero (it is actually %f)" % (errorMessage, self.path, currentValue)

        log.trace("  confirmControllerMode returned: %s - %s" % (str(success), errorMessage))
        return success, errorMessage

    # Implement a simple write confirmation.  We know the value that we tried to write, read the tag for a
    # reasonable amount of time.  As soon as we read the value back we are done.  Figuring out the
    # amount of time to wait is the tricky part.  
    def confirmWrite(self, val, valueType):  
        log.trace("Confirming the write of <%s> to the %s of %s..." % (str(val), valueType, self.path))
 
        from ils.io.util import confirmWrite
        confirmation, errorMessage = confirmWrite(self.path + "/" + valueType + "/value", val)
        return confirmation, errorMessage

    # This method makes sequential writes to ramp either the SP or OP of an Experion controller.  
    # There is no native output ramping capability in EPKS and this method fills the gap.  
    # In addition, it will ramp the SP of a controller that isn't built in G2 as having native EPKS SP Ramp capability.  
    # In both cases, the ramp is executed by writing sequentially based on a linear ramp.  
    # It assumes that the ramp time is in minutes.. 
    # *** This is called by a tag change script and runs in the gateway ***
    def writeRamp(self, val, valType, rampTime, updateFrequency, writeConfirm):       
        success = True
        log.trace("Writing ramp for controller %s" % (self.path))

        if val == None or rampTime == None or writeConfirm == None or valType == None or updateFrequency == None:
            log.error("ERROR writing ramp for PKS controller: %s - One or more of the required arguments is missing" % (self.path))
            return False, "One or more of the required arguments is missing"
        
        # Change  the mode of the controller and set the desired ramp type
        if string.upper(valType) in ["SP", "SETPOINT", "RAMP-SETPOINT", "SETPOINT-RAMP"]:
            modeValue = 'AUTO'
            valuePathRoot = self.path + '/sp'
            targetTag = self.spTag

        elif string.upper(valType) in ["OP", "OUTPUT", "RAMP-OUTPUT", "OUTPUT-RAMP"]:
            modeValue = 'MAN'
            valuePathRoot = self.path + '/op'
            targetTag = self.opTag

        else:
            log.error("ERROR writing ramp for PKS controller: %s - Unexpected value type <%s>" % (self.path, valType))
            return False, "Unexpected value type <%s>" % (valType)
        
        # Check the basic configuration of the tag we are trying to write to.
        success, errorMessage = self.checkConfig(valuePathRoot + "/value")
        if not(success):
            system.tag.write(self.path + "/writeStatus", "Failure")
            system.tag.write(self.path + "/writeErrorMessage", errorMessage)
            log.info("Aborting write to %s, checkConfig failed due to: %s" % (valuePathRoot, errorMessage))
            return False, errorMessage

        
        # Put the controller into the appropriate mode
        modeTag = self.modeTag
        confirmed, errorMessage = modeTag.writeDatum(modeValue, 'mode')
        if not(confirmed):
            log.warn("Warning: EPKS Controller <%s> - the controller mode <%s> could not be confirmed, attempting to write the ramp anyway!" % (self.path, modeValue))

        # Read the starting point for the ramp which is the current value
        startValue = system.tag.read(valuePathRoot + '/value')
        if str(startValue.quality) != 'Good':
            errorMessage = "ERROR: EPKS Controller <%s> - ramp aborted due to inability to read the initial <%s> setpoint!" % (self.path, valType)
            log.error(errorMessage)
            return False, errorMessage

        startValue = startValue.value

        log.info("Ramping the %s of EPKS controller <%s> from %s to %s over %s minutes" % (valType, self.path, str(startValue), str(val), str(rampTime)))
        system.tag.write(self.path + "/writeStatus", "Ramping the %s from %s to %s over %s minutes" % (valType, str(startValue), str(val), str(rampTime)))

        rampTimeSeconds = rampTime * 60.0

        from ils.common.util import equationOfLine
        m, b = equationOfLine(0.0, startValue, rampTimeSeconds, val)
        startTime = system.date.now()
        deltaSeconds = system.date.secondsBetween(startTime, system.date.now())
        
        while (deltaSeconds < rampTimeSeconds):
            from ils.common.util import calculateYFromEquationOfLine
            aVal = calculateYFromEquationOfLine(deltaSeconds, m, b)
            
            log.trace("EPKS Controller <%s> ramping to %s (elapsed time: %s)" % (self.path, str(aVal), str(deltaSeconds)))
            targetTag.writeWithNoCheck(aVal)
 
            # Time in seconds
            time.sleep(updateFrequency)
            deltaSeconds = system.date.secondsBetween(startTime, system.date.now())
        
        # Write the final point and confirm this one
        targetTag.writeDatum(val, valType)

        log.info("EPKS Controller <%s> done ramping!" % (self.path))
        return success, errorMessage
