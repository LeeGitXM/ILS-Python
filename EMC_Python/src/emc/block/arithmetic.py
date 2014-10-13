#  Copyright 2014 ILS Automation
#
def getClassName():
    return "Arithmetic"
# Implement a block that can execute custom functions. These
# functions are Python modules.
#
from ils.block import basicblock    


class Arithmetic(basicblock.BasicBlock):
    def __init__(self):
        basicblock.BasicBlock.__init__(self)
        self.initialize()
        
    # Set attributes custom to this class
    def initialize(self):
        self.className = 'emc.block.arithmetic.Arithmetic'
        self.properties['Function'] = {'value':'','editable':'True'}
        self.inports = [{'name':'in','type':'data'}]
        self.outports= [{'name':'out','type':'data'}]
        
    # Return a dictionary describing how to draw an icon
    # in the palette and how to create a view from it.
    def getPrototype(self):
        proto = {}
        proto['iconPath']= "Block/icons/palette/function.png"
        proto['label']   = "Arithmetic"
        proto['tooltip']        = "Execute a user-defined function on the input"
        proto['tabName']        = 'Arithmetic'
        proto['viewBackgroundColor'] = '0xF0F0F0'
        proto['viewIcon']      = "Block/icons/embedded/fx.png"
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