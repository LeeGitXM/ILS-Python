#  Copyright 2014 ILS Automation
#
def getClassName():
    return "FinalDiagnosis"

# A FinalDiagnosis block receives a truth-value from an SQC
# or other block upstream and deduces the reason for the issue.
#
from ils.block import basicblock
from ils.diagToolkit import finalDiagnosis

callback = "ils.diagToolkit.finalDiagnosis.evaluate()"

class FinalDiagnosis(basicblock.BasicBlock):
    def __init__(self):
        basicblock.BasicBlock.__init__(self)
        self.initialize()
    
    # Set attributes custom to this class
    def initialize(self):
        self.className = 'emc.block.finaldiagnosis.FinalDiagnosis'
        self.properties['CalculationMethod'] = {'value':'','editable':'True'}
        self.properties['Explanation'] = {'value':'','editable':'True'}
        self.properties['Label'] = {'value':'FinalDiagnosis','editable':'True'}
        self.properties['LogToDatabase'] = {'value':'False','editable':'True','type':'BOOLEAN'}
        self.properties['ManualMove'] = {'value':'False','editable':'True','type':'BOOLEAN'}
        self.properties['ManualMoveValue'] = {'value':'0.0','editable':'True','type':'DOUBLE'}
        self.properties['ManualTextRequired'] = {'value':'False','editable':'True','type':'BOOLEAN'}
        self.properties['Multiplier'] = {'value':'1.0','editable':'True','type':'DOUBLE'}
        self.properties['PostRecommendation'] = {'value':'False','editable':'True','type':'BOOLEAN'}
        self.properties['Priority'] = {'value':'1.0','editable':'True','type':'DOUBLE'}
        self.properties['Recommendation'] = {'value':'','editable':'True'}
        self.properties['RecommendationCallback'] = {'value':'','editable':'True'}
        # Value is seconds
        self.properties['RecommendationRefreshInterval'] = {'value':'10000000.','editable':'True','type':'DOUBLE'}
        self.properties['Targets'] = {'value':'','editable':'True','type':'LIST'}
        self.properties['TrapInsignificantConditions'] = {'value':'True','editable':'True','type':'BOOLEAN'}
    
        self.inports = [{'name':'in','type':'truthvalue'}]
        self.outports= [{'name':'out','type':'text'}]
        
    # Return a dictionary describing how to draw an icon
    # in the palette and how to create a view from it.
    def getPrototype(self):
        proto = {}
        proto['iconPath']= "Block/icons/palette/final_diagnosis.png"
        proto['label']   = "FinDiagnosis"
        proto['tooltip']        = "Conclude a diagnosis based on input"
        proto['tabName']        = 'Analysis'
        proto['viewBackgroundColor'] = '0xFCFEFE'
        proto['viewLabel']      = "Final Diagnosis"
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
        state = str(value).upper()
        print "FinalDiagnosis.acceptValue: ",state
        lcls = {}
        lcls['block'] = self
        lcls['state'] = state
        eval(callback,{},{})
        # Notifications on the signal link
        self.postValue('send','inhibit','good')
        self.postValue('send','reset','good')
        print "FinalDiagnosis.acceptValue: COMPLETE"
        self.postValue('out',state,'good')
        