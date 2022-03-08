#  Copyright 2014 ILS Automation
#

from ils.common.error import catchError
import string, system
from ils.log import getLogger
log =getLogger(__name__)

def getClassName():
    return "Action"

# Implement a block that can execute custom functions. These
# functions are Python modules in the project or global scope.
#
from ils.block import basicblock


class Action(basicblock.BasicBlock):
    def __init__(self):
        basicblock.BasicBlock.__init__(self)
        self.initialize()
        
    # Set attributes custom to this class.
    # Default the trigger to TRUE
    def initialize(self):
        self.className = 'ils.block.action.Action'
        self.properties['Script'] = {'value':'ils.actions.demo.act','editable':'True'}
        self.properties['Trigger'] = {'value':'TRUE','editable':'True','type':'TRUTHVALUE'}
        self.inports = [{'name':'in','type':'truthvalue'}]
        self.outports= [{'name':'out','type':'truthvalue'}]
        
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
    # If the value matches the trigger (case insensitive),
    # then evaluate the function. The output retains the 
    # timestamp of the input.
    def acceptValue(self,port,value,quality,time):
        handler = self.handler
        block = handler.getBlock(self.parentuuid, self.uuid)
        blockName = block.getName()
        
        log.infof("In %s.acceptValue() with %s", __name__, blockName)
        
        database = handler.getDefaultDatabase(self.parentuuid)
        provider = handler.getDefaultTagProvider(self.parentuuid)
        
        trigger = self.properties.get('Trigger',{}).get("value","").lower()
        text = str(value).lower()
        if text == trigger:
            log.infof("...processing a trigger...")
            self.state = "TRUE"
            function = self.properties.get('Script',{}).get("value","")
            log.infof("...calling function: <%s>", function)

            if len(function) > 0:
                log.tracef("...there is a function: <%s>", function)
                
                ''' If they specify shared or project scope, then we don't need to do this '''
                if not(string.find(function, "project") == 0 or string.find(function, "shared") == 0):
                    # The method contains a full python path, including the method name
                    log.tracef("...it is external...")
                    packName = self.packageFromFunctionPath(function)
                    funcName = self.functionFromFunctionPath(function)
                    log.tracef("   ...using External Python, the package is: <%s>.<%s>", packName, funcName)
                    exec("import %s" % (packName))
                    exec("from %s import %s" % (packName,funcName))
            
                eval(function)(blockName, self.uuid, self.parentuuid, provider, database)
#                project.test.diagToolkit.act_1(blockName, self.uuid, self.parentuuid, provider, database)
#                eval(function)(block)

        else:
            self.state = "FALSE"
            
        self.value = value
        self.quality=quality
        self.time = time
        self.postValue('out',value,quality,time)
        
    # Trigger property and connection notifications on the block
    def notifyOfStatus(self):
        self.handler.sendConnectionNotification(self.uuid, 'out', self.state,'good',0)  
        
    # Propagate the most recent state of the block. 
    def propagate(self):
        if self.value<>None:
            self.postValue('out',self.value,self.quality,self.time)