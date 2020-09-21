#  Copyright 2014 ILS Automation
#
import system, time

def getClassName():
    return "FinalDiagnosis"

# A FinalDiagnosis block receives a truth-value from an SQC
# or other block upstream and deduces the reason for the issue.
#
from ils.block import basicblock
#import ils.diagToolkit.finalDiagnosis as fd

callback = "fd.evaluate"

class FinalDiagnosis(basicblock.BasicBlock):
    def __init__(self):
        basicblock.BasicBlock.__init__(self)
        self.initialize()
        self.state = "UNKNOWN"
        self.handler.setAlerterClass(self.getClassName())
    
    # Set attributes custom to this class
    def initialize(self):
        self.className = 'ils.block.finaldiagnosis.FinalDiagnosis'
#        self.properties['Label'] = {'value':'FinalDiagnosis','editable':True}
        
        self.inports = [{'name':'in','type':'TRUTHVALUE','allowMultiple':False}]
        self.outports= [{'name':'out','type':'TRUTHVALUE'}]
    
        
    # Return a dictionary describing how to draw an icon
    # in the palette and how to create a view from it.
    def getPrototype(self):
        proto = {}
        proto['auxData'] = True
        proto['iconPath']= "Block/icons/palette/final_diagnosis.png"
        proto['label']   = "FinDiagnosis"
        proto['tooltip']        = "Conclude a diagnosis based on input"
        proto['tabName']        = 'Conclusion'
        proto['viewBackgroundColor'] = '0xFCFEFE'
        proto['viewLabel']      = "Final\nDiagnosis"
        proto['blockClass']     = self.getClassName()
        proto['blockStyle']     = 'square'
        proto['viewFontSize']       = 14
        proto['viewHeight']     = 80
        proto['inports']        = self.getInputPorts()
        proto['outports']       = self.getOutputPorts()
        proto['viewWidth']      = 100
        proto['transmitEnabled']= True
        return proto
            
    # Called when a value has arrived on one of our input ports
    # It is our diagnosis. Set the property then evaluate.
    def acceptValue(self,port,value,quality,ts):
        newState = str(value).upper()
        if newState == self.state:
            return
        
        self.state = newState
        
        # I'm not really using this, but I'm printing it up front just to make sure this works
        projectName = system.util.getProjectName()
        print "FinalDiagnosis.acceptValue: %s (project: %s)" % (self.state, projectName)

        if self.state != "UNKNOWN":
            print "Clearing the watermark"
            system.ils.blt.diagram.clearWatermark(self.parentuuid)
        
        handler = self.handler
        
        # On startup, it is possible for a block to get a value before
        # all resources (like the parent application) have been loaded. 
        if handler.getApplication(self.parentuuid)==None or handler.getFamily(self.parentuuid)==None:
            print "FinalDiagnosis.acceptValue: Parent application or family not loaded yet, ignoring state change"
            self.state = "UNKNOWN"
            return

        database = handler.getDefaultDatabase(self.parentuuid)
        provider = handler.getDefaultTagProvider(self.parentuuid)
        
        print "Using database: %s and tag provider: %s " % (database, provider)
        
        applicationName = handler.getApplication(self.parentuuid).getName()
        familyName = handler.getFamily(self.parentuuid).getName()
        print "Application: %s\nFamily: %s" % (applicationName, familyName)
        
        finalDiagnosis = handler.getBlock(self.parentuuid, self.uuid)
        finalDiagnosisName = finalDiagnosis.getName()
        print "Final Diagnosis: %s" % (finalDiagnosisName)        

        if self.state == "TRUE":
            print "The diagnosis just became TRUE"
            def work(fd=self,applicationName=applicationName,familyName=familyName,finalDiagnosisName=finalDiagnosisName,database=database,provider=provider):
                # Notify inhibit blocks to temporarily halt updates to SQC
                # handler.sendTimestampedSignal(self.parentuuid, "inhibit", "", "",time)
                from ils.diagToolkit.finalDiagnosis import postDiagnosisEntry
                postDiagnosisEntry(applicationName, familyName, finalDiagnosisName, fd.uuid, fd.parentuuid, database, provider)
            system.util.invokeAsynchronous(work)
        else:
            print "The diagnosis just became FALSE"
            from ils.diagToolkit.finalDiagnosis import clearDiagnosisEntry
            clearDiagnosisEntry(applicationName, familyName, finalDiagnosisName, database, provider)

        # Pass the input through to the output
        self.value = value
        self.quality=quality
        self.time = ts
        self.postValue('out',value,quality,ts)
        
        print "FinalDiagnosis.acceptValue: COMPLETE"
    
    # Trigger property and connection notifications on the block
    def notifyOfStatus(self):
        self.handler.sendConnectionNotification(self.uuid, 'out', self.state,'good',0)
        
    # Propagate the most recent state of the block. 
    def propagate(self):
        if self.state <> "UNSET":
            self.postValue('out',str(self.state),self.quality,self.time)