'''
Copyright 2014 ILS Automation

Either a float or text output to OPC.

Created on Jul 9, 2014
@author: phassler
'''
import ils.io.basicio as basicio
import string
import system.tag as systemtag
import time

class OPCOutput(basicio.BasicIO):
    def __init__(self,path):
        basicio.BasicIO.__init__(self,path)
        
    # Check some basic things about this OPC tag to determine if a write is likely to succeed!
    def checkConfig(self):
        # Check that the tag exists
        tagExists, reason = basicio.BasicIO.checkConfig(self)
        # TODO: Check if there is an item ID and an OPC server
                                               
        return tagExists, reason
 
    
 
    # Implement a simple write check.  We know the value that we tried to write, read the tag for a
    # reasonable amount of time.  As soon as we read the value back we are done.  Figuring out the
    # amount of time to wait is the tricky part.  In a simulated environment, as soon as the scan
    # class ran we read the value back, so the amount of time to wait was the scan class.  I don't
    # know if we will be able to do a device read, i.e., send the value all the way down to the
    # device and read it back.  If we can do that, then the time may be longer.
    def checkWrite(self, val):  
        print "Confirming the write..."
 
        for i in range(0,13):
            qv = systemtag.read(self.path + "/tag")
            print "%s Quality: comparing %f-%s to %f" % (self.path, qv.value, qv.quality, val)                                 
            if qv.value == val and string.upper(str(qv.quality)) == 'GOOD':
                return True, ""
 
                # TODO - This is hard coded!
                time.sleep(5)
                i=i+1
                               
        return False, "Value was not confirmed"
    
    
    
    
    # Write without confirmation.
    # Assume the UDT structure of an OPC Output
    def writeDatum(self):
        print "OPCOutput.writing ", self.path
                               
        systemtag.write(self.path + "/WriteConfirmed", False)
                               
        status,reason = self.checkConfig(self.path + "/Tag")
        if status == False :              
            systemtag.write(self.path + "/WriteStatus", "Failure")
            systemtag.write(self.path + "/WriteMessage", reason)
            return status,reason
 
        # Update the status to "Writing"
        systemtag.write(self.path + "/WriteStatus", "Writing")
 
        # Get the value to be read - this must be there BEFORE the command is set
        val = systemtag.read(self.path + "/WriteVal").value
 
        # Write the value to the OPC tag
        status = systemtag.write(self.path + "/Tag", val)
        print "OPCOutput.read status: ", status
                               
        status, msg = self.checkWrite(self.path, val)
        print "Confirmed: ", self.path, status, msg
        if status:
            systemtag.write(self.path + "/WriteStatus", "Success")
        else:
            systemtag.write(self.path + "/WriteStatus", "Failure")
            systemtag.write(self.path + "/WriteMessage", msg)
 
        return status, msg
 
 