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
import system
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
    
    # This basic class doesn't support this method
    def confirmWrite(self,command, val):
        return True,""
    
    # The default implementation clears the command
    # After doing nothing    
    def writeDatum(self):
        commandPath = self.path+"/command"
        system.tag.write(commandPath,"")