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
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
from ils.io.util import getProviderFromTagpath
log = LogUtil.getLogger("com.ils.io")

class OPCTag():

    # Path is the root tag path of the UDT which this object encapsulates
    path = None
    
    def __init__(self,tagPath):
        self.initialize(tagPath)
        
    # Set any default properties.
    # For this abstract class there aren't many (yet).
    def initialize(self,tagPath):    
        print "in OPCTag.initialize() The tagPath is ", tagPath
        self.path = str(tagPath)
        
    # Check for the existence of the tag
    def checkConfig(self):
        # Check that the tag exists
        reason = ""
        tagExists = system.tag.exists(self.path)
        if not(tagExists):
            reason = "Tag %s does not exist!" % self.path
            log.error(reason)
            return False, reason
 
        provider = getProviderFromTagpath(self.path)
        recipeWriteEnabled = system.tag.read("[" + provider + "]/Configuration/RecipeToolkit/recipeWriteEnabled").value
        globalWriteEnabled = system.tag.read("[" + provider + "]/Configuration/Common/writeEnabled").value
        writeEnabled = recipeWriteEnabled and globalWriteEnabled
        print "The combined write enabled status is: ", writeEnabled
        
        if not(writeEnabled):
            log.info('Write bypassed for %s because writes are inhibited!' % (self.path))
            return False, 'Writing is currently inhibited'
        # TODO: Check if there is an item ID and an OPC server
                                               
        return True, ""
    
    # This basic class doesn't support this method
    def confirmWrite(self,command, val):
        return True,""
    
    # The default implementation clears the command
    # After doing nothing    
    def writeDatum(self):
        commandPath = self.path+"/command"
        system.tag.write(commandPath,"")