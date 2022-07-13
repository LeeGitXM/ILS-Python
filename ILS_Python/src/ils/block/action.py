#  Copyright 2014 ILS Automation
#

from ils.common.error import catchError
import string, system

from ils.log import getLogger

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
        self.log = getLogger(__name__)
        
    # Set attributes custom to this class.
    # Default the trigger to TRUE
    def initialize(self):
        self.className = 'ils.block.action.Action'
        self.properties['Script'] = {'value':'ils.demo.diagToolkit.actions.defaultAction', 'editable':'True'}
        self.properties['Trigger'] = {'value':'TRUE', 'editable':'True', 'type':'TRUTHVALUE'}
        
        self.inports = [{'name':'in','type':'TRUTHVALUE','allowMultiple':False}]
        self.outports= [{'name':'out','type':'TRUTHVALUE'}]
        
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
    def acceptValue(self, port, value, quality, time):
        self.log.infof("In %s.acceptValue(), project: %s, resource: %s, state: %s", __name__, self.project, self.resource, self.state)
        
        diagramPath = self.resource
        
        handler = self.handler
        self.log.infof("...UUID: %s", self.uuid)
        
        database = handler.getDefaultDatabase(self.project, self.resource)
        self.log.infof("The default database is: %s", database)
        
        provider = handler.getDefaultTagProvider(self.project, self.resource)
        self.log.infof("The default provider is: %s", provider)
        
        block = handler.getBlock(self.project, self.resource, self.uuid)
        blockName = block.getName()
        self.log.infof("Diagram Path: %s", diagramPath)
        self.log.infof("Action Block Name: %s", blockName)
        
        trigger = self.properties.get('Trigger',{}).get("value","").lower()
        text = str(value).lower()
        if text == trigger:
            self.log.infof("...processing a trigger...")
            self.state = "TRUE"
            function = self.properties.get('Script',{}).get("value","")

            if len(function) > 0:
                self.log.tracef("...there is a function: <%s>", function)
                
                ''' If they specify shared or project scope, then we don't need to do this '''
                if not(string.find(function, "project") == 0 or string.find(function, "shared") == 0):
                    # The method contains a full python path, including the method name
                    self.log.tracef("...it is external...")
                    packName = self.packageFromFunctionPath(function)
                    funcName = self.functionFromFunctionPath(function)
                    self.log.tracef("   ...using External Python, the package is: <%s>.<%s>", packName, funcName)
                    exec("import %s" % (packName))
                    exec("from %s import %s" % (packName,funcName))
            
                eval(function)(block, diagramPath, blockName, self.uuid, provider, database)
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