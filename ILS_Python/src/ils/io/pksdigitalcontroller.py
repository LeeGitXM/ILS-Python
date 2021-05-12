'''
Created on Dec 6, 2018

@author: phass
'''

import ils.io.pkscontroller as pkscontroller
import system, string, time
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
import ils.io.opcoutput as opcoutput
log = LogUtil.getLogger(__name__)

class PKSDigitalController(pkscontroller.PKSController):
    
    def __init__(self,path):
        log.tracef("In %s.__int__()", __name__)
        pkscontroller.PKSController.__init__(self,path)

    def confirmControllerMode(self, newVal, testForZero, checkPathToValve, outputType):
        ''' Check if a controller is in the appropriate mode for writing to.  This does not attempt to change the 
        mode of the controller.  Return True if the controller is in the correct mode for writing.
        This is equivalent to s88-confirm-controller-mode in the old system. '''
        success = True
        errorMessage = ""
        
        log.trace("In %s checking the configuration of PKS controller %s for writing %s to %s" % (__name__, self.path, str(newVal), outputType))
        
        ''' Determine which tag in the controller we are seeking to write to '''
        if string.upper(outputType) in ["OP", "OUTPUT"]:
            tagRoot = self.path + '/op'
        else:
            raise Exception("Unexpected value Type: <%s> for a PKS Digital controller %s" % (outputType, self.path))

        ''' Read the current values of all of the tags we need to consider to determine if the configuration is valid. '''
        tagpaths = [tagRoot + '/value', self.path + '/mode/value',  self.path + '/mode/value.OPCItemPath']
        qvs = system.tag.readAll(tagpaths)
        
        currentValue = qvs[0]
        mode = qvs[1]
        modeItemId = qvs[2].value

        ''' Check the quality of the tags to make sure we can trust their values '''
        if str(currentValue.quality) != 'Good': 
            errorMessage = "the %s quality is: %s" % (outputType, str(currentValue.quality)) 
            log.warnf("checkConfig failed for %s because %s. (tag: %s)", modeItemId, errorMessage, self.path)
            return False, errorMessage, modeItemId

        ''' The quality is good so not get the values in a convenient form '''
        currentValue = currentValue.value

        ''' Check the Mode '''
        if str(mode.quality) != 'Good':
            errorMessage = "the mode quality is: %s" % (str(mode.quality))
            log.warnf("checkConfig failed for %s because %s. (tag: %s)", modeItemId, errorMessage, self.path)
            return False, errorMessage, modeItemId
        
        mode = string.strip(mode.value)  

        log.trace("%s: %s=%s, mode:%s" % (self.path, outputType, str(currentValue), mode))

        ''' For outputs check that the mode is MANUAL - no other test is required '''
        if string.upper(outputType) in ["OP", "OUTPUT"]:
            if string.upper(mode) not in [ 'MAN', 'MANUAL' ]:
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
            confirmTagPath = tagRoot + '/value'
        elif string.upper(valueType) in ["SP", "SETPOINT"]:
            tagRoot = self.path + '/sp'
            targetTag = self.spTag
            valueType = 'op'
            confirmTagPath = self.opTag.path + "/value"
        elif string.upper(valueType) in ["MODE"]:
            tagRoot = self.path + '/mode'
            targetTag = self.modeTag
            valueType = 'mode'
            confirmTagPath = tagRoot + "/value"
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
        
        ''' Set the permissive '''
        confirmed, errorMessage = self.setPermissive()
        if not(confirmed):
            return confirmed, errorMessage
        
        ''' Write the value to the OPC tag.  WriteDatum ALWAYS does a write confirmation.  The gateway is going to confirm 
        the write so this needs to just wait around for the answer. '''

        log.tracef("Writing %s to %s", str(val), tagRoot)
        system.tag.write(self.path + "/writeStatus", "Writing %s to %s" % (str(val), tagRoot))       
        confirmed, errorMessage = targetTag.writeDatum(val, valueType, confirmTagPath)
        
        ''' Return the permissive to its original value.  Don't let the success or failure of this override the result of the overall write. '''
        self.restorePermissive()

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
        
        ''' Set the permissive '''
        confirmed, errorMessage = self.setPermissive()
        if not(confirmed):
            return confirmed, errorMessage
        
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
        
        ''' Return the permissive to its original value.  Don't let the success or failure of this override the result of the overall write. '''
        self.restorePermissive()
        
        return confirmed, errorMessage