'''
Copyright 2014 ILS Automation

A thin wrapper for receiving commands/requests addressed
to the Output subsystem.

Created on Jul 9, 2014

@author: phassler
'''
import traceback
import string

# Chuck isn't sure why this doesn't work!
#import system

import system.tag as tag

# This is a simple integration test of the Eclipse/Python to Ignition framework
def hello():
    print "Hello World"

# This is another simple integration test of the Eclipse/Python to Ignition framework
def tagWriter(tagPath, val):
    tag.write(tagPath, val)

# Command a BasicIO object
def command(tagPath, command):
    print "%s received command: %s" % (tagPath, command)
 
    # If the tagname ends in ".command" then trim it off
    if tagPath.endswith('/command'):
        parentTagPath = tagPath[:len(tagPath) - 8]
    else:
        parentTagPath = tagPath
 
    # Get the name of the Python class that corresponds to this UDT.
    pythonClass = tag.read(parentTagPath + "/pythonClass").value
    pythonClass = pythonClass.lowerCase()+"/"+pythonClass
    print "Python Class: ", pythonClass
    status = False
    reason = ""
    # Dynamically create an object (that won't live very long)
    try:
        tag = eval("emc.io." + pythonClass + "("+parentTagPath+")" )
        if string.upper(command) == "WRITEDATUM":
            status,reason = tag.writeDatum()
        else:
            reason = "Unrecognized command: "+command
            print reason
    except:
        reason = "ERROR instantiating emc.io."+ pythonClass+" ("+traceback.format_exc()+")" 
        print "emc.io.wrapper - "+reason
        
    return status,reason

#
# Write to RecipeData
def writeRecipeDetail(tagName, command):
    print "     downloading recipe detail: ", tagName
    tagName = str(tagName)
               
    # Strip off the '/command'
    if tagName.endswith('/command'):
        parentTagName = tagName[:len(tagName) - 8]
    else:
        reason = "ERROR: Unexpected tag path: "+ tagName
        print reason
        return False,reason
               
    # Strip off the tagname to get just the path
    path = parentTagName[:parentTagName.rfind('/')+1]
    print "Path: <%s>" % (path)
 
    # Get the name of the Python class that corresponds to this UDT.
    pythonClass = tag.read(path + "/pythonClass").value
    pythonClass = pythonClass.lowerCase()+"/"+pythonClass
    print "Python Class: ", pythonClass
    status = False
    reason = ""
    # Dynamically create an object (that won't live very long)
    try:
        writer = eval("emc.io." + pythonClass + "("+path+")" )
        status, reason = writer.writeRecipeDetail(command)
    except:
        reason = "ERROR instantiating emc.io."+ pythonClass+" ("+traceback.format_exc()+")" 
        print "emc.io.wrapper - "+reason
        
    print "Done with writeRecipeDetail: ", path,command
    return status, reason
    