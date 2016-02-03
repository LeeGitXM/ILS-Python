'''
Created on Dec 1, 2014

@author: Pete
'''

import system, string, time
import ils.io.controller as controller
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
from java.util import Date
log = LogUtil.getLogger("com.ils.io")

class PKSController(controller.Controller):
    def __init__(self,path):
        controller.Controller.__init__(self,path)

    # Reset the UDT in preparation for a write 
    def reset(self):
        success = True
        errorMessage = ""
        log.trace('Resetting a PKSController...')       
        
        system.tag.write(self.path + '/command', '')
        system.tag.write(self.path + '/payload', '')
        system.tag.write(self.path + '/writeErrorMessage', '')
        system.tag.write(self.path + '/writeStatus', '')

        system.tag.write(self.path + '/mode/command', 'reset')
        system.tag.write(self.path + '/op/command', 'reset')
        system.tag.write(self.path + '/sp/command', 'reset')
        # Not sure if outputDisposability needs to be reset
        return success, errorMessage

    
    def writeDatum(self):
        # Get the value and type to be written - this must be there BEFORE the controller is reset       
        payload = system.tag.read(self.path + "/payload").value
        if payload == None or payload == "":
            payload = {}
            return False, "Missing payload: <%s>" % (self.path)
        
        # This is handy little way to turn a text string that looks like a dictionary into an actual dictionary
        import ast
        payload=ast.literal_eval(payload)

        val=payload.get("val","NaN")
        valueType=payload.get("valueType")
        
        log.trace("pkscontroller.writeDatum() %s - %s - %s" % (self.path, str(val), valueType))
        if string.upper(valueType) in ["SP", "SETPOINT"]:
            tagRoot = self.path + '/sp'
        elif string.upper(valueType) in ["OP", "OUTPUT"]:
            tagRoot = self.path + '/op'
        elif string.upper(valueType) in ["MODE"]:
            tagRoot = self.path + '/mode'
        else:
            log.error("Unexpected value Type: <%s>" % (valueType))
            return False, "Unexpected value Type: <%s>" % (valueType)

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
        system.tag.write(tagRoot + '/command', 'RESET')
        # Time in seconds
        time.sleep(1)
        
        #----------------------
        # Set the permissive
        #----------------------
        
        log.trace("Writing permissive...")
        
        # Update the status to "Writing"
        system.tag.write(self.path + "/writeStatus", "Writing Permissive")
 
        # Read the current permissive and save it so that we can put it back the way is was when we are done
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
            log.trace("Confirming permissive...")
            system.tag.write(self.path + "/writeStatus", "Confirming Permissive")
            from ils.io.util import confirmWrite
            confirmed, errorMessage = confirmWrite(self.path + "/permissive", permissiveValue)
 
            if confirmed:
                log.trace("Confirmed Permissive write: %s - %s" % (self.path, permissiveValue))
            else:
                errorMessage = "Failed to confirm permissive write of <%s> to %s because %s" % (str(permissiveValue), self.path, errorMessage)
                log.error(errorMessage)
                system.tag.write(self.path + "/writeStatus", "Failure")
                system.tag.write(self.path + "/writeErrorMessage", errorMessage)
                return confirmed, errorMessage
            
        # If we got this far, then the permissive was successfully written (or we don't care about confirming it, so
        # write the value to the OPC tag

        log.trace("Writing %s to %s" % (str(val), tagRoot))
        system.tag.write(self.path + "/writeStatus", "Writing %s to %s" % (str(val), tagRoot))
        system.tag.write(tagRoot + '/writeValue', val)
        system.tag.write(tagRoot + '/command', 'WRITEDATUM')
        
        # writeDatum ALWAYS does a write confirmation.  The gateway is going to confirm the write so this needs 
        # to just wait around for the answer

        log.trace("...waiting for write confirm...")
        from ils.io.util import waitForWriteConfirm
        confirmed, errorMessage = waitForWriteConfirm(tagRoot)
        txt="Write of %s to %s - Confirmed: %s - %s" % (str(val), tagRoot, str(confirmed), errorMessage)
        log.trace(txt)
        if confirmed:
            system.tag.write(self.path + "/writeStatus", "Success")
            system.tag.write(self.path + "/writeErrorMessage", txt)
        else:
            system.tag.write(self.path + "/writeStatus", "Failure")
            system.tag.write(self.path + "/writeErrorMessage", txt)
        status=confirmed
        
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
        
        return status, errorMessage

    # Perform a really basic check of the configuration of a tag
    def checkConfig(self, tagRoot):
        log.trace("In pkscontroller.checkConfig, checking %s" % (tagRoot))
        
        itemPath = system.tag.getAttribute(tagRoot, "OPCItemPath")

        if itemPath == "":
            return False, "%s OPCItemPath is not configured" % (tagRoot)
        
        server = system.tag.getAttribute(tagRoot, "OPCServer")
        if server == "":
            return False, "%s OPCServer is not configured" % (tagRoot)
        
        return True, ""
    
    # Check if a controller is in the appropriate mode for writing to.  This does not attempt to change the 
    # mode of the controller.
    # This is equivalent to s88-confirm-controller-mode in the old system. 
    def confirmControllerMode(self, newVal, testForZero, checkPathToValve, valueType):
        success = True
        errorMessage = ""
        
        log.trace("Checking the configuration of PKS controller %s for writing %s to %s" % (self.path, str(newVal), valueType))
        
        # Determine which tag in the controller we are seeking to write to
        if string.upper(valueType) in ["SP", "SETPOINT"]:
            tagRoot = self.path + '/sp'
        elif string.upper(valueType) in ["OP", "OUTPUT"]:
            tagRoot = self.path + '/op'
        else:
            log.error("Unexpected valType: <%s>" % (valueType))
            return False, "Unexpected value type: <%s>" % (valueType)

        # Read the current values of all of the tags we need to consider to determine if the configuration is valid.
        currentValue = system.tag.read(tagRoot + '/value')
        
        # TODO Does OutputDisposability belong here?
#        outputDisposability = system.tag.read(self.path + '/outputDisposability/value')
        mode = system.tag.read(self.path + '/mode/value')
        
        # Check the quality of the tags to make sure we can trust their values
        if str(currentValue.quality) != 'Good': 
            log.info("checkConfig failed for %s because the %s quality is %s" % (self.path, valueType, str(currentValue.quality)))
            return False, "The %s quality is %s" % (valueType, str(currentValue.quality))

#        if str(outputDisposability.quality) != 'Good': 
#            log.info("checkConfig failed for %s because the outputDisposability quality is %s" % (self.path, str(outputDisposability.quality)))
#            return False, "The output disposability quality is %s" % (str(outputDisposability.quality))
        
        if str(mode.quality) != 'Good': 
            log.info("checkConfig failed for %s because the mode quality is %s" % (self.path, str(mode.quality)))
            return False, "The mode quality is %s" % (str(mode.quality))
        
        # The quality is good so not get the values in a mode convenient form
        currentValue = float(currentValue.value)
#        outputDisposability = string.strip(outputDisposability.value)
        outputDisposability="HILO"
        mode = string.strip(mode.value)
        
        log.trace("%s: %s=%s, outputDisposability=%s, mode:%s" % (self.path, valueType, str(currentValue), outputDisposability, mode))

        # For outputs check that the mode is MANUAL - no other test is required
        if string.upper(valueType) in ["OP", "OUTPUT"]:
            if string.upper(mode) != 'MAN':
                success = False
                errorMessage = "%s is not in manual (mode is actually %s)" % (self.path, mode)
        
        # For setpoints, check that there is a path to the valve, mode = auto and sp = 0.  The path to valve check is 
        # optional 
        elif string.upper(valueType) in ["SP", "SETPOINT"]:
            if string.upper(outputDisposability) != 'HILO' and checkPathToValve:
                success = False
                errorMessage = "%s has no path to valve" % (self.path)
        
            if string.upper(mode) != 'AUTO':
                success = False
                errorMessage = "%s %s is not in automatic (mode is actually %s)" % (errorMessage, self.path, mode)
            
            # I don't understand this check, not sure if we are checking the current value or the new value.  
            # If checking the currentValue, what difference does it make what the new value is??
            if (currentValue > float(newVal) * 0.03) and testForZero:
                success = False
                errorMessage = "%s %s setpoint is not zero (it is actually %f)" % (errorMessage, self.path, currentValue)

        log.trace("checkConfiguration conclusion: %s - %s" % (str(success), errorMessage))
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
    def writeRamp(self):       
        success = True
        log.trace("Writing ramp for controller %s" % (self.path))
        payload = system.tag.read(self.path + '/payload').value
        payload = eval(str(payload))
        
        val = payload.get("val", None)
        rampTime = payload.get("rampTime", None)
        writeConfirm = payload.get("writeConfirm", None)
        valType = payload.get("valType", None)
        updateFrequency = payload.get("updateFrequency", None)
    
        if val == None or rampTime == None or writeConfirm == None or valType == None or updateFrequency == None:
            log.error("ERROR writing ramp for PKS controller: %s - One or more of the required arguments is missing" % (self.path))
            return False, "One or more of the required arguments is missing"
        
        # Change  the mode of the controller and set the desired ramp type
        if string.upper(valType) in ["SP", "SETPOINT", "RAMP-SETPOINT", "SETPOINT-RAMP"]:
            modeValue = 'AUTO'
            valuePathRoot = self.path + '/sp'

        elif string.upper(valType) in ["OP", "OUTPUT", "RAMP-OUTPUT", "OUTPUT-RAMP"]:
            modeValue = 'MAN'
            valuePathRoot = self.path + '/op'

        else:
            log.error("ERROR writing ramp for PKS controller: %s - Unexpected value type <%s>" % (self.path, valType))
            return False, "Unexpected value type <%s>" % (valType)
        
        # Put the controller into the appropriate mode
        system.tag.write(self.path + '/mode/writeValue', modeValue)
        system.tag.write(self.path + '/mode/command', 'WRITEDATUM')
        
        confirmed, errorMessage = self.confirmWrite(modeValue, 'mode')
        if not(confirmed):
            log.warn("Warning: EPKS Controller <%s> - the controller mode <%s> could not be confirmed, attempting to write the ramp anyway!" % (self.path, modeValue))

        # Read the starting point for the ramp
        startValue = system.tag.read(valuePathRoot + '/value')
        if str(startValue.quality) != 'Good':
            errorMessage = "ERROR: EPKS Controller <%s> - ramp aborted due to inability to read the initial <%s> setpoint!" % (self.path, valType)
            log.error(errorMessage)
            return False, errorMessage

        startValue = startValue.value

        log.info("Ramping the %s of EPKS controller <%s> from %s to %s over %s minutes" % (valType, self.path, str(startValue), str(val), str(rampTime)))

        from ils.common.util import equationOfLine
        m, b = equationOfLine(0.0, startValue, rampTime, val)
        startTime = Date().getTime()
        delta = (Date().getTime() - startTime) / 1000
        while (delta < rampTime):
            from ils.common.util import calculateYFromEquationOfLine
            aVal = calculateYFromEquationOfLine(delta, m, b)
            
            log.trace("EPKS Controller <%s> ramping to %s (elapsed time: %s)" % (self.path, str(aVal), str(delta)))

            system.tag.write(valuePathRoot + '/command', '')
            system.tag.write(valuePathRoot + '/writeValue', aVal)
            system.tag.write(valuePathRoot + '/command', 'WRITEDATUM')
 
            # Time in seconds
            time.sleep(updateFrequency)
            delta = (Date().getTime() - startTime) / 1000
        
        # Write the final point
        system.tag.write(valuePathRoot + '/command', '')
        system.tag.write(valuePathRoot + '/writeValue', val)
        system.tag.write(valuePathRoot + '/command', 'WRITEDATUM')

        log.info("EPKS Controller <%s> done ramping!" % (self.path))
        return success, errorMessage

