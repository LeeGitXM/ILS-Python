#  Copyright 2014 ILS Automation
#
def getClassName():
    return "Action"

# Implement a block that can execute custom functions. These
# functions are Python modules.
from ils.block import basicblock


class Action(basicblock.BasicBlock):
    def __init__(self):
        basicblock.BasicBlock.__init__(self)
        self.initialize()
        
    # Set attributes custom to this class
    def initialize(self):
        self.className = 'emc.block.action.Action'
        self.properties['Script'] = {'value':'','editable':'True'}
        self.inports = [{'name':'in','type':'any'}]
        self.outports= [{'name':'out','type':'data'}]
        
    # Return a dictionary describing how to draw an icon
    # in the palette and how to create a view from it.
    def getPrototype(self):
        proto = {}
        proto['iconPath']= "Block/icons/palette/action.png"
        proto['label']   = "Action"
        proto['tooltip']        = "Execute a user-defined script"
        proto['tabName']        = 'Misc'
        proto['viewBackgroundColor'] = '0xF0F0F0'
        proto['viewIcon']      = "Block/icons/embedded/gear.png"
        proto['blockClass']     = self.getClassName()
        proto['blockStyle']     = 'square'
        proto['viewHeight']     = 70
        proto['viewWidth']      = 70
        proto['inports']        = self.getInputPorts()
        proto['outports']       = self.getOutputPorts()
        proto['receiveEnabled']  = 'false'
        proto['transmitEnabled'] = 'false'
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
        print "Function.acceptValue: ",msg
        self.postValue('out',msg,'good')