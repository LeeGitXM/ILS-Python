'''
Copyright 2014 ILS Automation

A thin wrapper for receiving commands/requests addressed
to the Output subsystem.

Created on Jul 9, 2014

@author: phassler
'''
import traceback
import string
import ils.io
import ils.io.opcoutput
from ils.io import *

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
def command(tagPath, command):
    tagPath = str(tagPath)
    log.trace("%s received command: %s" % (tagPath, command))
 
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
            status,reason = tag.writeDatum()
        else:
            reason = "Unrecognized command: "+command
            log.error(reason)
    except:
        reason = "ERROR instantiating ils.io."+ pythonClass+" ("+traceback.format_exc()+")" 
        log.error(reason)
        
    return status,reason

#
# Write to RecipeData
def writeRecipeDetail(tagName, command):
    log.trace("downloading recipe detail: %s" % (tagName))
    tagName = str(tagName)
               
    # Strip off the '/command'
    if tagName.endswith('/command'):
        parentTagName = tagName[:len(tagName) - 8]
    else:
        reason = "Unexpected tag path: %s" % (tagName)
        log.error(reason)
        return False,reason
               
    # Strip off the tagname to get just the path
    path = parentTagName[:parentTagName.rfind('/')+1]
    print "Path: <%s>" % (path)
 
    # Get the name of the Python class that corresponds to this UDT.
    pythonClass = system.tag.read(path + "/pythonClass").value
    pythonClass = pythonClass.lowerCase()+"/"+pythonClass
    print "Python Class: ", pythonClass
    status = False
    reason = ""
    # Dynamically create an object (that won't live very long)
    try:
        writer = eval("io." + pythonClass + "("+path+")" )
        status, reason = writer.writeRecipeDetail(command)
    except:
        reason = "ERROR instantiating io."+ pythonClass+" ("+traceback.format_exc()+")" 
        print "io.wrapper - "+reason
        
    print "Done with writeRecipeDetail: ", path,command
    return status, reason
    