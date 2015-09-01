'''
Copyright 2014 ILS Automation

A thin wrapper for receiving commands/requests addressed to the Output subsystem.  These methods 
run on the gateway because they are launched by tag change scripts.

Created on Jul 9, 2014

@author: phassler
'''
import traceback
import string

# These next three lines may have warnings in eclipse, but they ARE needed!
import ils.io
import ils.io.opcoutput
import ils.io.opcconditionaloutput
import ils.io.recipedetail
import ils.io.controller
import ils.io.pkscontroller
import ils.io.tdccontroller

import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.io")

# Chuck isn't sure why this doesn't work!
import system

# This is a simple integration test of the Eclipse/Python to Ignition framework
def hello():
    print "Hello World"

# This is another simple integration test of the Eclipse/Python to Ignition framework
def tagWriter(tagPath, val):
    system.tag.write(tagPath, val)

# Command a BasicIO object
def write(tagPath, command):

    tagPath = str(tagPath)

    log.trace("Tag <%s> received command: %s" % (tagPath, command))
 
    # If the tagname ends in ".command" then trim it off
    if tagPath.endswith('/command'):
        parentTagPath = tagPath[:len(tagPath) - 8]
    else:
        parentTagPath = tagPath
 
    # Get the name of the Python class that corresponds to this UDT.
    pythonClass = system.tag.read(parentTagPath + "/pythonClass").value
    pythonClass = pythonClass.lower()+"."+pythonClass

    status = False
    reason = ""
    # Dynamically create an object (that won't live very long)
    try:
        cmd = "ils.io." + pythonClass + "('"+parentTagPath+"')"
        tag = eval(cmd)
        if string.upper(command) == "WRITEDATUM":
            status, reason = tag.writeDatum()
        elif string.upper(command) == "WRITEWITHNOCHECK":
            status, reason = tag.writeWithNoCheck()
        elif string.upper(command) == "WRITERAMP":
            status, reason = tag.writeRamp()
        elif string.upper(command) == "RESET":
            status, reason = tag.reset()
        else:
            reason = "Unrecognized command: "+command
            log.error(reason)
    except:
        reason = "ERROR writing to %s, a <%s> (%s)" % (tagPath, pythonClass, traceback.format_exc()) 
        log.error(reason)
        
    return status,reason

#
# Write to RecipeData
def writeRecipeDetail(tagPath, command):
    tagPath = str(tagPath)
    
    log.trace("Recipe Detail <%s> received command: %s" % (tagPath, command))

    # If the tagname ends in ".command" then trim it off
    if tagPath.endswith('/command'):
        parentTagPath = tagPath[:len(tagPath) - 8]
    else:
        reason = "Unexpected tag path: %s" % (tagPath)
        log.error(reason)
        return False,reason
               
    # The recipe detail UDT does not allow for multiple implementations of recipe detail via a named Java
    # tag class.  If there are variations of a recipe detail, then I can always add a tagClass property / tag in 
    # Recipe Details UDT.
    pythonClass = "recipedetail.RecipeDetail"
    status = False
    reason = ""
    # Dynamically create an object (that won't live very long)
    try:
        cmd = "ils.io." + pythonClass + "('"+parentTagPath+"')"
        writer = eval(cmd)
        status, reason = writer.writeRecipeDetail(command)
    except:
        reason = "ERROR instantiating io."+ pythonClass+" ("+traceback.format_exc()+")" 
        log.error("Error in writeRecipeDetail(): %s" % (reason))
        
    log.trace("Leaving writeRecipeDetail(): %s - %s - %s - %s" % (tagPath, command, status, reason))
    return status, reason

# This takes the name of a UDT and reads the proper embedded tag for the value.  Generally, the tag will be '/value'
# This returns a qualified value.
def read(tagPath):
    qv=system.tag.read(tagPath + '/value')
    return qv