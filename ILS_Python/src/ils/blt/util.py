#  Copyright 2014 ILS Automation
#
# Utility functions for dealing with Python classes for
# the block language toolkit. 
# 
from com.inductiveautomation.ignition.common.util import LogUtil
from ils.block import basicblock
# NOTE: We need these two imports in order to get the classes generically.
# We require the "wild" import so that we can iterate over classes
# NOTE: __init__.py defines the modules
import ils.block
from ils.block import *


log = LogUtil.getLogger("com.ils.block")

# We've received a value on our input (there is only one)
# We expect a truth value.
#  block - the python block object
#  port  - the input port name
#  value - the new value, a truth-value
#  quality - the quality of the new value
#  time    - the timestamp of the incoming value
def acceptValue(block,port,value,quality,time):
    #print 'ils.blt.util.acceptValue(block) ...'
    
    if block!=None:
        log.trace( "ils.blt.util: "+str(block.__class__)+" received "+str(value)+" ("+str(quality)+") on port "+str(port))
        block.acceptValue(port,value,quality,time)
#  ============== Externally callable ======
# Create an instance of a particular class.
# The arglist contains:
#     class - incoming class name
#     parent - UUID string of enclosing diagram
#     uid    - UUID string of the block itself
#     result - shared dictionary.
def createBlockInstance(className,parent,uid,result):
    log.infof('Creating a %s, parent: %s, uid: %s', className, parent, uid)
    obj = getNewBlockInstance(className)
    obj.setUUID(uid)
    obj.setParentUUID(parent)
    log.infof("...created!")
    result['instance'] = obj
#
# Given an instance of an executable block
# Call its propagate() method. There is no
# shared dictionary.
def propagate(block):

    if block!=None:
        block.propagate()

# Given an instance of an executable block,
# write its properties to the supplied list (properties)
# as specified in the Gateway startup script.
# 
def getBlockAnchors(block,anchors):
    
    if block!=None:
        log.tracef("ils.blt.util.getBlockAnchors: %s ==",str(block.__class__) )
        log.tracef( str(block.getInputPorts()) )
        log.tracef( str(block.getOutputPorts()) )
        dictionary = block.getInputPorts()
        for key in dictionary:
            anchor = dictionary[key]
            anchor['name'] = key
            anchor['direction'] = "incoming"
            anchors.append(anchor)
        dictionary = block.getOutputPorts()
        for key in dictionary:
            anchor = dictionary[key]
            anchor['name'] = key
            anchor['direction'] = "outgoing"
            anchors.append(anchor)
    else:
        print "ils.blt.util.getBlockAnchors: argument ",block," not defined"
                
# Given an instance of an executable block,
# write its properties to the supplied list (properties)
# as specified in the Gateway startup script.
# 
def getBlockProperties(block,properties):
    
    if block!=None:
        #log.infof("util.getBlockProperties: %s ==",str(block.__class__) )
        #log.info( str(block.getProperties()) )
        dictionary = block.getProperties()
        for key in dictionary:
            prop = dictionary[key]
            prop['name'] = key
            properties.append(prop)
    else:
        print "ils.blt.util.getBlockProperties: argument ",block," not defined"

# Write the value of the state as a string in the results list.
# 
def getBlockState(block,properties):
    
    if block!=None:
        #log.infof("ils.blt.util.getBlockState: %s ==",str(block.__class__) )
        state = block.getState()
        properties.append(state)
    else:
        print "ils.blt.util.getBlockState: argument ",block," not defined" 

#
# Return a new instance of each class of block.
# This works as long as all the block definitions are 
# in the "app.block" package. Our convention is that only
# executable blocks appear in this package -- and that
# the class has the same name as its file.
def getNewBlockInstances():
    log.debug('getNewBlockInstances ...' )
    instances = []
    # dir only lists modules that have actually been imported
    print dir(ils.block)
    print "======= Names ========="
    for name in dir(ils.block):
        if not name.startswith('__') and not name == 'basicblock':
            className = eval("ils.block."+name+".getClassName()")
            constructor = "ils.block."+name.lower() +"."+className+"()"
            obj = eval(constructor)
            print "ils.blt.util.getNewBlockInstances:",name,'=',obj.__class__
            instances.append(obj) 
    print "====================="
    return instances
#
# Return a new instance of the specified class of block.
# A fully-qualified class must be specified. Use the null constructor.
def getNewBlockInstance(className):
    log.debugf('util.getNewBlockInstance: %s',className)
    constructor = className+"()"
    obj = eval(constructor)
    return obj
    
#
# Obtain a list of all subclasses of BasicBlock,
# then create a dictionary of prototype attributes from each. 
# Communicate results in 'prototypes', a list known to the gateway. 
def getBlockPrototypes(prototypes):
    log.debug("ils.blt.util.getBlockPrototypes")
    instances = getNewBlockInstances()
    for obj in instances:
        prototypes.append(obj.getPrototype())
#
# Trigger property and connection status notifications on the block
def notifyOfStatus(block):

    if block!=None:
        block.notifyOfStatus()
#
#
# Given an instance of an executable block
# Call its reset() method. 
def reset(block):

    if block!=None:
        block.reset()
        
# Given an instance of an executable block,
# set one of its properties. The property
# is a dictionary named "property"
# as specified in the Gateway startup script.
# 
def setBlockProperty(block,prop):
    log.trace('ils.blt.util.setBlockProperty(block) ...')
    if block!=None:
        block.setProperty(prop.get("name","??"),prop)
    
# Write the value of the state as a string in the results list.
# 
def setBlockState(block,state):
    
    if block!=None:
        log.infof("ils.blt.util.setBlockState: %s ==%s",str(block.__class__),state )
        block.setState(state)
    else:
        print "ils.blt.util.setBlockState: argument ",block," not defined" 
