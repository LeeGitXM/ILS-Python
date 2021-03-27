#  Copyright 2014-2021 ILS Automation
#
# Utility functions for dealing with Python classes for
# the block language toolkit. This module adds any arguments needed
# for the block interface methods  to execute in a pure Python environment.
# 
import system
from ils.block import basicblock
# NOTE: We need the next two imports in order to get the classes generically.
# We require the "wild" imports so that we can iterate over classes
# NOTE: __init__.py defines the modules

import ils.block
from ils.block import *
from ils.user.block import *
from ils.log.LogRecorder import LogRecorder
log = LogRecorder(__name__)



def acceptValue(block,port,value,quality,time):
    '''
    We've received a value on  the named port. The expected data type is known by the block.
        block - the python block object
        port  - the input port name
        value - the new value, a truth-value
        quality - the quality of the new value
        time    - the timestamp of the incoming value
    '''
    if block!=None:
        log.tracef("%s.acceptValue() a %s received %s - %s on port %s", __name__, str(block.__class__), str(value), str(quality), str(port))
        block.acceptValue(port,value,quality,time)


def createBlockInstance(className, parent, uid, result):
    ''' Create an instance of a particular class.
    The arglist contains:
         class - incoming class name
         parent - UUID string of enclosing diagram
         uid    - UUID string of the block itself
         result - shared dictionary.
    '''
    log.infof('Creating a %s, parent: %s, uid: %s', className, parent, uid)
    obj = getNewBlockInstance(className)
    obj.setUUID(uid)
    obj.setParentUUID(parent)
    log.infof("...created!")
    result['instance'] = obj

def getAuxData(block,aux):
    '''
    Return the auxiliary data of a block. The aux data are contained in a 
    GeneralPurposeDataContainer structure that must be supplied. 
    '''
    

def getBlockAnchors(block,anchors):
    '''
    Given an instance of an executable block,write its properties to the supplied list (properties) as specified in the Gateway startup script.
    '''
    if block!=None:
        log.tracef("%s.getBlockAnchors: %s ==", __name__, str(block.__class__) )
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
                

def getBlockProperties(block,properties):
    '''
    Given an instance of an executable block, write its properties to the supplied list (properties).
    '''
    if block!=None:
        dictionary = block.getProperties()
        for key in dictionary:
            prop = dictionary[key]
            prop['name'] = key
            properties.append(prop)
    else:
        log.errorf("%s.getBlockProperties: argument <%s> not defined" , __name__, block)


def getBlockState(block,properties):
    '''
    Write the value of the state as a string in the results list.
    '''
    if block!=None:
        #log.infof("ils.blt.util.getBlockState: %s ==",str(block.__class__) )
        state = block.getState()
        properties.append(state)
    else:
        log.errorf("%s.getBlockState: argument <%s> not defined" , __name__, block)


def getNewBlockInstances():
    '''
    Return a new instance of each class of block.  This works as long as all the block definitions are 
    in the "app.block" package. Our convention is that only executable blocks appear in this package -- and that
    the class has the same name as its file.
    '''
    log.debugf('%s.getNewBlockInstances...', __name__)

    instances = []
    # dir only lists modules that have actually been imported
    print dir(ils.block)
    print "======= Names ========="
    for name in dir(ils.block):
        if not name.startswith('__') and not name == 'basicblock':
            className = eval("ils.block."+name+".getClassName()")
            constructor = "ils.block."+name.lower() +"."+className+"()"
            obj = eval(constructor)
            log.infof("%s.getNewBlockInstances: %s = %s", __name__, name, obj.__class__)
            instances.append(obj) 
    print "====================="
    return instances


# Return a new instance of each class of block created by users
#
#  The idea is to create a safe location for user created blocks that won't get overwritten by updates
#
# This works as long as all the block definitions are 
# in the "ils.user.block" package. Our convention is that only
# executable blocks appear in this package -- and that
# the class has the same name as its file.
#
# ***Make sure the class/file is also listed in __init.py__ or the import fails
#
# ** file and class names MUST be LOWER CASE
#
def getNewUserBlockInstances():
    log.info('getNewUserBlockInstances ...' )
    instances = []
    # dir only lists modules that have actually been imported
    print dir(ils.user.block)
    print "======= Names ========="
    for name in dir(ils.user.block):
        if not name.startswith('__') and not name == 'basicblock':
            className = eval("ils.user.block."+name+".getClassName()")
            constructor = "ils.user.block."+name.lower() +"."+className+"()"
            obj = eval(constructor)
            print "ils.blt.util.getNewUserBlockInstances:",name,'=',obj.__class__
            instances.append(obj) 
    print "====================="
    return instances


def getNewBlockInstance(className):
    '''
    Return a new instance of the specified class of block.
    A fully-qualified class must be specified. Use the null constructor.
    '''
    log.debugf('%s.getNewBlockInstance: %s', __name__, className)
    constructor = className+"()"
    obj = eval(constructor)
    return obj
    

def getBlockPrototypes(prototypes):
    '''
    Obtain a list of all subclasses of BasicBlock, then create a dictionary of prototype attributes from each. 
    Communicate results in 'prototypes', a list known to the gateway. 
    '''
    log.debugf("%s.getBlockPrototypes", __name__)
    instances = getNewBlockInstances()
    for obj in instances:
        prototypes.append(obj.getPrototype())


def notifyOfStatus(block):
    '''
    Trigger property and connection status notifications on the block
    '''
    if block!=None:
        block.notifyOfStatus()

def onDelete(block):
    '''
    Perform any custom processing on a block removal
    '''
    block.onSave()
    
def onSave(block):
    '''
    Perform any custom processing on a block save or creation/
    '''
    block.onSave()
    

def propagate(block):
    '''
     Given an instance of an executable block # Call its propagate() method. There is no shared dictionary.
    '''
    if block!=None:
        block.propagate()

def reset(block):
    '''
    Given an instance of an executable block call its reset() method. 
    '''
    if block!=None:
        block.reset()
        
def setAuxData(block,aux):
    '''
    Set the auxiliary data of a block from a database.
    This base method does nothing. 
    '''
    pass
    
def setBlockProperty(block,prop):
    '''
    Given an instance of an executable block, set one of its properties. The property
    is a dictionary named "property" as specified in the Gateway startup script.
    '''
    log.tracef('%s.setBlockProperty(block) ...', __name__)
    if block!=None:
        block.setProperty(prop.get("name","??"),prop)
    

def setBlockState(block,state):
    '''
    Write the value of the state as a string in the results list.
    '''
    if block != None:
        log.infof("%s.setBlockState: %s ==%s", __name__, str(block.__class__), state )
        block.setState(state)
    else:
        log.infof("%s.setBlockState: block <%s> not defined" ,  __name__, block)
