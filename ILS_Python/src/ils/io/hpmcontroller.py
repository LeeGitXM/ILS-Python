'''
Created on Jan 7, 2021

@author: CPM
'''

import ils.io.controller as controller
import system, string, time
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
import ils.io.opcoutput as opcoutput
from ils.io.util import confirmWrite

log = LogUtil.getLogger("com.ils.io")

class HPMController(controller.Controller):
    opTag = None
    spTag = None
    permissiveAsFound = ""
    permissiveConfirmation = True
    permissiveValue = ""
    CONFIRM_TIMEOUT = 10.0
    PERMISSIVE_LATENCY_TIME = 0.0
    OPC_LATENCY_TIME = 0.0
    
    def __init__(self,path):
        log.tracef("In %s.__int__()", __name__)
        controller.Controller.__init__(self,path)
        
        self.spTag = opcoutput.OPCOutput(path + '/sp')
        self.opTag = opcoutput.OPCOutput(path + '/op')
        log.tracef("OP Tag path: %s", self.opTag.path)
        self.PERMISSIVE_LATENCY_TIME = system.tag.read("[XOM]Configuration/Common/opcPermissiveLatencySeconds").value
        self.OPC_LATENCY_TIME = system.tag.read("[XOM]Configuration/Common/opcTagLatencySeconds").value
        
    def reset(self):
        ''' Reset the UDT in preparation for a write '''
        status = True
        errorMessage = ""
        log.tracef('Resetting a %s Controller...', __name__)       
        
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

        return status, errorMessage

    def setPermissive(self):
        log.trace("Writing permissive...")
        
        ''' Update the status to "Writing" '''
        system.tag.write(self.path + "/writeStatus", "Writing Permissive")
 
        ''' Read the current permissive and save it so that we can put it back the way is was when we are done '''
        self.permissiveAsFound = system.tag.read(self.path + "/permissive").value
        log.tracef("   permissive as found: %s", self.permissiveAsFound)
        
        ''' Get from the configuration of the UDT the value to write to the permissive and whether or not it needs to be confirmed '''
        self.permissiveValue = 'PROGRAM'
        self.permissiveConfirmation = system.tag.read(self.path + "/permissiveConfirmation").value
        
        ''' Write the permissive value to the permissive tag and wait until it gets there '''
        log.tracef("   writing permissive value: %s", self.permissiveValue)
        system.tag.write(self.path + "/permissive", self.permissiveValue)
        
        ''' Confirm the permissive if necessary.  If the UDT is configured for confirmation, then it MUST be confirmed for the write to proceed '''
        if self.permissiveConfirmation:
            log.trace("   confirming permissive...")
            system.tag.write(self.path + "/writeStatus", "Confirming Permissive")
            
            confirmed, errorMessage = confirmWrite(self.path + "/permissive", self.permissiveValue, self.CONFIRM_TIMEOUT)
 
            if confirmed:
                log.tracef("   confirmed Permissive write: %s - %s", self.path, self.permissiveValue)
            else:
                errorMessage = "Failed to confirm permissive write of <%s> to %s because %s" % (str(self.permissiveValue), self.path, errorMessage)
                log.error(errorMessage)
                system.tag.write(self.path + "/writeStatus", "Failure")
                system.tag.write(self.path + "/writeErrorMessage", errorMessage)
                return confirmed, errorMessage
        else:
            log.trace("...dwelling in lieu of permissive confirmation...")
            time.sleep(self.PERMISSIVE_LATENCY_TIME)
            confirmed = True
            errorMessage = ""
            
        return confirmed, errorMessage
    
    def restorePermissive(self):
        time.sleep(self.PERMISSIVE_LATENCY_TIME)
        log.trace("Restoring permissive")
        system.tag.write(self.path + "/permissive", self.permissiveAsFound)
        if self.permissiveConfirmation:
            confirmed, confirmMessage = confirmWrite(self.path + "/permissive", self.permissiveAsFound, self.CONFIRM_TIMEOUT)
            if confirmed:    
                log.tracef("Confirmed Permissive restore: %s", self.path)
            else:
                txt = "Failed to confirm permissive write of <%s> to %s because %s" % (str(self.permissiveAsFound), self.path, confirmMessage)
                log.error(txt)
                system.tag.write(self.path + "/writeStatus", "Failure")
                system.tag.write(self.path + "/writeErrorMessage", txt)
                
    def writeDatum(self, val, valueType):
        '''Get the previous mode'''
        modeAsFound = system.tag.read(self.path + '/mode/value').value
        
        ''' writeDatum for a controller supports writing values to the OP, SP, or MODE, one at a time. '''    
        log.tracef("In %s.writeDatum() %s - %s - %s", __name__, self.path, str(val), valueType)
        if string.upper(valueType) in ["SP", "SETPOINT"]:
            tagRoot = self.path + '/sp'
            targetTag = self.spTag
            valueType = 'sp'
            #Change the mode to CAS
            modeSuccess, errorMessage = self.writeDatum('CAS','MODE')
            
            #Abort the write if the mode cannot be confirmed
            if not(modeSuccess):
                log.errorf(errorMessage)
                #return False, errorMessage
        elif string.upper(valueType) in ["OP", "OUTPUT"]:
            tagRoot = self.path + '/op'
            targetTag = self.opTag
            valueType = 'op'
            #Change the mode to CAS
            modeSuccess, errorMessage = self.writeDatum('CAS','MODE')
            
            #Abort the write if the mode cannot be confirmed
            if not(modeSuccess):
                log.errorf(errorMessage)
                #return False, errorMessage
        elif string.upper(valueType) in ["MODE"]:
            tagRoot = self.path + '/mode'
            targetTag = self.modeTag
            valueType = 'mode'
        else:
            log.errorf("Unexpected value Type: <%s>", valueType)
            raise Exception("Unexpected value Type: <%s>" % (valueType))
        
        confirmTagPath = tagRoot + '/value'

        ''' Check the basic configuration of the tag we are trying to write to. '''
        success, errorMessage = self.checkConfig(tagRoot + "/value")
        if not(success):
            system.tag.write(self.path + "/writeStatus", "Failure")
            system.tag.write(self.path + "/writeErrorMessage", errorMessage)
            log.infof("Aborting write to %s, checkConfig failed due to: %s", tagRoot, errorMessage)
            return False, errorMessage

        '''No need to check the permissive because it only needs to be PROGRAM for a SETPOINT RAMP, which is handled in the writeRamp function'''
        
        ''' reset the UDT '''
        self.reset()
        time.sleep(1)
            
        '''
        If we got this far, then the mode was successfully written (or we don't care about confirming it, so
        write the value to the OPC tag.  WriteDatum ALWAYS does a write confirmation.  The gateway is going to confirm 
        the write so this needs to just wait around for the answer
        '''
            
        log.tracef("Writing %s to %s", str(val), tagRoot)
        system.tag.write(self.path + "/writeStatus", "Writing %s to %s" % (str(val), tagRoot))       
        confirmed, errorMessage = targetTag.writeDatum(val, valueType, confirmTagPath)
         
        ''' Return the mode to its original value.  Don't let the success or failure of this override the result of the overall write. '''
        system.tag.write(self.path + '/mode/value', modeAsFound)
        
        return confirmed, errorMessage

    def checkConfig(self, tagRoot):
        ''' Perform a really basic check of the configuration of a tag '''
        log.tracef("In %s.checkConfig, checking %s", __name__, tagRoot)
        
        from ils.io.util import checkConfig
        configOK, errorMsg = checkConfig(self.path)
        if not(configOK):
            return configOK, errorMsg
        
        '''
        The I/O module is designed for OPC I/O, if we are writing to memory tags then we don't use the I/O API.
        However, if we are using isolation tags then we DO write to memory tags!  If we are writing to memory tags then 
        it doesn't make sense to check for an item id or OPC server.
        '''
        tagType = system.tag.read(tagRoot + ".TagType").value
        if tagType == 1:
            return True, ""
        
        itemPath = system.tag.getAttribute(tagRoot, "OPCItemPath")
        if itemPath == "":
            return False, "%s OPCItemPath is not configured" % (tagRoot)

        server = system.tag.getAttribute(tagRoot, "OPCServer")
        if server == "":
            return False, "%s OPCServer is not configured" % (tagRoot)
        
        return True, ""
    
    def confirmControllerMode(self, newVal, testForZero, checkPathToValve, outputType):
        '''
        Check if a controller is in the appropriate mode for writing to.  This does not attempt to change the 
        mode of the controller.  Return True if the controller is in the correct mode for writing.
        This is equivalent to s88-confirm-controller-mode in the old system. 
        '''
        success = True
        errorMessage = ""
        
        log.tracef("In %s.confirmControllerMode checking the configuration of TDC controller %s for writing %s to %s", __name__, self.path, str(newVal), outputType)
        
        permissiveRoot = '/permissive'
        rcasRoot = '/rcasopt'
        
        ''' Determine which tag in the controller we are seeking to write to '''
        if string.upper(outputType) in ["SP", "SETPOINT", "SETPOINT RAMP"]:
            tagRoot = self.path + '/sp'
        elif string.upper(outputType) in ["OP", "OUTPUT", "OUTPUT RAMP"]:
            tagRoot = self.path + '/op'
        else:
            raise Exception("Unexpected value Type: <%s> for an HPM controller %s" % (outputType, self.path))

        ''' Read the current values of all of the tags we need to consider to determine if the configuration is valid. '''
        tagpaths = [tagRoot + '/value', self.path + '/mode/value',  self.path + '/mode/value.OPCItemPath', self.path + '/windup', self.path + rcasRoot, self.path + permissiveRoot]
        qvs = system.tag.readAll(tagpaths)
        
        currentValue = qvs[0]
        mode = qvs[1]
        modeItemId = qvs[2].value
        windup = qvs[3]
        rcasOpt = qvs[4]
        permissiveVal = qvs[5]
        
        ''' Check the quality of the tags to make sure we can trust their values '''
        if str(currentValue.quality) != 'Good': 
            errorMessage = "The %s quality is %s" % (outputType, str(currentValue.quality)) 
            log.warnf("checkConfig failed for %s because %s. (tag: %s)", modeItemId, errorMessage, self.path)
            return False, errorMessage, modeItemId

        ''' The quality is good so not get the values in a convenient form '''
        currentValue = float(currentValue.value)
        log.tracef("The current value which will be used for the 'Test For Zero' test is %s", str(currentValue))

        ''' Check the Mode '''
        if str(mode.quality) != 'Good':
            errorMessage = "The mode quality is %s" % (str(mode.quality))
            log.warnf("checkConfig failed for %s because %s. (tag: %s)", modeItemId, errorMessage, self.path)
            return False, errorMessage, modeItemId
        
        mode = string.strip(mode.value)
        
        ''' Check the Windup  - Check the quality of the tags to make sure we can trust their values '''
        if str(windup.quality) != 'Good':
            errorMessage = "The windup quality is %s" % (str(windup.quality))
            log.warnf("checkConfig failed for %s because %s. (tag: %s)", modeItemId, errorMessage, self.path)
            return False, errorMessage, modeItemId

        windup = string.strip(windup.value)        
        
        ''' Check the RCasOpt  - Check the quality of the tags to make sure we can trust their values '''
        if str(rcasOpt.quality) != 'Good':
            errorMessage = "The RCasopt quality is %s" % (str(rcasOpt.quality))
            log.warnf("checkConfig failed for %s because %s. (tag: %s)", modeItemId, errorMessage, self.path)
            return False, errorMessage, modeItemId

        rcasOpt = string.strip(rcasOpt.value)
        
        ''' Check the Permissive  - Check the quality of the tags to make sure we can trust their values '''
        if str(permissiveVal.quality) != 'Good':
            errorMessage = "The permissive quality is %s" % (str(permissiveVal.quality))
            log.warnf("checkConfig failed for %s because %s. (tag: %s)", modeItemId, errorMessage, self.path)
            return False, errorMessage, modeItemId

        permissiveVal = string.strip(permissiveVal.value)
        
        log.infof("%s: %s=%s, windup=%s, mode:%s, rcasopt:%s, permissive:%s", self.path, outputType, str(currentValue), windup, mode, rcasOpt, permissiveVal)

        ''' For outputs check that the mode is CASCADE and RCASOpt is DDC '''
        if string.upper(outputType) in ["OP", "OUTPUT", "OUTPUT RAMP"]:
            if string.upper(mode) != 'CAS':
                success = False
                errorMessage = "the controller is not in CAS (current mode is <%s>)" % (mode)
            
            if string.upper(rcasOpt) != 'DDC':
                success = False
                errorMessage = "the controller does not have the appropriate RCasOpt to accept outputs"
                
        elif string.upper(outputType) in ["SP", "SETPOINT"]:
            ''' For setpoints, check that there is a path to the valve, mode = auto and sp = 0.  The path to valve check is optional '''
            if string.upper(windup) == 'HILO' and checkPathToValve:
                success = False
                errorMessage = "the controller has no path to valve"
        
            if string.upper(mode) != 'CAS':
                success = False
                errorMessage = "%s the controller is not in CAS (mode is actually %s)" % (errorMessage, mode)
            
            if string.upper(rcasOpt) != 'SPC':
                success = False
                errorMessage = "the controller does not have the appropriate RCasOpt to accept setpoints"
            '''
            The testForZero check is used when we expect the starting point for the write to be 0, i.e. a closed valve.
            If we expect the current SP to be 0, and it isn't, then the state of the plant is not what we expect so
            warn the operator.  See s88-confirm-controller-mode(opc-pks-controller)
            '''
            if (currentValue > (float(newVal) * 0.03)) and testForZero:
                success = False
                errorMessage = "%s the controller setpoint is not zero (it is actually %f)" % (errorMessage, currentValue)
                
        elif string.upper(outputType) == "SETPOINT RAMP":
            ''' For setpoints, check that there is a path to the valve, mode = auto and sp = 0.  The path to valve check is optional '''
            if string.upper(windup) == 'HILO' and checkPathToValve:
                success = False
                errorMessage = "the controller has no path to valve"
        
            if string.upper(mode) != 'AUTO':
                success = False
                errorMessage = "%s the controller is not in AUTO (mode is actually %s)" % (errorMessage, mode)
            
            if string.upper(permissiveVal) != 'PROGRAM':
                success = False
                errorMessage = "the controller is not have mode attribute PROGRAM so it cannot have its ramp set"
                
            '''
            The testForZero check is used when we expect the starting point for the write to be 0, i.e. a closed valve.
            If we expect the current SP to be 0, and it isn't, then the state of the plant is not what we expect so
            warn the operator.  See s88-confirm-controller-mode(opc-pks-controller)
            '''
            if (currentValue > (float(newVal) * 0.03)) and testForZero:
                success = False
                errorMessage = "%s the controller setpoint is not zero (it is actually %f)" % (errorMessage, currentValue)
        else:
            success = False
            errorMessage = "Unknown output type: %s" % (outputType)

        log.infof("  confirmControllerMode returned: %s - %s", str(success), errorMessage)
        return success, errorMessage, modeItemId
    
    # 
    
    def writeOPRamp(self, val, valType, rampTime, updateFrequency, writeConfirm):
        success = True
        errorMessage = ''
        
        modeValue = 'CAS'
        valuePathRoot = self.path + '/op'
        targetTag = self.opTag
        
        ''' Check the basic configuration of the tag we are trying to write to. '''
        success, errorMessage = self.checkConfig(valuePathRoot + "/value")
        if not(success):
            system.tag.write(self.path + "/writeStatus", "Failure")
            system.tag.write(self.path + "/writeErrorMessage", errorMessage)
            log.infof("Aborting write to %s, checkConfig failed due to: %s", valuePathRoot, errorMessage)
            return False, errorMessage

        ''' reset the UDT '''
        self.reset()
        time.sleep(1)
        
        ''' Put the controller into the appropriate mode '''
        modeTag = self.modeTag
        confirmed, errorMessage = modeTag.writeDatum(modeValue, 'mode')
        if not(confirmed):
            log.warnf("Warning: TDC Controller <%s> - the controller mode <%s> could not be confirmed, attempting to write the ramp anyway!", self.path, modeValue)
        
        confirmMode, errorMessage, _ = self.confirmControllerMode(val, False, True, "OUTPUT RAMP")
        if not(confirmMode):
            log.errorf(errorMessage)
            return False, errorMessage
        
        ''' Read the starting point for the ramp which is the current value '''
        startValue = system.tag.read(valuePathRoot + '/value')
        if str(startValue.quality) != 'Good':
            errorMessage = "ERROR: TDC Controller <%s> - ramp aborted due to inability to read the starting value for a %s from <%s>!" % (self.path, valType, valuePathRoot)
            log.errorf(errorMessage)
            return False, errorMessage

        startValue = startValue.value

        log.infof("Ramping the %s of TDC controller <%s> from %s to %s over %s minutes", valType, self.path, str(startValue), str(val), str(rampTime))
        baseTxt = "Ramping the %s from %s to %s over %s minutes" % (valType, str(startValue), str(val), str(rampTime))
        system.tag.write(self.path + "/writeStatus", baseTxt)

        rampTimeSeconds = float(rampTime) * 60.0

        from ils.common.util import equationOfLine
        m, b = equationOfLine(0.0, startValue, rampTimeSeconds, val)
        startTime = system.date.now()
        deltaSeconds = system.date.secondsBetween(startTime, system.date.now())
        
        while (deltaSeconds < rampTimeSeconds):
            from ils.common.util import calculateYFromEquationOfLine
            aVal = calculateYFromEquationOfLine(deltaSeconds, m, b)
            
            log.tracef("HPM Controller <%s> ramping to %s (elapsed time: %s)", self.path, str(aVal), str(deltaSeconds))
            
            #Stop the ramp if the controller is taken out of CAS
            qv = system.tag.read(self.path + '/mode/value')
            if str(qv.quality) == 'Good':
                mode = str(qv.value)
                mode = string.strip(mode)
                mode = string.upper(mode)
                if mode != 'CAS':
                    break
                
            targetTag.writeWithNoCheck(aVal)
            
            txt = "%s (%.2f at %s)" % (baseTxt, aVal, str(deltaSeconds))
            system.tag.write(self.path + "/writeStatus", txt)
 
            ''' Time in seconds '''
            time.sleep(updateFrequency)
            deltaSeconds = system.date.secondsBetween(startTime, system.date.now())
        
        # Write the final point and confirm this one only if the mode is CAS
        qv = system.tag.read(self.path + '/mode/value')
        if str(qv.quality) == 'Good':
            mode = str(qv.value)
            mode = string.strip(mode)
            mode = string.upper(mode)
            if mode == 'CAS':
                log.infof("HPM Controller <%s> writing the final value of the ramp!", self.path)
                targetTag.writeDatum(val, valType)

        # Return the mode to MAN when finished ramping an OP
        confirmed, errorMessage = modeTag.writeDatum('MAN', 'mode')
        if not(confirmed):
            log.warnf("Warning: TDC Controller <%s> - the controller mode <%s> could not be confirmed after completing the ramp!", self.path, modeValue)
            
        log.infof("%s - <%s> done ramping!", __name__, self.path)
        return success, errorMessage
    
    def writeSPRamp(self, val, valType, rampTime, updateFrequency, writeConfirm):
        success = True
        errorMessage = ''
        
        ''' Change  the mode of the controller and set the desired ramp type '''
        modeValue = 'AUTO'
        valuePathRoot = self.path + '/sp'
        targetTag = self.spTag
        
        ''' Check the basic configuration of the tag we are trying to write to. '''
        success, errorMessage = self.checkConfig(valuePathRoot + "/value")
        if not(success):
            system.tag.write(self.path + "/writeStatus", "Failure")
            system.tag.write(self.path + "/writeErrorMessage", errorMessage)
            log.infof("Aborting write to %s, checkConfig failed due to: %s", valuePathRoot, errorMessage)
            return False, errorMessage

        ''' reset the UDT '''
        self.reset()
        time.sleep(1)
        
        ''' Set the permissive '''
        confirmed, errorMessage = self.setPermissive()
        if not(confirmed):
            return confirmed, errorMessage
        
        ''' Put the controller into the appropriate mode '''
        modeTag = self.modeTag
        confirmed, errorMessage = modeTag.writeDatum(modeValue, 'mode')
        if not(confirmed):
            log.warnf("Warning: TDC Controller <%s> - the controller mode <%s> could not be confirmed, attempting to write the ramp anyway!", self.path, modeValue)

        confirmMode, errorMessage, _ = self.confirmControllerMode(val, False, True, "SETPOINT RAMP")
        if not(confirmMode):
            log.error(errorMessage)
            return False, errorMessage
        
        log.tracef("In %s.writeRamp() writing a setpoint ramp for controller %s", __name__, self.path)
        
        # Check the basic configuration of the tag we are trying to write to.
        success, errorMessage = self.checkConfig(valuePathRoot + "/value")
        if not(success):
            system.tag.write(self.path + "/writeStatus", "Failure")
            system.tag.write(self.path + "/writeErrorMessage", errorMessage)
            log.infof("Aborting write to %s, checkConfig failed due to: %s", valuePathRoot, errorMessage)
            return False, errorMessage
        
        log.infof("Ramping the %s of TDC controller <%s> to %s over %s minutes", valType, self.path, str(val), str(rampTime))
        system.tag.write(self.path + "/writeStatus", "Ramping the %s to %s over %s minutes" % (valType, str(val), str(rampTime)))

        log.trace("...writing PRESET to the rampstate...")
        system.tag.write(self.path + "/sp/rampState", "PRESET")            
        time.sleep(self.OPC_LATENCY_TIME)

        '''   ramp time must always be in minutes '''
        
        log.tracef("...writing %f to the targetValue and %f to the ramptime...", val, rampTime)
        system.tag.write(self.path + "/sp/rampTime", rampTime)
        system.tag.write(self.path + "/sp/setpointTargetValue", val)
        time.sleep(self.OPC_LATENCY_TIME)
        
        log.trace("...writing RUN to the rampstate...")
        system.tag.write(self.path + "/sp/rampState", "RUN")
        time.sleep(self.OPC_LATENCY_TIME)
        
        log.infof("TDC Controller <%s> done ramping!", self.path)
        return success, errorMessage
    
    def writeRamp(self, val, valType, rampTime, updateFrequency, writeConfirm):
        '''
        This method makes sequential writes to ramp the OP, or configuration of the DCS SPTV of an HPM controller.  
        There is no native output ramping capability in HPM and this method fills the gap.  
        It assumes that the ramp time is in minutes.. 
        *** This is called by a tag change script and runs in the gateway ***
        '''   
        success = True
        log.infof("In %s.writeRamp() Writing %s for controller %s", __name__, valType, self.path)

        if val == None or rampTime == None or writeConfirm == None or valType == None or updateFrequency == None:
            log.errorf("ERROR writing ramp for HPM controller: %s - One or more of the required arguments is missing val=%s rampTime=%s writeConfirm=%s valType=%s updateFreq=%s" % (self.path,val,rampTime,writeConfirm,valType,updateFrequency))
            return False, "One or more of the required arguments is missing"
        
        '''Check what type of ramp we want to perform and call the appropriate sub-function'''
        if string.upper(valType) == "OUTPUT RAMP":
            status, errorMessage = self.writeOPRamp(val, valType, rampTime, updateFrequency, writeConfirm)
            return status, errorMessage
        
        elif string.upper(valType) == "SETPOINT RAMP":
            status, errorMessage = self.writeSPRamp(val, valType, rampTime, updateFrequency, writeConfirm)
            return status, errorMessage
        
        else:
            log.errorf("ERROR writing ramp for HPM controller: %s - Unexpected value type <%s>", self.path, valType)
            return False, "Unexpected value type <%s>" % (valType)
        
    def writeWithNoCheck(self, val, valueType):
        ''' WiteWithNoCheck for a controller supports writing values to the OP, SP, or MODE, one at a time. ''' 
        log.tracef("%s.writeWithNoCheck() %s - %s - %s", __name__, self.path, str(val), valueType)
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
            log.errorf("Unexpected value Type: <%s>", valueType)
            raise Exception("Unexpected value Type: <%s>" % (valueType))

        ''' Check the basic configuration of the tag we are trying to write to. '''
        success, errorMessage = self.checkConfig(tagRoot + "/value")
        if not(success):
            system.tag.write(self.path + "/writeStatus", "Failure")
            system.tag.write(self.path + "/writeErrorMessage", errorMessage)
            log.infof("Aborting write to %s, checkConfig failed due to: %s", tagRoot, errorMessage)
            return False, errorMessage
        
        # Check the basic configuration of the permissive of the controller we are writing to.
        success, errorMessage = self.checkConfig(self.path + '/permissive')
        if not(success):
            system.tag.write(self.path + "/writeStatus", "Failure")
            system.tag.write(self.path + "/writeErrorMessage", errorMessage)
            log.infof("Aborting write to %s, checkConfig failed due to: %s", self.path + '/permissive', errorMessage)
            return False, errorMessage
        
        
        ''' reset the UDT '''
        self.reset()
        time.sleep(1)
        
        """
        '''
        ----------------------
         Set the permissive
        ---------------------- '''
        
        log.trace("Writing permissive...")
        
        ''' Update the status to "Writing" '''
        system.tag.write(self.path + "/writeStatus", "Writing Permissive")
 
        ''' Read the current permissive and save it so that we can put it back the way is was when we are done '''
        permissiveAsFound = system.tag.read(self.path + "/permissive").value
        log.tracef("   permisive as found: %s", permissiveAsFound)
        
        ''' Get from the configuration of the UDT the value to write to the permissive and whether or not it needs to be confirmed '''
        permissiveValue = system.tag.read(self.path + "/permissiveValue").value
        permissiveConfirmation = system.tag.read(self.path + "/permissiveConfirmation").value
        
        ''' Write the permissive value to the permissive tag and wait until it gets there '''
        log.tracef("   writing permissive value: %s", permissiveValue)
        system.tag.write(self.path + "/permissive", permissiveValue)
        
        ''' 
        Confirm the permissive if necessary.  If the UDT is configured for confirmation, then it MUST be confirmed 
        for the write to proceed.  This has nothing to do with confirming the write.
        '''
        if permissiveConfirmation:
            log.trace("   confirming permissive...")
            system.tag.write(self.path + "/writeStatus", "Confirming Permissive")
            from ils.io.util import confirmWrite
            confirmed, errorMessage = confirmWrite(self.path + "/permissive", permissiveValue, self.CONFIRM_TIMEOUT)
 
            if confirmed:
                log.tracef("   confirmed Permissive write: %s - %s", self.path, permissiveValue)
            else:
                errorMessage = "Failed to confirm permissive write of <%s> to %s because %s" % (str(permissiveValue), self.path, errorMessage)
                log.error(errorMessage)
                system.tag.write(self.path + "/writeStatus", "Failure")
                system.tag.write(self.path + "/writeErrorMessage", errorMessage)
                return confirmed, errorMessage
        else:
            log.trace("...dwelling in lieu of permissive confirmation...")
            time.sleep(self.PERMISSIVE_LATENCY_TIME)
            
        ''' 
        If we got this far, then the permissive was successfully written (or we don't care about confirming it, so
        write the value to the OPC tag.  WriteDatum ALWAYS does a write confirmation.  The gateway is going to confirm 
        the write so this needs to just wait around for the answer
        '''
        """
        log.tracef("Writing %s to %s", str(val), tagRoot)
        system.tag.write(self.path + "/writeStatus", "Writing %s to %s" % (str(val), tagRoot))       
        confirmed, errorMessage = targetTag.writeWithNoCheck(val, valueType)
        if not(confirmed):
            log.error(errorMessage)
            system.tag.write(self.path + "/writeStatus", "Failure")
            system.tag.write(self.path + "/writeErrorMessage", errorMessage)
            return confirmed, errorMessage
         
        ''' Return the permissive to its original value.  Don't let the success or failure of this override the result of the overall write. '''
        """
        ''' Since we didn't confirm the write above, we need to wait for a latency time to give the value a chance to '''
        log.trace("...dwelling after the value write and before the permissive restore...")
        time.sleep(self.PERMISSIVE_LATENCY_TIME)

        log.trace("Restoring permissive")
        system.tag.write(self.path + "/permissive", permissiveAsFound)
        if permissiveConfirmation:
            confirmed, confirmMessage = confirmWrite(self.path + "/permissive", permissiveAsFound, self.CONFIRM_TIMEOUT)
            
            if confirmed:    
                log.tracef("Confirmed Permissive restore: %s", self.path)
            else:
                txt = "Failed to confirm permissive write of <%s> to %s because %s" % (str(val), self.path, confirmMessage)
                log.error(txt)
                system.tag.write(self.path + "/writeStatus", "Failure")
                system.tag.write(self.path + "/writeErrorMessage", txt)
        """