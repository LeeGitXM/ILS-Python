'''
Copyright 2014 ILS Automation

Either a float or text output to OPC.

Created on Jul 9, 2014
@author: phassler
'''
import ils
import ils.io
import ils.io.opctag as opctag
import system, string, time

from ils.log import getLogger
log =getLogger(__name__)


class OPCOutput(opctag.OPCTag):
    def __init__(self,path):
        opctag.OPCTag.__init__(self,path)
        
    def checkConfig(self):
        ''' Check some basic things about this OPC tag to determine if a write is likely to succeed '''
        log.tracef("In OPCOutput.checkConfig()...")
        
        ''' Check that the tag exists ''' 
        tagExists, reason = opctag.OPCTag.checkConfig(self)
        
        # TODO: Check if there is an item ID and an OPC server
                                               
        return tagExists, reason
 
    def confirmControllerMode(self, newVal, testForZero, checkPathToValve, outputType):
        ''' This check doesn't make sense for a simple OPC tag, always return True.  '''
        success = True
        errorMessage = ""
        itemId = ""
        return success, errorMessage, itemId
 
    def reset(self):
        ''' Reset the UDT in preparation for a write '''
        status = True
        msg = ""
        system.tag.write(self.path + '/command', '')
        system.tag.write(self.path + '/badValue', False)
        system.tag.write(self.path + '/writeConfirmed', False)
        system.tag.write(self.path + '/writeErrorMessage', '')
        system.tag.write(self.path + '/writeStatus', 'Reset')
        return status, msg
 
    def confirmWrite(self, val, confirmTagPath=""):  
        ''' Implement a simple write confirmation.  Use the standard utility routine to perform the check. '''
        
        if confirmTagPath == "":
            confirmTagPath = self.path
            
        log.tracef("%s - Confirming the write of <%s> to %s...", __name__, str(val), confirmTagPath)
 
        from ils.io.util import confirmWrite as confirmWriteUtil
        system.tag.write(self.path + '/writeStatus', 'Confirming')
        confirmation, errorMessage = confirmWriteUtil(confirmTagPath, val)
        return confirmation, errorMessage
   
    def writeDatum(self, val, valueType="", confirmTagPath=""):
        ''' Write with confirmation. Assume the UDT structure of an OPC Output  '''
        
        '''
        I added the 3rd argument, which is optional and providea a default value of "", to support the case with digital controllers 
        where we write to the SP tag, which is configured with the .GOP item id, but we confirm from the OP tag, which is configured
        with the .OP item id.
        '''
        log.tracef("%s.writeDatum() - Writing <%s>, <%s> to %s, an OPCOutput", __name__, str(val), str(valueType), self.path)
        
        if confirmTagPath == "":
            confirmTagPath = self.path + "/value"

        if val == None or string.upper(str(val)) == 'NAN':
            val = float("NaN")

        system.tag.write(self.path + "/writeConfirmed", False)
        system.tag.write(self.path + "/writeStatus", "")
        system.tag.write(self.path + "/writeErrorMessage", "")
                               
        status,reason = self.checkConfig()
        if status == False :              
            system.tag.write(self.path + "/writeStatus", "Failure")
            system.tag.write(self.path + "/writeErrorMessage", reason)
            log.warnf("%s - Aborting write to %s, checkConfig failed due to: %s", __name__, self.path, reason)
            return status,reason
 
        ''' Update the status to "Writing" '''
        system.tag.write(self.path + "/writeStatus", "Writing Value")
 
        ''' Write the value to the OPC tag '''
        log.tracef("%s - Writing value <%s> to %s/value", __name__, str(val), self.path)
        status = system.tag.write(self.path + "/value", val)
        log.tracef("%s - Write status: %s", __name__, status)
                               
        status, msg = self.confirmWrite(val, confirmTagPath)
 
        if status:
            log.tracef("%s - Confirmed: %s - %s - %s", __name__, self.path, status, msg)
            system.tag.write(self.path + "/writeStatus", "Success")
            system.tag.write(self.path + "/writeConfirmed", True)
        else:
            log.errorf("%s - Failed to confirm write of <%s> to %s because %s", __name__, str(val), self.path, msg)
            system.tag.write(self.path + "/writeStatus", "Failure")
            system.tag.write(self.path + "/writeErrorMessage", msg)
 
        return status, msg

    def writeRamp(self, val, valType, rampTime, updateFrequency, writeConfirm):
        '''
        This method makes sequential writes to ramp the value of an output.  
        There is no native output ramping capability in the DCS for ramping an output and this method fills the gap.    
        The ramp is executed by writing sequentially based on a linear ramp.  
        The ramp time is in minutes.. 
        '''   
        success = True
        errorMessage = ""
        log.tracef("In %s.writeRamp() Writing %s for OPC output %s", __name__, valType, self.path)

        if val == None or rampTime == None or writeConfirm == None or valType == None or updateFrequency == None:
            log.errorf("ERROR writing ramp for OPC output: %s - One or more of the required arguments is missing val=%s rampTime=%s writeConfirm=%s valType=%s updateFreq=%s" % (self.path,val,rampTime,writeConfirm,valType,updateFrequency))
            return False, "One or more of the required arguments is missing"
        
        ''' Check the basic configuration of the tag '''        
        status,reason = self.checkConfig()
        if status == False :              
            system.tag.write(self.path + "/writeStatus", "Failure")
            system.tag.write(self.path + "/writeErrorMessage", reason)
            log.warnf("%s - Aborting write to %s, checkConfig failed due to: %s", __name__, self.path, reason)
            return status,reason

        ''' reset the UDT '''
        self.reset()
        
        ''' Update the status to "Writing" '''
        system.tag.write(self.path + "/writeStatus", "Writing Value")
        
        ''' Read the starting point for the ramp which is the current value '''
        startValue = system.tag.read(self.path + '/value')
        if str(startValue.quality) != 'Good':
            errorMessage = "ERROR: OPC Output <%s> - ramp aborted due to inability to read the starting value!" % (self.path)
            log.error(errorMessage)
            return False, errorMessage

        startValue = startValue.value

        baseTxt = "Ramping <%s> from %s to %s over %s minutes" % (self.path, str(startValue), str(val), str(rampTime))
        log.infof(baseTxt)
        system.tag.write(self.path + "/writeStatus", baseTxt)

        rampTimeSeconds = float(rampTime) * 60.0

        from ils.common.util import equationOfLine
        m, b = equationOfLine(0.0, startValue, rampTimeSeconds, val)
        startTime = system.date.now()
        deltaSeconds = system.date.secondsBetween(startTime, system.date.now())
        
        while (deltaSeconds < rampTimeSeconds):
            from ils.common.util import calculateYFromEquationOfLine
            aVal = calculateYFromEquationOfLine(deltaSeconds, m, b)
            
            log.tracef("OPC Output <%s> ramping to %s (elapsed time: %s)", self.path, str(aVal), str(deltaSeconds))
            
            status = system.tag.write(self.path + "/value", aVal)
            txt = "%s (%.2f at %s)" % (baseTxt, aVal, str(deltaSeconds))
            system.tag.write(self.path + "/writeStatus", txt)
 
            ''' Time in seconds '''
            time.sleep(updateFrequency)
            deltaSeconds = system.date.secondsBetween(startTime, system.date.now())
        
        ''' Write the final point and confirm this one '''
        status = system.tag.write(self.path + "/value", val)
        print "Final value status: ", status

        log.infof("%s - <%s> done ramping!", __name__, self.path)
        return success, errorMessage

    def writeWithNoCheck(self, val, valueType=""):
        ''' Write with NO confirmation.  Assume the UDT structure of an OPC Output '''
        if val == None or string.upper(str(val)) == 'NAN':
            val = float("NaN")

        log.tracef("%s.writeWithNoCheck() - Writing <%s> to %s, an OPCOutput with no confirmation", __name__, str(val), self.path)

        system.tag.write(self.path + "/writeConfirmed", False)
        system.tag.write(self.path + "/writeStatus", "")
        system.tag.write(self.path + "/writeErrorMessage", "")
                               
        status,reason = self.checkConfig()

        if status == False :              
            system.tag.write(self.path + "/writeStatus", "Failure")
            system.tag.write(self.path + "/writeErrorMessage", reason)
            log.warnf("%s - Aborting write to %s, checkConfig failed due to: %s", __name__, self.path, reason)
            return status,reason
 
        ''' Update the status to "Writing" '''
        system.tag.write(self.path + "/writeStatus", "Writing Value")
 
        ''' Write the value to the OPC tag '''
        log.tracef("%s - Writing value <%s> to %s/value", __name__, str(val), self.path)
        status = system.tag.write(self.path + "/value", val)
        log.tracef("%s - Write status: %s", __name__, status)
                               
        if status == 0:
            success = False
            errorMessage = "Write failed immediately"
            system.tag.write(self.path + "/writeStatus", "Failure")
        else:
            success = True
            errorMessage = ""
            system.tag.write(self.path + "/writeStatus", "Success")
            
        log.tracef("%s - Write Status: %s - %s - %s", __name__, self.path, str(success), errorMessage)
 
        return success, errorMessage