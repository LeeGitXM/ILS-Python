'''
Created on Mar 29, 2018

@author: phass
'''


import system, string, time
import ils.io.pkscontroller as pkscontroller
import ils.io.opcoutput as opcoutput
log = system.util.getLogger("com.ils.io")

class PKSRampController(pkscontroller.PKSController):
    
    def __init__(self,path):
        pkscontroller.PKSController.__init__(self,path)

    # Reset the UDT in preparation for a write 
    def reset(self):
        success = True
        errorMessage = ""
        log.trace('Resetting a PKSRampController...')       
        
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

    '''
    Inherit the writeDatum method from a pks controller
    '''

    '''
    Inherit the checkConfig method from a pks controller
    '''

    '''
    Inherit the confirmControllerMode method from a pks controller
    '''

    
    '''
    A ramp controller implements the ramp in the DCS.  All we have to do is write the target value and the ramp time and the DCS does the rest.
    We also have to do all of the other handshaking, but we don't need to ramp from the current value to the new value one step at a time.
    '''
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
    
    # WiteWithNoCheck for a controller supports writing values to the OP, SP, or MODE, one at a time.
    def writeWithNoCheck(self, val, valueType):      
        log.trace("pkscontroller.writeWithNoCheck() %s - %s - %s" % (self.path, str(val), valueType))
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
        # for the write to proceed.  This has nothing to do with confirming the write.
        if permissiveConfirmation:
            log.trace("   confirming permissive...")
            system.tag.write(self.path + "/writeStatus", "Confirming Permissive")
            from ils.io.util import confirmWrite
            confirmed, errorMessage = confirmWrite(self.path + "/permissive", permissiveValue, self.CONFIRM_TIMEOUT)
 
            if confirmed:
                log.trace("   confirmed Permissive write: %s - %s" % (self.path, permissiveValue))
            else:
                errorMessage = "Failed to confirm permissive write of <%s> to %s because %s" % (str(permissiveValue), self.path, errorMessage)
                log.error(errorMessage)
                system.tag.write(self.path + "/writeStatus", "Failure")
                system.tag.write(self.path + "/writeErrorMessage", errorMessage)
                return confirmed, errorMessage
        else:
            log.trace("...dwelling in lieu of permissive confirmation...")
            time.sleep(self.PERMISSIVE_LATENCY_TIME)
            
        # If we got this far, then the permissive was successfully written (or we don't care about confirming it, so
        # write the value to the OPC tag.  WriteDatum ALWAYS does a write confirmation.  The gateway is going to confirm 
        # the write so this needs to just wait around for the answer

        log.trace("Writing %s to %s" % (str(val), tagRoot))
        system.tag.write(self.path + "/writeStatus", "Writing %s to %s" % (str(val), tagRoot))       
        confirmed, errorMessage = targetTag.writeWithNoCheck(val, valueType)
        if not(confirmed):
            log.error(errorMessage)
            system.tag.write(self.path + "/writeStatus", "Failure")
            system.tag.write(self.path + "/writeErrorMessage", errorMessage)
            return confirmed, errorMessage
         
        # Return the permissive to its original value.  Don't let the success or failure of this override the result of the 
        # overall write.
        
        # Since we didn't confirm the write above, we need to wait for a latency time to give the value a chance to 
        log.trace("...dwelling after the value write and before the permissive restore...")
        time.sleep(self.PERMISSIVE_LATENCY_TIME)

        log.trace("Restoring permissive")
        system.tag.write(self.path + "/permissive", permissiveAsFound)
        if permissiveConfirmation:
            confirmed, confirmMessage = confirmWrite(self.path + "/permissive", permissiveAsFound, self.CONFIRM_TIMEOUT)
            
            if confirmed:    
                log.trace("Confirmed Permissive restore: %s" % (self.path))
            else:
                txt = "Failed to confirm permissive write of <%s> to %s because %s" % (str(val), self.path, confirmMessage)
                log.error(txt)
                system.tag.write(self.path + "/writeStatus", "Failure")
                system.tag.write(self.path + "/writeErrorMessage", txt)
        
        return confirmed, errorMessage
