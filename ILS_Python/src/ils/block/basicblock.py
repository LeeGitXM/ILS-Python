#  Copyright 2014 ILS Automation
#
# An abstract base class for all executable blocks written
# in tbe Python style.
#
# WARNING: basic imports (like sys) fail here, but succeed in subclasses.
#          Could it be from the import * in util.py? 
# NOTE: Subclasses must be added to __init__.py.
#
import com.ils.blt.gateway.PythonRequestHandler as PythonRequestHandler
import java.lang.Double as Double
import java.lang.String as String
import time


class BasicBlock():
    
    
    def __init__(self):
        # Each block has a state, whether it is meaningful or not
        self.state = "UNSET"
        # Properties are a dictionary of attributes keyed by name
        # Properties attributes: name, value, editable, type(STRING,DOUBLE,INTEGER,BOOLEAN,OBJECT)
        #            The name attribute is set automatically to the key
        # - property values are cached in the Gateway java proxy
        # - values should not be changed except by call from the proxy
        self.properties = {}
        # Input ports are named stubs for incoming connections
        # Ports have properties: name,connectionType
        self.inports = []
        # Outports are named stubs for outgoing connections
        # Connection types are: data,information,signal,truthvalue
        self.outports = []
        # Each block has a unique id that matches its proxy object
        self.uuid = ""
        self.parentuuid=""
        # This is the handler that takes care of injecting results
        # into the execution engine.
        self.handler = PythonRequestHandler()
        self.initialize()
    
    # Set the default properties and connection ports
    # For the super class there are none.
    
    def initialize(self):    
        self.className = 'xom.block.basicblock.BasicBlock'
        
        
    # Called when a value has arrived on one of our input ports
    # By default, we do nothing
    def acceptValue(self,port,value,quality,time):
        self.value = value
        self.quality = quality 
      
    # Return the class name. This is a fully qualified
    # path, including the module path 
    def getClassName(self):
        return self.className
            
    # Return a list of property names. 
    def getPropertyNames(self):
        return self.properties.keys()
        
    # Return a specified property. The property
    # is a dictionary guaranteed to have a "value". 
    def getProperty(self,name):
        return self.properties.get(name,{})
        
    # Return all properties
    def getProperties(self):
        return self.properties
    # Return all properties
    def getState(self):
        return self.state
    # Return a list of all input ports
    def getInputPorts(self):
        return self.inports
    # Return a list of all output ports
    def getOutputPorts(self):
        return self.outports
    # Set the block's UUID (a string)
    def setUUID(self,uid):
        self.uuid = uid
    # Set the block's parent's UUID (a string)
    def setParentUUID(self,uid):
        self.parentuuid = uid
        
    # Report to the engine that a new value has appeared at an output port
    def postValue(self,port,value,quality,time):
        self.handler.postValue(self.parentuuid,self.uuid,port,value,quality,long(time))
    # Replace or add a property
    # We expect the dictionary to have all the proper attributes
    def setProperty(self,name,dictionary):
        #print "BasicBlock.setProperty:",name,"=",dictionary
        self.properties[name] = dictionary
        self.handler.sendPropertyNotification(self.uuid,name,dictionary.get("value",""))
        
    # Evaluate the block. This is called on expiration
    # of a timer. This default implementation
    # does nothing.
    def evaluate(self):
        pass
    # Trigger property and connection notifications on the block
    def notifyOfStatus(self):
        pass
    # Reset the block. This default implementation
    # sends notifications on all output connections.
    def reset(self):
        self.state = 'UNSET'
        now = long(time.time()*1000)
        print "BASICBLOCK:",now
        for anchor in self.outports:
            if anchor['type'].upper()=='TRUTHVALUE':
                self.handler.sendConnectionNotification(self.uuid,anchor["name"],'UNKNOWN',"Good",long(now))
            elif anchor['type'].upper() == 'DATA':
                self.handler.sendConnectionNotification(self.uuid,anchor["name"],String.valueOf(Double.NaN),"Good",now)
            else:
                self.handler.sendConnectionNotification(self.uuid,anchor["name"],"","Good",now)
    
    # Convenience method to extract the package name from a module
    # Use this for the import
    def packageFromModule(self,modName):
        packName = modName
        index = modName.rfind(".")
        if index>0:
            print "BasicBlock.packageFromModule: ",modName,",",index
            packName = modName[0:index]
        return packName
    