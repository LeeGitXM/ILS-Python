#  Author: Craig Lovold - ILS Automation
#  Created on: 04/22/2020

from ils.common.error import catchError
from ils.log.LogRecorder import LogRecorder
log = LogRecorder(__name__)

def getClassName():
    return "Sample"

from ils.block import basicblock


class Sample(basicblock.BasicBlock):
    def __init__(self):
        basicblock.BasicBlock.__init__(self)
        self.initialize()
        
    # Set attributes custom to this class.
    def initialize(self):
        self.className = 'ils.user.block.sample.Sample'
        self.inports = [{'name':'in','type':'truthvalue'}]
        self.outports= [{'name':'out','type':'truthvalue'}]
        
    # Return a dictionary describing how to draw an icon
    # in the palette and how to create a view from it.
    #
    #
    def getPrototype(self):
        proto = {}
        proto['iconPath']= "Block/icons/palette/sample.png"
        proto['viewIcon']      = "Block/icons/embedded/sample.png"
        proto['label']   = "Sample"
        proto['tooltip']        = "Sample user created block"
        proto['tabName']        = 'Logic'
        proto['viewBackgroundColor'] = '0xF0F0F0'
        proto['blockClass']     = self.getClassName()
        proto['blockStyle']     = 'square'
        proto['viewHeight']     = 70
        proto['viewWidth']      = 70
        proto['inports']        = self.getInputPorts()
        proto['outports']       = self.getOutputPorts()
        proto['receiveEnabled']  = 'false'
        proto['transmitEnabled'] = 'false'
        return proto
            
    # 
    def acceptValue(self,port,value,quality,time):
        log.infof("In %s.acceptValue()", __name__)

        # the next lines just show accessing some available objects        
        handler = self.handler
        database = handler.getDefaultDatabase(self.parentuuid)
        provider = handler.getDefaultTagProvider(self.parentuuid)
        block = handler.getBlock(self.parentuuid, self.uuid)
        blockName = block.getName()
        

        
    # Trigger property and connection notifications on the block
    def notifyOfStatus(self):
        self.handler.sendConnectionNotification(self.uuid, 'out', self.state,'good',0)  
        
    # Propagate the most recent state of the block. 
    def propagate(self):
        if self.value<>None:
            self.postValue('out',self.value,self.quality,self.time)
