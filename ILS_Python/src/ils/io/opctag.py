'''
 Copyright 2014 ILS Automation
 
 Abstract base class for output IO. The output
 encapsulates the tagPath
 
 Created on Jul 9, 2014

@author: phassler
'''
#  Copyright 2014 ILS Automation
#
# WARNING: basic imports (like sys) fail here, but succeed in subclasses.
#          Could it be from the import * in util.py? 
# NOTE: Subclasses must be added to __init__.py.
import system, string
from ils.io.util import getProviderFromTagPath
log = system.util.getLogger("com.ils.io")

class OPCTag():

    # Path is the root tag path of the UDT which this object encapsulates
    path = None
    
    # Set any default properties.
    # For this abstract class there aren't many (yet).
    def __init__(self,path):
        self.path = str(path)
        
        
    # Check for the existence of the tag and the global write flag
    def checkConfig(self):
        log.trace("In OPCTag.checkConfig()...")
        
        from ils.io.util import checkConfig
        status, reason = checkConfig(self.path)
        if not(status):
            return status, reason
        
        # Read the value and check the quality.  I don't think that there is a way that an OPC tag can be bad.
        # If NaN causes the tag to appear bad then we will need to look at the specific reason
        val = system.tag.read(self.path + "/value")
        if val.quality.isGood() or str(val.quality) in ['Tag Evaluation Error', 'foo']:
            return True, ""
            
        return False, "Tag is bad: %s" % (val.quality)
    
    # This check doesn't make sense for a simple OPC tag, always return True. 
    def confirmControllerMode(self, newVal, testForZero, checkPathToValve, outputType):
        success = True
        errorMessage = ""
        return success, errorMessage
    
    # This basic class doesn't support this method
    # Implement a simple write confirmation.  Use the standard utility routine to perform the check.
    def confirmWrite(self, val):  
        log.trace("Confirming the write of <%s> to %s..." % (str(val), self.path))
 
        from ils.io.util import confirmWrite as confirmWriteUtil
        confirmation, errorMessage = confirmWriteUtil(self.path + "/value", val)
        return confirmation, errorMessage
    
    # This is a very simple write    
    def writeDatum(self, val, valueType=""):

        if val == None or string.upper(str(val)) == 'NAN':
            val = float("NaN")
                               
        status,reason = self.checkConfig()
        if status == False :              
            log.warn("* Aborting write to %s, checkConfig failed due to: %s" % (self.path, reason))
            return status,reason
 
        # Write the value to the OPC tag
        log.trace("  Writing value <%s> to %s/value" % (str(val), self.path))
        status = system.tag.write(self.path + "/value", val)
        log.trace("  Write status: %s" % (status))
                               
        status, msg = self.confirmWrite(val)
 
        if status:
            log.trace("Confirmed: %s - %s - %s" % (self.path, status, msg))
        else:
            log.error("Failed to confirm write of <%s> to %s because %s" % (str(val), self.path, msg))
 
        return status, msg

        