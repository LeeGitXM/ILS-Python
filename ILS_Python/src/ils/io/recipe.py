'''
 Copyright 2014 ILS Automation
 
 Abstract base class for RecipeData
 encapsulates the root path of the UDT
 
 Created on Jul 9, 2014

@author: phassler
'''
# NOTE: Subclasses must be added to __init__.py 
#       for automatic import.
import system, time
from ils.io.util import writeTag

from ils.log import getLogger
log = getLogger(__name__)

class Recipe():

    # Path is the root tag path of the UDT which this object encapsulates
    path = None
    
    def __init__(self,tagPath):
        self.initialize(tagPath)
        
    # Set any default properties.
    # For this abstract class there aren't many (yet).
    def initialize(self,tagPath):    
        self.path = str(tagPath)
    
    # Pass the WRITEDATUM command along and then wait for a confirmation. 
    def writeDatum(self, tagPath, val):
        log.trace("Entering Recipe.writeDatum(): %s - %s" % (tagPath, str(val)))
 
        # Record the current command being executed.
#        writeTag(tagPath + '/command', 'WRITEDATUM')
#        writeWithNoCheck(tagPath, val)
        print "NEED TO FIGURE OUT A WRITE HERE"
                               
        # wait until the tag is confirmed
        log.trace("Waiting for the write to be confirmed...")
        from ils.io.util import waitForWriteConfirm
        confirmed, errorMessage = waitForWriteConfirm(tagPath)                 
        
        return confirmed, errorMessage   
    
    # Basic method does nothing
    def writeRecipeDetail(self,command):
        pass
