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
import com.ils.common.GeneralPurposeDataContainer as GeneralPurposeDataContainer
import time


class BasicBlock():
    
    
    def __init__(self):
        # Each block has a state, whether it is meaningful or not
        self.state = "UNSET"
        self.quality = "good"
        self.time = 0
        self.auxData = GeneralPurposeDataContainer()
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
        self.className = 'ils.block.basicblock.BasicBlock'
        
        
    # Called when a value has arrived on one of our input ports
    # By default, we do nothing
    def acceptValue(self,port,value,quality,time):
        self.value   = value
        self.quality = quality
        self.time    = time 
    # The base method leaves the aux data unchanged.
    def getAuxData(self,aux):
        print "basicblock: getAuxData"
        pass
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
    # Return the current block state
    def getState(self):
        return self.state
    # Return a list of all input ports
    def getInputPorts(self):
        return self.inports
    # Return a list of all output ports
    def getOutputPorts(self):
        return self.outports
        # Trigger property and connection notifications on the block
    def notifyOfStatus(self):
        pass
    def onDelete(self):
        pass
    def onSave(self):
        pass
    # Propagate the current state of the block. This default implementation
    # does nothing.
    def propagate(self):
        pass
    # Report to the engine that a new value has appeared at an output port
    def postValue(self,port,value,quality,time):
        self.handler.postValue(self.parentuuid,self.uuid,port,value,quality,long(time))
    # Reset the block. This default implementation
    # sends notifications on all output connections.
    def reset(self):
        self.state = 'UNSET'
        now = long(time.time()*1000)
        for anchor in self.outports:
            if anchor['type'].upper()=='TRUTHVALUE':
                self.handler.sendConnectionNotification(self.uuid,anchor["name"],'UNSET',"Good",long(now))
            elif anchor['type'].upper() == 'DATA':
                self.handler.sendConnectionNotification(self.uuid,anchor["name"],String.valueOf(Double.NaN),"Good",now)
            else:
                self.handler.sendConnectionNotification(self.uuid,anchor["name"],"","Good",now)
    
    # Set aux data in an external database. This base method does nothing
    def setAuxData(self,data):
        print "basicblock: setAuxData"
        pass
    # The proxy block contains the name.
    # This method is intended as a hook for an extension function to do, essentially, a rename
    def setName(self,name):
        pass
    # Replace or add a property
    # We expect the dictionary to have all the proper attributes
    def setProperty(self,name,dictionary):
        #print "BasicBlock.setProperty:",name,"=",dictionary
        self.properties[name] = dictionary
        self.handler.sendPropertyNotification(self.uuid,name,dictionary.get("value",""))
        
    # Programmatically set the state. The default implementation has no side effects.
    def setState(self,newState):
        #print "BasicBlock.setProperty:",name,"=",dictionary
        self.state = newState
       
    # Set the block's UUID (a string)
    def setUUID(self,uid):
        self.uuid = uid
    # Set the block's parent's UUID (a string)
    def setParentUUID(self,uid):
        self.parentuuid = uid  
           
    
    # Convenience method to extract the package name from a function
    # Use this for the import
    def packageFromFunctionPath(self, packageModuleFunction):
        packName = packageModuleFunction
        index = packageModuleFunction.rfind(".")
        if index > 0:
            packName = packageModuleFunction[0:index]
        return packName
    
    # Convenience method to extract the package name from a function
    # Use this for the import
    def functionFromFunctionPath(self, packageModuleFunction):
        funcName = packageModuleFunction
        index = packageModuleFunction.rfind(".")
        if index>0:
            funcName = packageModuleFunction[index+1:]
        return funcName