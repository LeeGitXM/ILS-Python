#  Copyright 2014 ILS Automation
#
def getClassName():
    return "SubDiagnosis"

# A SubDiagnosis is a pass-thru. Its purpose is to
# facilitate migration.
#
from ils.block import basicblock


class SubDiagnosis(basicblock.BasicBlock):
    def __init__(self):
        basicblock.BasicBlock.__init__(self)
        self.initialize()
    
    # Set attributes custom to this class
    def initialize(self):
        self.className = 'emc.block.subdiagnosis.SubDiagnosis'
        self.properties['Label'] = {'value':'SubDiagnosis','editable':'True'}

    
        self.inports = [{'name':'in','type':'truthvalue'}]
        self.outports= [{'name':'out','type':'text'}]
        
    # Return a dictionary describing how to draw an icon
    # in the palette and how to create a view from it.
    def getPrototype(self):
        proto = {}
        proto['iconPath']= "Block/icons/palette/sub_diagnosis.png"
        proto['label']   = "SubDiagnosis"
        proto['tooltip']        = "Conclude a diagnosis based on input"
        proto['tabName']        = 'Analysis'
        proto['viewBackgroundColor'] = '0xFCFEFE'
        proto['viewLabel']      = "Sub\nDiagnosis"
        proto['blockClass']     = self.getClassName()
        proto['blockStyle']     = 'square'
        proto['viewHeight']     = 80
        proto['inports']        = self.getInputPorts()
        proto['outports']       = self.getOutputPorts()
        proto['viewWidth']      = 100
        return proto
            
    # Called when a value has arrived on one of our input ports
    # It is our diagnosis. Set the property then evaluate.
    def acceptValue(self,value,quality,port):
        diagnosis = self.properties.get('Diagnosis',{})
        text = str(value).lower()
        if text == 'true':
            msg = "Fix it"
            self.postValue('send','inhibit','good')
            self.postValue('send','reset','good')
        else:
            msg = "Leave things alone"
            
        diagnosis['value'] = msg
        print "SubDiagnosis.acceptValue: ",msg
        self.postValue('out',msg,'good')