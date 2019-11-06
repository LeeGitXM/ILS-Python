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
        self.className = 'ils.block.subdiagnosis.SubDiagnosis'
        self.properties['Label'] = {'value':'SubDiagnosis','editable':'True'}
        self.properties['TagPath'] = { 'value':'','binding':'','bindingType':'TAG_WRITE','editable':'True'}
        self.inports = [{'name':'in','type':'truthvalue'}]
        self.outports= [{'name':'out','type':'truthvalue'}]
        
    # Return a dictionary describing how to draw an icon
    # in the palette and how to create a view from it.
    def getPrototype(self):
        proto = {}
        proto['iconPath']= "Block/icons/palette/sub_diagnosis.png"
        proto['label']   = "SubDiagnosis"
        proto['tooltip']        = "Conclude an action based on input"
        proto['tabName']        = 'Conclusion'
        proto['viewBackgroundColor'] = '0xFCFEFE'
        proto['viewLabel']      = "Sub\nDiagnosis"
        proto['blockClass']     = self.getClassName()
        proto['blockStyle']     = 'square'
        proto['viewFontSize']   = 14
        proto['viewHeight']     = 80
        proto['inports']        = self.getInputPorts()
        proto['outports']       = self.getOutputPorts()
        proto['viewWidth']      = 100
        return proto
            
    # Called when a new value has arrived on one of our input ports
    # For now we record it to a tag and  pass it through to the output
    def acceptValue(self,port,value,quality,time):
        if not self.state == str(value):
            print "Accepting a new value <%s> for an sub-diagnosis block..." % (str(value))
            self.state = str(value)
            # Write to the tag, if it exists
            prop = self.properties['TagPath']
            path = prop['binding']
            #print "SubDiagnosis:",property
            if len(path)>0:
                self.handler.updateTag(self.parentuuid,path,str(value),quality,time)
            
        # Pass the input through to the output
        self.value = value
        self.quality=quality
        self.time = time
        self.postValue('out',value,quality,time)
        
    # Trigger property and connection notifications on the block
    def notifyOfStatus(self):
        self.handler.sendConnectionNotification(self.uuid, 'out', self.state,'good',0)
        
    # Propagate the most recent state of the block. 
    def propagate(self):
        if self.state <> None:
            self.postValue('out',str(self.state),self.quality,self.time)