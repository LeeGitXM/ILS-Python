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
import xom.block
from xom.block import *


log = LogUtil.getLogger("com.ils.block")

# We've received a value on our input (there is only one)
# We expect a truth value.
#  block - the python block object
#  port  - the input port name
#  value - the new value, a truth-value
#  quality - the quality of the new value
def acceptValue(block,port,value,quality):
    #print 'ils.blt.util.acceptValue(block) ...'
    
    if block!=None:
        log.info( "ils.block.util: "+str(block.__class__)+" received "+str(value)+" ("+str(quality)+") on port "+str(port))
        block.acceptValue(value,quality,port)
#  ============== Externally callable ======
# Create an instance of a particular class.
# The arglist contains:
#     class - incoming class name
#     parent - UUID string of enclosing diagram
#     uid    - UUID string of the block itself
#     result - shared dictionary.
def createBlockInstance(className,parent,uid,result):
    log.infof('createBlockInstance ...%s',className )
    obj = getNewBlockInstance(className)
    obj.setUUID(uid)
    obj.setParentUUID(parent)
    result['instance'] = obj
#
# Given an instance of an executable block
# Call its evaluate() method. There is no
# shared dictionary.
def evaluate(block):

    if block!=None:
        block.evluate()

# Given an instance of an executable block,
# write its properties to the supplied list (properties)
# as specified in the Gateway startup script.
# 
def getBlockAnchors(block,anchors):
    
    if block!=None:
        log.infof("util.getBlockAnchors: %s ==",str(block.__class__) )
        log.info( str(block.getInputPorts()) )
        log.info( str(block.getOutputPorts()) )
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
        print "util.getBlockAnchors: argument ",block," not defined"
                
# Given an instance of an executable block,
# write its properties to the supplied list (properties)
# as specified in the Gateway startup script.
# 
def getBlockProperties(block,properties):
    
    if block!=None:
        log.infof("util.getBlockProperties: %s ==",str(block.__class__) )
        log.info( str(block.getProperties()) )
        dictionary = block.getProperties()
        for key in dictionary:
            prop = dictionary[key]
            prop['name'] = key
            properties.append(prop)
    else:
        print "util.getBlockProperties: argument ",block," not defined"

# Write the value of the state as a string in the results list.
# 
def getBlockState(block,properties):
    
    if block!=None:
        log.infof("util.getBlockState: %s ==",str(block.__class__) )
        state = block.getState()
        properties.append(state)
    else:
        print "util.getBlockState: argument ",block," not defined"


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
    print dir(xom.block)
    print "======= Names ========="
    for name in dir(xom.block):
        if not name.startswith('__') and not name == 'basicblock':
            className = eval("xom.block."+name+".getClassName()")
            constructor = "xom.block."+name.lower() +"."+className+"()"
            obj = eval(constructor)
            print "util.getNewBlockInstances:",name,'=',obj.__class__
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
    log.debug("util.getBlockPrototypes")
    instances = getNewBlockInstances()
    for obj in instances:
        print 'util.getBlockPrototype:',obj.__class__
        prototypes.append(obj.getPrototype())
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
    log.debug('util.setBlockProperty(block) ...')
    if block!=None:
        block.setProperty(prop.get("name","??"),prop)
    

