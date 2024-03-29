'''
Created on Nov 4, 2018

@author: phass
'''

import ils.io.controller as controller
import system, string, time
from ils.common.config import getTagProvider
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
import ils.io.opcoutput as opcoutput
log = LogUtil.getLogger("com.ils.io")

class TDCDigitalController(controller.Controller):
    opTag = None
    CONFIRM_TIMEOUT = 10.0
    PERMISSIVE_LATENCY_TIME = 0.0
    OPC_LATENCY_TIME = 0.0
    
    def __init__(self,path):
        controller.Controller.__init__(self,path)
        self.opTag = opcoutput.OPCOutput(path + '/op')
        provider = getTagProvider()
        self.PERMISSIVE_LATENCY_TIME = system.tag.read("[%s]Configuration/Common/opcPermissiveLatencySeconds" % (provider)).value
        self.OPC_LATENCY_TIME = system.tag.read("[%s]Configuration/Common/opcTagLatencySeconds" % (provider)).value

    def reset(self):
        ''' Reset the UDT in preparation for a write '''
        success = True
        errorMessage = ""
        log.tracef('Resetting a %s Controller...', __name__)       
        
        system.tag.write(self.path + '/badValue', False)
        system.tag.write(self.path + '/writeErrorMessage', '')
        system.tag.write(self.path + '/writeConfirmed', False)
        system.tag.write(self.path + '/writeStatus', '')
        
        for embeddedTag in ['/mode', '/op']:
            tagPath = self.path + embeddedTag
            system.tag.write(tagPath + '/badValue', False)
            system.tag.write(tagPath + '/writeErrorMessage', '')
            system.tag.write(tagPath + '/writeConfirmed', False)
            system.tag.write(tagPath + '/writeStatus', '')

    def confirmControllerMode(self, newVal, testForZero, checkPathToValve, outputType):
        ''' Check if a controller is in the appropriate mode for writing to.  This does not attempt to change the 
        mode of the controller.  Return True if the controller is in the correct mode for writing.
        This is equivalent to s88-confirm-controller-mode in the old system. '''
        success = True
        errorMessage = ""
        
        log.trace("In %s checking the configuration of PKS controller %s for writing %s to %s" % (__name__, self.path, str(newVal), outputType))
        
        #TODO Need to add support for a setpoint ramp here and at the end.
        
        ''' Determine which tag in the controller we are seeking to write to '''
        if string.upper(outputType) in ["OP", "OUTPUT"]:
            tagRoot = self.path + '/op'
        else:
            raise Exception("Unexpected value Type: <%s> for a TDC controller %s" % (outputType, self.path))

        ''' Read the current values of all of the tags we need to consider to determine if the configuration is valid. '''
        tagpaths = [tagRoot + '/value', self.path + '/mode/value',  self.path + '/mode/value.OPCItemPath', self.path + '/windup']
        qvs = system.tag.readAll(tagpaths)
        
        currentValue = qvs[0]
        mode = qvs[1]
        modeItemId = qvs[2].value
        windup = qvs[3]

        ''' Check the quality of the tags to make sure we can trust their values '''
        if str(currentValue.quality) != 'Good': 
            errorMessage = "the %s quality is %s" % (outputType, str(currentValue.quality)) 
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
        if str(windup.quality) != 'Good':
            errorMessage = "The windup quality is %s" % (str(windup.quality))
            log.warnf("checkConfig failed for %s because %s. (tag: %s)", modeItemId, errorMessage, self.path)
            return False, errorMessage, modeItemId

        windup = string.strip(windup.value)        

        log.trace("%s: %s=%s, windup=%s, mode:%s" % (self.path, outputType, str(currentValue), windup, mode))

        ''' For outputs check that the mode is MANUAL - no other test is required '''
        if string.upper(outputType) in ["OP", "OUTPUT"]:
            if string.upper(mode) != 'MAN':
                success = False
                errorMessage = "the controller is not in manual (mode is actually %s)" % (mode)
        else:
            success = False
            errorMessage = "Unknown output type: %s" % (outputType)
            
        log.trace("checkConfiguration conclusion: %s - %s" % (str(success), errorMessage))
        return success, errorMessage, modeItemId
    
    def writeDatum(self, val, valueType):
        ''' writeDatum for a controller supports writing values to the OP, SP, or MODE, one at a time. '''
        log.tracef("In %s.writeDatum() %s - %s - %s", __name__, self.path, str(val), valueType)

        if string.upper(valueType) in ["OP", "OUTPUT"]:
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
        
        ''' reset the UDT '''
        self.reset()
        time.sleep(1)
        
        ''' Write the value to the OPC tag.  WriteDatum ALWAYS does a write confirmation.  The gateway is going to confirm 
        the write so this needs to just wait around for the answer. '''

        log.tracef("Writing %s to %s", str(val), tagRoot)
        system.tag.write(self.path + "/writeStatus", "Writing %s to %s" % (str(val), tagRoot))       
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

    def writeWithNoCheck(self, val, valueType):
        ''' WiteWithNoCheck for a controller supports writing values to the OP, SP, or MODE, one at a time. '''
        log.tracef("%s.writeWithNoCheck() %s - %s - %s", __name__, self.path, str(val), valueType)
        
        if string.upper(valueType) in ["OP", "OUTPUT"]:
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
        
        ''' reset the UDT '''
        self.reset()
        time.sleep(1)
        
        ''' If we got this far, then the permissive was successfully written (or we don't care about confirming it, so
        write the value to the OPC tag.  WriteDatum ALWAYS does a write confirmation.  The gateway is going to confirm 
        the write so this needs to just wait around for the answer '''

        log.tracef("Writing %s to %s", str(val), tagRoot)
        system.tag.write(self.path + "/writeStatus", "Writing %s to %s" % (str(val), tagRoot))       
        confirmed, errorMessage = targetTag.writeWithNoCheck(val, valueType)
        if not(confirmed):
            log.error(errorMessage)
            system.tag.write(self.path + "/writeStatus", "Failure")
            system.tag.write(self.path + "/writeErrorMessage", errorMessage)
            return confirmed, errorMessage
         
        system.tag.write(self.path + "/writeStatus", "Success")
        
        return confirmed, errorMessage