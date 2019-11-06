#  Copyright 2014 ILS Automation
#
def getClassName():
    return "Arithmetic"

# Implement a block that can execute custom functions. These
# functions are Python modules.
#
from ils.block import basicblock  
from com.inductiveautomation.ignition.common.util import LogUtil

import org.apache.commons.math3.analysis.function.Abs as Abs
import org.apache.commons.math3.analysis.function.Ceil as Ceiling
import org.apache.commons.math3.analysis.function.Cos as Cosine
import org.apache.commons.math3.analysis.function.Floor as Floor
import org.apache.commons.math3.analysis.function.Sin as Sine
import org.apache.commons.math3.analysis.function.Tan as Tangent
import org.apache.commons.math3.util.Precision as Precision

import java.lang.Double as Double   

log = LogUtil.getLogger("com.ils.block")

class Arithmetic(basicblock.BasicBlock):
    def __init__(self):
        basicblock.BasicBlock.__init__(self)
        self.initialize()
        
    # Set attributes custom to this class
    def initialize(self):
        self.className = 'ils.block.arithmetic.Arithmetic'
        self.properties['Function'] = {'value':'','editable':'True','bindingType':'OPTION',
                                       'binding':'ABS,CEILING,COSINE,FLOOR,SINE,TANGENT,TO_RADIAN'}
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
    # Compute the result, then propagate on the output.
    def acceptValue(self,port,invalue,quality,time):
        function = self.properties.get('Function',{}).get("value","")
        if len(invalue) == 0:
            return
        
        dbl = Double(str(invalue))
        value = dbl.doubleValue()      # Default behavior is a pass-through
        #value = float(invalue)
        if len(function)>0:
            if function == 'ABS':
                absolute = Abs()
                value = absolute.value(value)
            elif function == 'CEILING':
                ceiling = Ceiling()
                value = ceiling.value(value)
            elif function == 'COSINE':
                cosine = Cosine()
                value = cosine.value(value)
            elif function == 'FLOOR':
                floor = Floor()
                value = floor.value(value)
            elif function == 'ROUND':
                value = Precision.round(value,0)   # Static function, this is OK
            elif function == 'SINE':
                sine = Sine()
                value = sine.value(value)
            elif function == 'TANGENT':
                tan = Tangent()
                value = tan.value(value)
            elif function == 'TO_RADIAN':
                value = 0.0174532925*value;
            
            log.tracef("Arithmetic.acceptValue: %s(%s) = %s",function,str(invalue),str(value))
            
            self.value = value
            self.quality=quality
            self.time = time
            self.state = "TRUE"
            self.postValue('out',str(value),'good',time)
            
    # The output connection of this block is a value, not block status
    def notifyOfStatus(self):
        pass
    
    # Propagate the most recent state of the block. 
    def propagate(self):
        if self.value<>None:
            self.postValue('out',str(self.value),self.quality,self.time)