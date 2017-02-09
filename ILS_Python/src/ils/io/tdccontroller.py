'''
Created on Dec 1, 2014

@author: Pete
'''

import ils.io.controller as controller
import system, string
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.io")

class TDCController(controller.Controller):
    def __init__(self,path):
        controller.Controller.__init__(self,path)

    # Reset the UDT in preparation for a write 
    def reset(self):
        log.trace('Resetting a TDCController...')

    # Check if a controller is in the appropriate mode for writing to.  This does not attempt to change the 
    # mode of the controller.  Return True if the controller is in the correct mode for writing.
    # This is equivalent to s88-confirm-controller-mode in the old system. 
    def confirmControllerMode(self, newVal, testForZero, checkPathToValve, outputType):
        success = True
        errorMessage = ""
        
        log.trace("In %s checking the configuration of PKS controller %s for writing %s to %s" % (__name__, self.path, str(newVal), outputType))
        
        #TODO Need to add support for a setpoint ramp here and at the end.
        
        # Determine which tag in the controller we are seeking to write to
        if string.upper(outputType) in ["SP", "SETPOINT"]:
            tagRoot = self.path + '/sp'
        elif string.upper(outputType) in ["OP", "OUTPUT"]:
            tagRoot = self.path + '/op'
        else:
            raise Exception("Unexpected value Type: <%s> for a TDC controller %s" % (outputType, self.path))

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
        
        # Check the Output Disposability
        
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
                errorMessage = "%s is not in manual (mode is actually %s)" % (self.path, mode)
        
        # For setpoints, check that there is a path to the valve, mode = auto and sp = 0.  The path to valve check is 
        # optional 
        elif string.upper(outputType) in ["SP", "SETPOINT"]:
            if string.upper(windup) == 'HILO' and checkPathToValve:
                success = False
                errorMessage = "%s has no path to valve" % (self.path)
        
            if string.upper(mode) <> 'AUTO':
                success = False
                errorMessage = "%s %s is not in automatic (mode is actually %s)" % (errorMessage, self.path, mode)
            
            # I don't understand this check, not sure if we are checking the current value or the new value.  
            # If checking the currentValue, what difference does it make what the new value is??
            # See s88-confirm-controller-mode(opc-pks-controller)
            if (currentValue > (float(newVal) * 0.03)) and testForZero:
                success = False
                errorMessage = "%s %s setpoint is not zero (it is actually %f)" % (errorMessage, self.path, currentValue)

        # An 
        else:
            print "Foo"
        log.trace("checkConfiguration conclusion: %s - %s" % (str(success), errorMessage))
        return success, errorMessage
