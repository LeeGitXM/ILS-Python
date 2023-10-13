'''
Created on Mar 29, 2018

@author: phass
'''

import system, string, time
from ils.io.util import writeTag
import ils.io.pkscontroller as pkscontroller
import ils.io.opcoutput as opcoutput
from ils.io.util import confirmWrite
from ils.log import getLogger
log = getLogger(__name__)

class PKSRampController(pkscontroller.PKSController):
    
    def __init__(self,path):
        pkscontroller.PKSController.__init__(self,path)

    # Reset the UDT in preparation for a write 
    def reset(self):
        status, errorMessage = pkscontroller.PKSController.reset(self) 
        return status, errorMessage

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
    A ramp controller can only ramp the SP in hardware, if the request is to ramp an OP then the ramp will be implemented in Ignition.
    '''
    def writeRamp(self, val, valType, rampTime, updateFrequency, writeConfirm):       
        success = True

        if val == None or rampTime == None or writeConfirm == None or valType == None or updateFrequency == None:
            log.errorf("ERROR writing ramp for PKS Ramp controller: %s - One or more of the required arguments is missing val=%s rampTime=%s writeConfirm=%s valType=%s updateFreq=%s" % (self.path,val,rampTime,writeConfirm,valType,updateFrequency))
            return False, "One or more of the required arguments is missing"
        
        if string.upper(valType) in ["OUTPUT RAMP"]:
            status, errorMessage = pkscontroller.PKSController.writeRamp(self, val, valType, rampTime, updateFrequency, writeConfirm)
            return status, errorMessage

        pkscontroller.PKSController.setPermissive(self)
       
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
            writeTag(self.path + "/writeStatus", "Failure")
            writeTag(self.path + "/writeErrorMessage", errorMessage)
            log.infof("Aborting write to %s, checkConfig failed due to: %s", valuePathRoot, errorMessage)
            return False, errorMessage
        
        # Put the controller into the appropriate mode
        modeTag = self.modeTag
        confirmed, errorMessage = modeTag.writeDatum(modeValue, 'mode')
        if not(confirmed):
            log.warnf("Warning: EPKS Controller <%s> - the controller mode <%s> could not be confirmed, attempting to write the ramp anyway!", self.path, modeValue)

        log.infof("Ramping the %s of EPKS controller <%s> to %s over %s minutes", valType, self.path, str(val), str(rampTime))
        writeTag(self.path + "/writeStatus", "Ramping the %s to %s over %s minutes" % (valType, str(val), str(rampTime)))

#        rampTimeSeconds = rampTime * 60.0
        '''
        log.trace("...writing PRESET to the rampstate...")
        writeTag(self.path + "/sp/rampState", "PRESET")            
        time.sleep(self.OPC_LATENCY_TIME)

        log.tracef("...writing %f to the targetValue and %f to the ramptime...", val, rampTime)
        writeTag(self.path + "/sp/rampTime", rampTime)
        writeTag(self.path + "/sp/targetValue", val)
        time.sleep(self.OPC_LATENCY_TIME)
        
        log.trace("...writing RUN to the rampstate...")
        writeTag(self.path + "/sp/rampState", "RUN")
        time.sleep(self.OPC_LATENCY_TIME)
        '''
        
        ''' 
        This is the new version that confirms each of the individual writes.
        If we confirm each individual write then we don't need the inexact fixed delays.
        The confirm will try for a minute to confirm the write.
        PH 12/8/2021
        '''
        log.trace("...writing PRESET to the rampstate...")
        writeTag(self.path + "/sp/rampState", "PRESET")
        confirmed, errorMessage = confirmWrite(self.path + "/sp/rampState", "PRESET")   

        ''' I want to write these simultaneously, rather than write one, wait as it is confirmed, and then write the other and wait to confirm it '''
        if confirmed:
            log.tracef("...writing %f to the targetValue and %s to the ramptime...", val, str(rampTime))
            writeTag(self.path + "/sp/rampTime", rampTime)
            writeTag(self.path + "/sp/targetValue", val)
            confirmed, errorMessage = confirmWrite(self.path + "/sp/rampTime", rampTime)
            if confirmed:
                confirmed, errorMessage = confirmWrite(self.path + "/sp/targetValue", val)
        
        if confirmed:
            log.trace("...writing RUN to the rampstate...")
            writeTag(self.path + "/sp/rampState", "RUN")
            confirmed, errorMessage = confirmWrite(self.path + "/sp/rampState", "RUN")
        
        pkscontroller.PKSController.restorePermissive(self)

        log.infof("EPKS Controller <%s> done ramping!", self.path)
        return confirmed, errorMessage
    