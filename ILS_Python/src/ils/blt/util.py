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
    print 'ils.blt.util.acceptValue(block) ...'
    
    if block!=None:
        print "util: ",block.__class__," received ",value,",",quality," on ",port
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
    print 'util.evaluate(block) ...'

    if block!=None:
        block.evluate()
        
# Given an instance of an executable block,
# write its properties to the supplied list (properties)
# as specified in the Gateway startup script.
# 
def getBlockProperties(block,properties):
    log.info('util.getBlockProperties ...' )
    if block!=None:
        print block.__class__
        print block.getProperties()
        dictionary = block.getProperties()
        for key in dictionary:
            prop = dictionary[key]
            prop['name'] = key
            properties.append(prop)
    else:
        print "getBlockProperties: argument ",block," not defined"


#
# Return a new instance of each class of block.
# This works as long as all the block definitions are 
# in the "app.block" package. Our convention is that only
# executable blocks appear in this package -- and that
# the class has the same name as its file.
def getNewBlockInstances():
    log.info('getNewBlockInstances ...' )
    instances = []
    # dir only lists modules that have actually been imported
    print dir(xom.block)
    print "======= Names ========="
    for name in dir(xom.block):
        if not name.startswith('__') and not name == 'basicblock':
            className = eval("xom.block."+name+".getClassName()")
            constructor = "emc.block."+name.lower() +"."+className+"()"
            obj = eval(constructor)
            print "getNewBlockInstances:",name,'=',obj.__class__
            instances.append(obj) 
    print "====================="
    return instances
#
# Return a new instance of the specified class of block.
# A fully-qualified class must be specified. Use the null constructor.
def getNewBlockInstance(className):
    log.infof('getNewBlockInstance: %s',className)
    constructor = className+"()"
    obj = eval(constructor)
    return obj
    
#
# Obtain a list of all subclasses of BasicBlock,
# then create a dictionary of prototype attributes from each. 
# Communicate results in 'prototypes', a list known to the gateway. 
def getBlockPrototypes(prototypes):
    log.info("getBlockPrototypes")
    instances = getNewBlockInstances()
    for obj in instances:
        print 'getBlockPrototype:',obj.__class__
        prototypes.append(obj.getPrototype())
#

# Given an instance of an executable block,
# set one of its properties. The property
# is a dictionary named "property"
# as specified in the Gateway startup script.
# 
def setBlockProperty(block,prop):
    print 'util.setBlockProperty(block) ...'

    if block!=None:
        print block.__class__
        block.setProperties(property.get("name"),prop)
    

