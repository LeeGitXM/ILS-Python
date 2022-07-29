#  Copyright 2014 ILS Automation
#
import system
from ils.common.cast import toBit
from ils.common.database import toDateString

def getClassName():
    return "FinalDiagnosis"

# A FinalDiagnosis block receives a truth-value from an SQC
# or other block upstream and deduces the reason for the issue.
#
from ils.block import basicblock
from ils.log import getLogger

#import ils.diagToolkit.finalDiagnosis as fd

callback = "fd.evaluate"

class FinalDiagnosis(basicblock.BasicBlock):
    def __init__(self):
        basicblock.BasicBlock.__init__(self)
        self.initialize()
        self.state = "UNKNOWN"
        self.log = getLogger(__name__)
        self.log.infof("Initializing a FinalDiagnosis in project %s", self.project)
    
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
    def acceptValue(self, port, value, quality, timestamp):
        self.log.infof("In %s.acceptValue - value: %s", __name__, str(value))
        newState = str(value).upper()
        if newState == self.state:
            return
        
        handler = self.handler
        block = handler.getBlock(self.project, self.resource, self.uuid)
        blockName = block.getName()
        
        self.state = newState
        diagramPath = self.resource
        
        # I'm not really using this, but I'm printing it up front just to make sure this works
        self.log.infof("%s (project: %s, UUID: %s, block: %s, diagram: %s)", self.state, self.project, self.uuid, blockName, diagramPath)

        if self.state != "UNKNOWN":
            from ils.blt.api import clearWatermark
            clearWatermark(diagramPath) 
        
        # On startup, it is possible for a block to get a value before
        # all resources (like the parent application) have been loaded. 
#        if self.handler.getApplication(self.parentuuid)==None or self.handler.getFamily(self.parentuuid)==None:
#            print "FinalDiagnosis.acceptValue: Parent application or family not loaded yet, ignoring state change"
#            self.state = "UNKNOWN"
#            return

        database = self.handler.getDefaultDatabase(self.project, self.resource)
        provider = self.handler.getDefaultTagProvider(self.project, self.resource)
        
        print "Using database: %s and tag provider: %s " % (database, provider)
        
#        applicationName = self.handler.getApplication(self.project,self.resource).getName()
#        familyName = self.handler.getFamily(self.project,self.resource).getName()
#        print "Application: %s\nFamily: %s" % (applicationName, familyName)
        
        theFinalDiagnosis = self.handler.getBlock(self.project, self.resource, self.uuid)
        finalDiagnosisName = theFinalDiagnosis.getName()
        print "Final Diagnosis: %s" % (finalDiagnosisName)        

        if self.state == "TRUE":
            print "The diagnosis just became TRUE, posting a diagnosis entry..."
            from ils.diagToolkit.finalDiagnosis import postDiagnosisEntry
            postDiagnosisEntry(self.project, diagramPath, finalDiagnosisName, self.uuid, database, provider)
        else:
            print "The diagnosis just became FALSE, clearing existing diagnosis entries..."
            from ils.diagToolkit.finalDiagnosis import clearDiagnosisEntry
            clearDiagnosisEntry(self.project, diagramPath, finalDiagnosisName, database, provider)

        # Pass the input through to the output
        self.value = value
        self.quality=quality
        self.time = timestamp
        self.postValue('out', value, quality, timestamp)
        
        print "FinalDiagnosis.acceptValue: COMPLETE"
    
        # The base method leaves the aux data unchanged.
    
    # Trigger property and connection notifications on the block
    def notifyOfStatus(self):
        self.handler.sendConnectionNotification(self.uuid, 'out', self.state,'good',0)
        
    # Propagate the most recent state of the block. 
    def propagate(self):
        if self.state <> "UNSET":
            self.postValue('out',str(self.state),self.quality,self.time)
    
    def getAuxData(self, aux):
        '''
        NOTE: The UUID supplied is from the parent, a diagram. The database interactions
               are all based on a the block name which is  the data structure.
        
        The aux data structure is a Python list of three dictionaries. These are:
        properties, lists and maplists.
         
        Fill the aux structure with values from the database.
        '''
        self.log.infof("In finalDiagnosis.getAuxData() with nothing to do!")

    def setAuxData(self, data):
        '''
        Update / insert data in the Symbolic Ai database. 
        The goal is to synchronize the database with the configuration of the Final Diagnosis in Ignition, i.e., the serialized block.
        For now, this is called whenever the focus in the property editor is lost.  It should be called when the user selects File->Save
        in the Designer.
        '''
        self.log.infof("In finalDiagnosis.setAuxData() with nothing to do!")