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
import system.tag as systemtag
class BasicIO():

    # Path is the root tag path of the UDT which this object encapsulates
    path = None
    
    def __init__(self,tagPath):
        self.initialize(tagPath)
        
    # Set any default properties.
    # For this abstract class there aren't many (yet).
    def initialize(self,tagPath):    
        self.path = str(tagPath)
        
    # Check for the existence of the tag
    def checkConfig(self):
        # Check that the tag exists
        reason = ""
        tagExists = systemtag.exists(self.path)
        if not(tagExists):
            reason = "Tag %s does not exist!" % self.path
            print reason
 
        # TODO: Check if there is an item ID and an OPC server
                                               
        return tagExists,reason
    
    # Do nothing
    def checkWrite(self, val):
        return True,""
    
    def confirmWrite(self,command, val):
        return True,""
    
    # The default implementation clears the command
    # After doing nothing    
    def writeDatum(self):
        commandPath = self.path+"/command"
        systemtag.write(commandPath,"")