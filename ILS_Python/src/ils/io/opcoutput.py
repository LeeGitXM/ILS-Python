'''
Copyright 2014 ILS Automation

Either a float or text output to OPC.

Created on Jul 9, 2014
@author: phassler
'''
import ils
import ils.io
import ils.io.opctag as opctag
import system, string

log = system.util.getLogger("com.ils.io")


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