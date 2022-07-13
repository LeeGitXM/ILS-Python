'''
Created on Jul 9, 2014

@author: chuckc
'''
import ils.io.recipe as recipe
from ils.io.util import readTag
import system, string, time
import ils.io.opcoutput as opcoutput
import ils.io.opcconditionaloutput as opcconditionaloutput
from ils.log import getLogger
log = getLogger(__name__)

class RecipeDetail(recipe.Recipe):
    highLimitTag = None
    spTag = None
    lowLimitTag = None
    writeHighLimit = False
    writeLowLimit = False
    writeSp = False
    pythonClass = ""
    LATENCY_TIME = 5.0
    
    def __init__(self, path):
        recipe.Recipe.__init__(self, path)

        log.tracef("%s.__init__() Initializing the recipe detail object for %s", __name__, path)
        
        rootPath=self.path[0:self.path.rfind('/')+1]


    def writeRecipeDetail(self, newValue, newHighLimitValue, newLowLimitValue):
    
        log.infof("In RecipeDetail::writeRecipeDetail() with <%s>: %s - %s - %s", self.path, str(newValue), str(newHighLimitValue), str(newLowLimitValue))
        
        rootPath=self.path[0:self.path.rfind('/')+1]

        # start of what I moved from init
        
        tags = []
        for attr in ['highLimitTagName', 'lowLimitTagName','valueTagName']:
            tags.append(self.path + '/' + attr)
 
        vals = system.tag.readBlocking(tags)
 
        highLimitTagName = vals[0].value
        if highLimitTagName not in ["", "0"] and newHighLimitValue not in ["", None]:
            self.highLimitTag = opcoutput.OPCOutput(rootPath + highLimitTagName)
            self.writeHighLimit = True
            log.trace("  setting up to write the high limit")
        
        lowLimitTagName = vals[1].value
        if lowLimitTagName not in ["", "0"] and newLowLimitValue not in ["", None]:
            self.lowLimitTag = opcoutput.OPCOutput(rootPath + lowLimitTagName)
            self.writeLowLimit = True
            log.trace("  setting up to write the low limit")

        '''
        The limits that I am setting up above here are always opcOutputs.  The SP is generally a more
        complicated UDT.  At Vistalon, they are always OPC Conditional Outputs, but I'm not sure that will always be the case.
        So for the sp, the first thing I need to do is to read the Python class from the UDT so I can create the proper
        type of object here and then dispatch the method correctly
        '''
        spTagName = vals[2].value
        print "The SP tag name is: <%s>" % (spTagName)
        if spTagName not in ["", "0"] and newValue not in ["", None]:
            self.pythonClass = readTag(rootPath + spTagName + "/pythonClass").value
            
            if self.pythonClass == "OPCOutput":
                self.spTag = opcoutput.OPCOutput(rootPath + spTagName)
            elif self.pythonClass == "OPCConditionalOutput":
                self.spTag = opcconditionaloutput.OPCConditionalOutput(rootPath + spTagName)
            
            self.writeSp = True
            log.trace("  setting up to write the setpoint")
            
        # End of what I moved from init
 
        # Get the path to this tag, the other tags will be in the same folder
        rootPath=self.path[0:self.path.rfind('/')+1]

        if self.writeHighLimit:
            oldHighLimitValue = readTag(self.highLimitTag.path + '/value').value             
            log.trace("Changing High limit from %s to %s" % (str(oldHighLimitValue), str(newHighLimitValue)))

        if self.writeLowLimit:
            oldLowLimitValue = readTag(self.lowLimitTag.path + '/value').value 
            log.trace("Changing Low limit from %s to %s" % (str(oldLowLimitValue), str(newLowLimitValue)))

        if self.writeSp:
            oldValue = readTag(self.spTag.path + '/value').value
            log.trace("Changing Value from %s to %s" % (str(oldValue), str(newValue)))

        highLimitWritten = False
        lowLimitWritten = False

        # TODO - Should I bail as soon as one of the writes cannot be confirmed?
        status = True
        reason = ''
        
        # If moving the upper limit up then writ it before the value
        if self.writeHighLimit:
            if float(newHighLimitValue) > float(oldHighLimitValue):
                log.trace("** Writing the high limit: %s **" % (str(newHighLimitValue)))
                highLimitWritten = True
                confirmed, r = self.highLimitTag.writeDatum(newHighLimitValue)
                reason = reason + r
                status = status and confirmed
#                log.info("...dwelling after high limit write before SP write...")
#                time.sleep(self.LATENCY_TIME)

        # If moving the upper limit up then writ it before the value
        if self.writeLowLimit:
            if float(newLowLimitValue) < float(oldLowLimitValue):
                log.trace("** Writing the Low limit: %s **" % (str(newLowLimitValue)))
                lowLimitWritten = True
                confirmed, r = self.lowLimitTag.writeDatum(newLowLimitValue)
                reason = reason + r
                status = status and confirmed
#               log.info("...dwelling after low limit write before SP write...")
#               time.sleep(self.LATENCY_TIME)
 
        if self.writeSp:
            log.trace("** Writing the Value: %s **" % (str(newValue)))
            confirmed, r = self.spTag.writeDatum(newValue)
            reason = reason + r
            status = status and confirmed
                
        if self.writeHighLimit and not(highLimitWritten):
            log.trace("** Writing the high limit: %s **" % (str(newHighLimitValue)))
            confirmed, r = self.highLimitTag.writeDatum(newHighLimitValue)
            reason = reason + r
            status = status and confirmed
                
        if self.writeLowLimit and not(lowLimitWritten):
            log.trace("** Write the low limit: %s **" % (str(newLowLimitValue)))
            confirmed, r = self.lowLimitTag.writeDatum(newLowLimitValue)
            reason = reason + r
            status = status and confirmed
                
        log.info("Done writing recipe detail: %s - %s - %s" % (self.path, status, reason))
        return status, reason