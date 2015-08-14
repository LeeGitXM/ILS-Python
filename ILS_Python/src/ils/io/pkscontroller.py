'''
Created on Dec 1, 2014

@author: Pete
'''

import system, string, time
import ils.common.util as util
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
        print "resetting a PKS controller"
        log.trace('Resetting a PKSController...')       
        
        system.tag.write(self.path + '/command', '')
        system.tag.write(self.path + '/payload', '')

        system.tag.write(self.path + '/mode/command', 'reset')
        system.tag.write(self.path + '/op/command', 'reset')
        system.tag.write(self.path + '/sp/command', 'reset')
        # Not sure if outputDisposability needs to be reset
        return success, errorMessage

    # Check if a controller is in the appropriate mode for writing to.  This does not attempt to change the 
    # mode of the controller.
    # This is equivalent to s88-confirm-controller-mode in the old system. 
    def checkConfig(self, newVal, testForZero, checkPathToValue, valType):
        success = True
        errorMessage = ""
        
        log.trace("Checking the configuration of PKS controller %s for writing %s to %s" % (self.path, str(newVal), valType))
        
        # Determine which tag in the controller we are seeking to write to
        if string.upper(valType) in ["SP", "SETPOINT"]:
            tagRoot = self.path + '/sp'
        elif string.upper(valType) in ["OP", "OUTPUT"]:
            tagRoot = self.path + '/op'
        else:
            log.error("Unexpected valType: <%s>" % (valType))
            return False, "Unexpected value type: <%s>" % (valType)

        # Read the current values of all of the tags we need to consider to determine if the configuration is valid.
        currentValue = system.tag.read(tagRoot + '/value')
        outputDisposability = system.tag.read(self.path + '/outputDisposability/value')
        mode = system.tag.read(self.path + '/mode/value')
        
        # Check the quality of the tags to make sure we can trust their values
        if str(currentValue.quality) != 'Good': 
            log.info("checkConfig failed for %s because the %s quality is %s" % (self.path, valType, str(currentValue.quality)))
            return False, "The %s quality is %s" % (valType, str(currentValue.quality))

        if str(outputDisposability.quality) != 'Good': 
            log.info("checkConfig failed for %s because the outputDisposability quality is %s" % (self.path, str(outputDisposability.quality)))
            return False, "The output disposability quality is %s" % (str(outputDisposability.quality))
        
        if str(mode.quality) != 'Good': 
            log.info("checkConfig failed for %s because the mode quality is %s" % (self.path, str(mode.quality)))
            return False, "The mode quality is %s" % (str(mode.quality))
        
        # The quality is good so not get the values in a mode convenient form
        currentValue = float(currentValue.value)
        outputDisposability = string.strip(outputDisposability.value)
        mode = string.strip(mode.value)
        
        log.trace("%s: %s=%s, outputDisposability=%s, mode:%s" % (self.path, valType, str(currentValue), outputDisposability, mode))
        
        # For outputs check that the mode is MANUAL - no other test is required
        if string.upper(valType) in ["OP", "OUTPUT"]:
            if string.upper(mode) != 'MAN':
                return False, "%s is not in manual (mode is actually %s)" % (self.path, mode)
        
        # For setpoints, check that there is a path to the valve, mode = auto and sp = 0.  The path to valve check is 
        # optional 
        elif string.upper(valType) in ["SP", "SETPOINT"]:
            if string.upper(outputDisposability) != 'HILO' and checkPathToValue:
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

        return success, errorMessage

    # Implement a simple write confirmation.  We know the value that we tried to write, read the tag for a
    # reasonable amount of time.  As soon as we read the value back we are done.  Figuring out the
    # amount of time to wait is the tricky part.  
    def confirmWrite(self, val, valType):  
        log.trace("Confirming the write of <%s> to the %s of %s..." % (str(val), valType, self.path))
 
        from ils.io.util import confirmWrite
        confirmation, errorMessage = confirmWrite(self.path + "/" + valType + "/value", val)
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
            log.warning("Warning: EPKS Controller <%s> - the controller mode <%s> could not be confirmed, attempting to write the ramp anyway!" % (self.path, modeValue))

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

