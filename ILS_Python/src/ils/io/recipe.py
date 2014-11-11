'''
 Copyright 2014 ILS Automation
 
 Abstract base class for RecipeData
 encapsulates the root path of the UDT
 
 Created on Jul 9, 2014

@author: phassler
'''
# NOTE: Subclasses must be added to __init__.py 
#       for automatic import.
import system
import time
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.io")

class Recipe():

    # Path is the root tag path of the UDT which this object encapsulates
    path = None
    
    def __init__(self,tagPath):
        self.initialize(tagPath)
        
    # Set any default properties.
    # For this abstract class there aren't many (yet).
    def initialize(self,tagPath):    
        self.path = str(tagPath)
    
    # Helper method that confirms that a write has completed. 
    def writeConfirm(self, tagPath, command, val):
        log.trace("Entering Recipe.confirmWrite(): %s - %s - %s" % (tagPath, command, str(val)))
 
        # Record the current command being executed.
        system.tag.write(tagPath + '/command', command)
                               
        # wait until the tag is confirmed
        log.trace("Waiting for the write to be confirmed...")
                               
        for i in range(0,12):
            status = system.tag.read(tagPath + "/writeStatus").value
            log.trace("  confirm status for %s: %s" % (self.path, status))
                                                                               
            if status == "Failure":
                return False,"Read failure on confirm attempt"
            elif  status == "Success" :
                return True,"" 
                            
            time.sleep(5)
            i = i+1                    
        
        return False,"Write not confirmed"   
    
    # Basic method does nothing
    def writeRecipeDetail(self,command):
        pass
