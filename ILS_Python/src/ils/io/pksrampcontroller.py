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

        if val == None or rampTime == None or writeConfirm == None or valType == None or updateFrequency == None:
            log.errorf("ERROR writing ramp for PKS controller: %s - One or more of the required arguments is missing", self.path)
            return False, "One or more of the required arguments is missing"
        
        '''
        A ramp controller can only ramp the SP in hardware, if the request is to ramp an OP then the ramp will be implemented in Ignition..
        '''
        if string.upper(valType) in ["OUTPUT RAMP"]:
            status, errorMessage = pkscontroller.PKSController.writeRamp(self, val, valType, rampTime, updateFrequency, writeConfirm)
            return status, errorMessage
            
        '''
        This method only handles setpoint ramps
        '''
        log.tracef("In %s.writeRamp() writing a setpoint ramp for controller %s", __name__, self.path)
        if string.upper(valType) not in ["SETPOINT RAMP"]:
            log.errorf("ERROR writing ramp for PKS controller: %s - Unexpected value type <%s>", self.path, valType)
            return False, "Unexpected value type <%s>" % (valType)
        
        # Change  the mode of the controller and set the desired ramp type
        modeValue = 'AUTO'
        valuePathRoot = self.path + '/sp'
        targetTag = self.spTag
        
        # Check the basic configuration of the tag we are trying to write to.
        success, errorMessage = self.checkConfig(valuePathRoot + "/value")
        if not(success):
            system.tag.write(self.path + "/writeStatus", "Failure")
            system.tag.write(self.path + "/writeErrorMessage", errorMessage)
            log.infof("Aborting write to %s, checkConfig failed due to: %s", valuePathRoot, errorMessage)
            return False, errorMessage

        
        # Put the controller into the appropriate mode
        modeTag = self.modeTag
        confirmed, errorMessage = modeTag.writeDatum(modeValue, 'mode')
        if not(confirmed):
            log.warnf("Warning: EPKS Controller <%s> - the controller mode <%s> could not be confirmed, attempting to write the ramp anyway!", self.path, modeValue)

        log.infof("Ramping the %s of EPKS controller <%s> to %s over %s minutes", valType, self.path, str(val), str(rampTime))
        system.tag.write(self.path + "/writeStatus", "Ramping the %s to %s over %s minutes" % (valType, str(val), str(rampTime)))

        rampTimeSeconds = rampTime * 60.0

        log.trace("...writing PRESET to the rampstate...")
        system.tag.write(self.path + "/sp/rampState", "PRESET")            
        time.sleep(self.OPC_LATENCY_TIME)

        log.tracef("...writing %f to the targetValue and %f to the ramptime...", val, rampTime)
        system.tag.write(self.path + "/sp/rampTime", rampTimeSeconds)
        system.tag.write(self.path + "/sp/targetValue", val)
        time.sleep(self.OPC_LATENCY_TIME)
        
        log.trace("...writing RUN to the rampstate...")
        system.tag.write(self.path + "/sp/rampState", "RUN")
        time.sleep(self.OPC_LATENCY_TIME)

        log.infof("EPKS Controller <%s> done ramping!", self.path)
        return success, errorMessage
    