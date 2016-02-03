'''
Created on Dec 3, 2014

@author: Pete
'''

import system, string, time
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
from java.util import Date
from ils.common.util import isText
from ils.common.util import isFloattOrSpecialValue

# Try and figure out if the thing is a UDT or a simple memory or OPC tag
# There has to be a more direct way to do this but this should work
def checkIfUDT(fullTagPath):    
    tags = system.tag.browseTags(parentPath=fullTagPath)
    if len(tags) > 0:
        isUDT = True
    else:
        isUDT = False
    return isUDT

# Try and figure out if the thing is a controller, we should already know that it is a UDT.
# If it has a tag PythonClass, and the Python class contains the word controller then it is a controller, 
# otherwise it is NOT a controller.
def checkIfController(fullTagPath):
    tagPath=fullTagPath + '/pythonClass'
    exists=system.tag.exists(tagPath)
    if not(exists):
        return False

    pythonClass=system.tag.read(tagPath).value
#    print "Checking if <%s> contains <CONTROLLER>" % (pythonClass)
    if pythonClass.upper().find('CONTROLLER') > -1:
        return True

    return False

# Compare two tag values taking into account that a float may be disguised as a text string and also
# calling two floats the same if they are almost the same.
def equalityCheck(val1, val2, recipeMinimumDifference, recipeMinimumRelativeDifference):
    val1IsText = isText(val1)
    val2IsText = isText(val2)

    # When we write a NaN we read back a Null value which looks like a '' - Treat these as equal
    if string.upper(str(val1)) == "NAN" or string.upper(str(val2)) == "NAN":
        val1 = string.upper(str(val1))
        val2 = string.upper(str(val2))

        if (val1 == 'NAN' or val1 == '' or val1 == 'NONE' or val1 == None) and (val2 == 'NAN' or val2 == '' or val2 == 'NONE' or val2 == None):
            return True
        else:
            return False
        
    elif val1IsText and val2IsText:
        if val1 == val2:
            return True
        else:
            return False

    else:
        # They aren't both text, so if only one is text, then they don't match 
        if val1IsText or val2IsText:
            return False
        else:
            minThreshold = abs(recipeMinimumRelativeDifference * float(val1))
            if minThreshold < recipeMinimumDifference:
                minThreshold = recipeMinimumDifference

            if abs(float(val1) - float(val2)) < minThreshold:
                return True
            else:
                return False


# Verify that val2 is the same data type as val1.  Make sure to treat special values such as NaN as a float
def dataTypeMatch(val1, val2):
    val1IsFloat = isText(val1)
    val2IsFloat = isText(val2)
    
    if val1IsFloat != val2IsFloat:
        return False
    
    return True


# Implement a simple write confirmation.  We know the value that we tried to write, read the tag for a
# reasonable amount of time.  As soon as we read the value back we are done.  The tagPath must be the full path to the 
# OPC tag that we are confirming, not the UDT that contains it. 
def confirmWrite(tagPath, val, timeout=60.0, frequency=1.0): 
    log = LogUtil.getLogger("com.ils.io")
    log.trace("Confirming the write of <%s> to %s..." % (str(val), tagPath))
 
    startTime = Date().getTime()
    delta = (Date().getTime() - startTime) / 1000
    
    while (delta < timeout):
        qv = system.tag.read(tagPath)
        log.trace("%s: comparing %s-%s to %s" % (tagPath, str(qv.value), str(qv.quality), str(val)))
        if string.upper(str(val)) == "NAN":
            if qv.value == None:
                return True, ""
        else:
            if string.upper(str(qv.quality)) == 'GOOD':
                if qv.value == val:
                    return True, ""
                if equalityCheck(qv.value, val, 0.0001, 0.0001):
                    return True, ""

        # Time in seconds
        time.sleep(frequency)
        delta = (Date().getTime() - startTime) / 1000

    log.info("Write of <%s> to %s was not confirmed!" % (str(val), tagPath))
    return False, "Value %s was not confirmed" % (str(val))  

# This waits for a pending write / confirmation to complete and then reports back the results.  This does not perform 
# any value comparison or have any output specific knowledge.  There is another thread running, generally in the gateway,
# that is methodized on the class of object performing the write that does the actual write comparison.  This probably should 
# keep checking as long as the write method is still running, as indicated by a NULL writeStatus, but I have implemented a 
# timeout just to prevent it from running forever. 
def waitForWriteConfirm(tagRoot, timeout=60, frequency=1): 
    
    log = LogUtil.getLogger("com.ils.io")

    log.trace("Waiting for write confirmation for <%s>..." % (tagRoot))
 
    startTime = Date().getTime()
    delta = (Date().getTime() - startTime) / 1000

    while (delta < timeout):
        writeStatus = system.tag.read(tagRoot + "/writeStatus").value
        if string.upper(writeStatus) in ["SUCCESS", "FAILURE"]:
            writeConfirmed = writeStatus = system.tag.read(tagRoot + "/writeConfirmed").value
            writeErrorMessage = writeStatus = system.tag.read(tagRoot + "/writeErrorMessage").value
            return writeConfirmed, writeErrorMessage

        # Time in seconds
        time.sleep(frequency)
        delta = (Date().getTime() - startTime) / 1000

    log.error("Timed out waiting for write confirmation of %s!" % (tagRoot))
    return False, "Timed out waiting for write confirmation"
   
# This waits for a pending write to complete and then reports back the results of the write.  This does not do a write 
# confirm in the sense that it compares the value we wrote to the actual value.  It is generally used with a WriteWithNoCheck.
# It will check the basics of tag configuration and report that back.  It will also report if the OPC write was successful. 
# It determines if a write is complete by checking for SUCCESS or FAILURE in the writeStatus tag.
def waitForWriteComplete(tagRoot, timeout=60, frequency=1): 
    log = LogUtil.getLogger("com.ils.io")
    log.trace("Waiting for write completion for <%s>..." % (tagRoot))
 
    startTime = Date().getTime()
    delta = (Date().getTime() - startTime) / 1000

    while (delta < timeout):
        writeStatus = system.tag.read(tagRoot + "/writeStatus").value
        if string.upper(writeStatus) == "SUCCESS":
            return True, ""
        elif string.upper(writeStatus) == "FAILURE":
            writeErrorMessage = system.tag.read(tagRoot + "/writeErrorMessage").value
            return False, writeErrorMessage

        # Time in seconds
        time.sleep(frequency)
        delta = (Date().getTime() - startTime) / 1000

    log.error("Timed out waiting for write complete of %s!" % (tagRoot))
    return False, "Timed out waiting for write complete"

# This parses a full tagpath, which includes the provider at the beginning in square brackets, and returns the 
# provider without the brackets.
def getProviderFromTagpath(tagPath):
    provider=tagPath[1:tagPath.find(']')]
    return provider

# Convert a full tag path to just the tag name.
# Full tag paths are always used internally, but just the tag name is used for display purposes.
def splitTagPath(tagPath):
    parentPath = tagPath[:string.rfind(tagPath, '/')]
    tagName = tagPath[string.rfind(tagPath, '/') + 1:]
    print "Split <%s> into <%s> and <%s>" % (tagPath, parentPath, tagName)
    return parentPath, tagName