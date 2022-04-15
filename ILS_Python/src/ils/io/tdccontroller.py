'''
Created on Dec 1, 2014

@author: Pete
'''

import ils.io.controller as controller
import system, string, time
from ils.io.util import confirmWrite, readTag, writeTag
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
import ils.io.opcoutput as opcoutput
log = LogUtil.getLogger("com.ils.io")

class TDCController(controller.Controller):
    opTag = None
    spTag = None
    CONFIRM_TIMEOUT = 10.0
    PERMISSIVE_LATENCY_TIME = 0.0
    OPC_LATENCY_TIME = 0.0
    
    def __init__(self,path):
        controller.Controller.__init__(self,path)
        self.spTag = opcoutput.OPCOutput(path + '/sp')
        self.opTag = opcoutput.OPCOutput(path + '/op')
        self.PERMISSIVE_LATENCY_TIME = readTag("[%s]Configuration/Common/opcPermissiveLatencySeconds" % (self.tagProvider)).value

    def reset(self):
        ''' Reset the UDT in preparation for a write  '''
        log.trace('Resetting a TDCController...')
        status = True
        errorMessage = ""
        writeTag(self.path + '/badValue', False)
        writeTag(self.path + '/writeErrorMessage', '')
        writeTag(self.path + '/writeConfirmed', False)
        writeTag(self.path + '/writeStatus', '')
        
        for embeddedTag in ['/mode', '/op', '/sp']:
            tagPath = self.path + embeddedTag
            writeTag(tagPath + '/badValue', False)
            writeTag(tagPath + '/writeErrorMessage', '')
            writeTag(tagPath + '/writeConfirmed', False)
            writeTag(tagPath + '/writeStatus', '')
            
        log.trace('...done resetting a TDCController!')
        return status, errorMessage

    #  
    def confirmControllerMode(self, newVal, testForZero, checkPathToValve, outputType):
        ''' Check if a controller is in the appropriate mode for writing to.  This does not attempt to change the 
        mode of the controller.  Return True if the controller is in the correct mode for writing.
        This is equivalent to s88-confirm-controller-mode in the old system. '''
        success = True
        errorMessage = ""
        
        log.trace("In %s checking the configuration of PKS controller %s for writing %s to %s" % (__name__, self.path, str(newVal), outputType))
        
        #TODO Need to add support for a setpoint ramp here and at the end.
        
        ''' Determine which tag in the controller we are seeking to write to '''
        if string.upper(outputType) in ["SP", "SETPOINT", "SETPOINT RAMP"]:
            tagRoot = self.path + '/sp'
        elif string.upper(outputType) in ["OP", "OUTPUT", "OUTPUT RAMP"]:
            tagRoot = self.path + '/op'
        else:
            raise Exception("Unexpected value Type: <%s> for a TDC controller %s" % (outputType, self.path))

        ''' Read the current values of all of the tags we need to consider to determine if the configuration is valid. '''
        tagpaths = [tagRoot + '/value', self.path + '/mode/value',  self.path + '/mode/value.OPCItemPath', self.path + '/outputDisposability/value']
        qvs = system.tag.readBlocking(tagpaths)
        
        currentValue = qvs[0]
        mode = qvs[1]
        modeItemId = qvs[2].value
        outputDisposability = qvs[3]

        ''' Check the quality of the tags to make sure we can trust their values '''
        if str(currentValue.quality) != 'Good': 
            errorMessage = "The %s quality is %s" % (outputType, str(currentValue.quality)) 
            log.warnf("checkConfig failed for %s because %s. (tag: %s)", modeItemId, errorMessage, self.path)
            return False, errorMessage, modeItemId

        ''' The quality is good so not get the values in a convenient form '''
        currentValue = float(currentValue.value)

        ''' Check the Mode '''
        if str(mode.quality) != 'Good':
            errorMessage = "The mode quality is %s" % (str(mode.quality))
            log.warnf("checkConfig failed for %s because %s. (tag: %s)", modeItemId, errorMessage, self.path)
            return False, errorMessage, modeItemId
        
        mode = string.strip(mode.value)
        
        ''' Check the Output Disposability - Check the quality of the tags to make sure we can trust their values '''
        if str(outputDisposability.quality) != 'Good': 
            errorMessage = "the outputDisposability quality is %s" % (str(outputDisposability.quality))
            log.warnf("checkConfig failed for %s because %s. (tag: %s)", modeItemId, errorMessage, self.path)
            return False, errorMessage, modeItemId

        outputDisposability = string.strip(outputDisposability.value)        

        log.trace("%s: %s=%s, outputDisposability=%s, mode:%s" % (self.path, outputType, str(currentValue), outputDisposability, mode))

        ''' For outputs check that the mode is MANUAL - no other test is required '''
        if string.upper(outputType) in ["OP", "OUTPUT", "OUTPUT RAMP"]:
            if string.upper(mode) != 'MAN':
                success = False
                errorMessage = "the controller is not in manual (mode is actually %s)" % (mode)

        elif string.upper(outputType) in ["SP", "SETPOINT", "SETPOINT RAMP"]:
            ''' For setpoints, check that there is a path to the valve, mode = auto and sp = 0.  The path to valve check is optional '''
            #TODO Not sure if output disposability has the same values as windup...
            if string.upper(outputDisposability) == 'HILO' and checkPathToValve:
                success = False
                errorMessage = "the controller has no path to valve"
        
            if string.upper(mode) <> 'AUTO':
                success = False
                errorMessage = "%s the controller is not in automatic (mode is actually %s)" % (errorMessage, mode)

            ''' The testForZero check is used when we expect the starting point for the write to be 0, i.e. a closed valve.
            If we expect the current SP to be 0, and it isn't, then the state of the plant is not what we expect so
            warn the operator.  See s88-confirm-controller-mode(opc-pks-controller) '''
            if (currentValue > (float(newVal) * 0.03)) and testForZero:
                success = False
                errorMessage = "%s the controller setpoint is not zero (it is actually %f)" % (errorMessage, currentValue)

        else:
            success = False
            errorMessage = "Unknown output type: %s" % (outputType)
            
        log.trace("checkConfiguration conclusion: %s - %s" % (str(success), errorMessage))
        return success, errorMessage, modeItemId
    
    def writeDatum(self, val, valueType):
        ''' writeDatum for a controller supports writing values to the OP, SP, or MODE, one at a time '''   
        log.tracef("In %s.writeDatum() %s - %s - %s", __name__, self.path, str(val), valueType)
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
            writeTag(self.path + "/writeStatus", "Failure")
            writeTag(self.path + "/writeErrorMessage", errorMessage)
            log.infof("Aborting write to %s, checkConfig failed due to: %s", tagRoot, errorMessage)
            return False, errorMessage
        
        ''' reset the UDT '''
        self.reset()
        time.sleep(1)
        
        ''' Write the value to the OPC tag.  WriteDatum ALWAYS does a write confirmation.  The gateway is going to confirm 
        the write so this needs to just wait around for the answer '''

        log.tracef("Writing %s to %s", str(val), tagRoot)
        writeTag(self.path + "/writeStatus", "Writing %s to %s" % (str(val), tagRoot))       
        confirmed, errorMessage = targetTag.writeDatum(val, valueType)
        
        return confirmed, errorMessage

    def checkConfig(self, tagRoot):
        ''' Perform a really basic check of the configuration of a tag '''
        log.tracef("In %s.checkConfig, checking %s", __name__, tagRoot)
        
        from ils.io.util import checkConfig
        configOK, errorMsg = checkConfig(self.path)
        if not(configOK):
            return configOK, errorMsg
        
        '''
        The I/O module is designer for OPC I/O, if we are writing to memory tags then we don't use the I/O API.
        However, if we are using isolation tags then we DO write to memory tags!  If we are writing to memory tags then 
        it doesn't make sense to check for an item id or OPC server.
        '''
        tagType = readTag(tagRoot + ".TagType").value
        if tagType == 1:
            return True, ""
        
        itemPath = system.tag.getAttribute(tagRoot, "OPCItemPath")
        if itemPath == "":
            return False, "%s OPCItemPath is not configured" % (tagRoot)

        server = system.tag.getAttribute(tagRoot, "OPCServer")
        if server == "":
            return False, "%s OPCServer is not configured" % (tagRoot)
        
        return True, ""
    
    # 
    def writeRamp(self, val, valType, rampTime, updateFrequency, writeConfirm):
        ''' This method makes sequential writes to ramp either the SP or OP of an Experion controller.  
        There is no native output ramping capability in EPKS and this method fills the gap.  
        In addition, it will ramp the SP of a controller that isn't built in G2 as having native EPKS SP Ramp capability.  
        In both cases, the ramp is executed by writing sequentially based on a linear ramp.  
        It assumes that the ramp time is in minutes.. 
            *** This is called by a tag change script and runs in the gateway *** '''
        
        success = True
        log.tracef("In %s.writeRamp() Writing ramp for controller %s", __name__, self.path)

        if val == None or rampTime == None or writeConfirm == None or valType == None or updateFrequency == None:
            log.errorf("ERROR writing ramp for PKS controller: %s - One or more of the required arguments is missing", self.path)
            return False, "One or more of the required arguments is missing"

        ''' Change  the mode of the controller and set the desired ramp type '''
        if string.upper(valType) == "SETPOINT RAMP":
            modeValue = 'AUTO'
            valuePathRoot = self.path + '/sp'
            targetTag = self.spTag

        elif string.upper(valType) == "OUTPUT RAMP":
            modeValue = 'MAN'
            valuePathRoot = self.path + '/op'
            targetTag = self.opTag

        else:
            log.errorf("ERROR writing ramp for PKS controller: %s - Unexpected value type <%s>", self.path, valType)
            return False, "Unexpected value type <%s>" % (valType)
        
        ''' Check the basic configuration of the tag we are trying to write to. '''
        success, errorMessage = self.checkConfig(valuePathRoot + "/value")
        if not(success):
            writeTag(self.path + "/writeStatus", "Failure")
            writeTag(self.path + "/writeErrorMessage", errorMessage)
            log.infof("Aborting write to %s, checkConfig failed due to: %s", valuePathRoot, errorMessage)
            return False, errorMessage

        
        ''' Put the controller into the appropriate mode '''
        modeTag = self.modeTag
        confirmed, errorMessage = modeTag.writeDatum(modeValue, 'mode')
        if not(confirmed):
            log.warnf("Warning: TDC Controller <%s> - the controller mode <%s> could not be confirmed, attempting to write the ramp anyway!", self.path, modeValue)

        ''' Read the starting point for the ramp which is the current value '''
        startValue = readTag(valuePathRoot + '/value')
        if str(startValue.quality) != 'Good':
            errorMessage = "ERROR: TDC Controller <%s> - ramp aborted due to inability to read the initial <%s> setpoint!" % (self.path, valType)
            log.error(errorMessage)
            return False, errorMessage

        startValue = startValue.value

        baseTxt = "Ramping the %s of TDC controller <%s> from %s to %s over %s minutes" % (valType, self.path, str(startValue), str(val), str(rampTime))
        log.infof(baseTxt)
        writeTag(self.path + "/writeStatus", baseTxt)

        rampTimeSeconds = float(rampTime) * 60.0

        from ils.common.util import equationOfLine
        m, b = equationOfLine(0.0, startValue, rampTimeSeconds, val)
        startTime = system.date.now()
        deltaSeconds = system.date.secondsBetween(startTime, system.date.now())
        print "rampTimeSeconds: ", rampTimeSeconds
        print "deltaSeconds: ", deltaSeconds
        
        while (deltaSeconds < rampTimeSeconds):
            from ils.common.util import calculateYFromEquationOfLine
            aVal = calculateYFromEquationOfLine(deltaSeconds, m, b)
            
            log.tracef("TDC Controller <%s> ramping to %s (elapsed time: %s)", self.path, str(aVal), str(deltaSeconds))
            
            #CRC Edit 1/6/2021 to only write if you are still in PROGRAM
            qvs = system.tag.readBlocking([self.path + "/permissive", self.path + "/permissiveValue"])
            permissiveCheck = (qvs[0].value == qvs[1].value)
            if not(permissiveCheck):
                print "Exiting because it failed the permissive check"
                self.permissiveAsFound = qvs[0].value
                break
            #End CRC Edit 1/6/2021
            
            targetTag.writeWithNoCheck(aVal)
            
            txt = "%s (%.2f at %s)" % (baseTxt, aVal, str(deltaSeconds))
            writeTag(self.path + "/writeStatus", txt)
 
            ''' Time in seconds '''
            time.sleep(updateFrequency)
            deltaSeconds = system.date.secondsBetween(startTime, system.date.now())
        
        ''' Write the final point and confirm this one '''
        #CRC Edit 1/6/2021 to only write if you are still in PROGRAM
        qvs = system.tag.readBlocking([self.path + "/permissive", self.path + "/permissiveValue"])
        permissiveCheck = (qvs[0].value == qvs[1].value)
        if permissiveCheck:
            targetTag.writeDatum(val, valType)
        #End CRC Edit 1/6/2021

        ''' For a PKS controller, we restore the permissive here, not sure why we don't do that for TDC '''
            
        log.infof("%s - <%s> done ramping!", __name__, self.path)
        return success, errorMessage
    
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
            writeTag(self.path + "/writeStatus", "Failure")
            writeTag(self.path + "/writeErrorMessage", errorMessage)
            log.infof("Aborting write to %s, checkConfig failed due to: %s", tagRoot, errorMessage)
            return False, errorMessage
        
        ''' reset the UDT '''
        self.reset()
        time.sleep(1)
                    
        ''' Write the value to the OPC tag. '''
        log.tracef("Writing %s to %s", str(val), tagRoot)
        writeTag(self.path + "/writeStatus", "Writing %s to %s" % (str(val), tagRoot))       
        confirmed, errorMessage = targetTag.writeWithNoCheck(val, valueType)
        if not(confirmed):
            log.error(errorMessage)
            writeTag(self.path + "/writeStatus", "Failure")
            writeTag(self.path + "/writeErrorMessage", errorMessage)
            return confirmed, errorMessage
        
        return confirmed, errorMessage