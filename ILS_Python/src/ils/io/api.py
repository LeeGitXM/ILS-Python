'''
Created on Nov 30, 2014

@author: Pete
'''
import string
import system
import time
import traceback
from java.util import Date

# These next three lines may have warnings in eclipse, but they ARE needed!
import ils.io
import ils.io.opcoutput
import ils.io.opcconditionaloutput
import ils.io.recipedetail
import ils.io.controller
import ils.io.pkscontroller
import ils.io.tdccontroller

import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.io.api")

# This is a convenience function that determines to correct API to use based on the target of the write.  
# If the target is a simple memory or OPC tag, then wither writeDatum or writeWithNoCheck will be used.  If the target is
# a UDT then writeOutput or writeRamp will be used.  If writing to a simple tag, then the valueType attribute is ignored
# This can run in either the client or the gateway    
def write(fullTagPath, val, writeConfirm, valueType="value"):
    log.info("Writing %s to the %s of %s (Confirm write: %s)" % (str(val), valueType, fullTagPath, str(writeConfirm)))
    
    tagExists = system.tag.exists(fullTagPath)
    if not(tagExists):
        return False, "%s does not exist" % (fullTagPath)
    
    # Try and figure out if the thing is a UDT or a simple memory or OPC tag
    # There has to be a more direct way to do this but this should work
    tags = system.tag.browseTags(parentPath=fullTagPath)
    if len(tags) > 0:
        isController = True
    else:
        isController = False

    success = True
    errorMessage = ""
    
    if isController:
        writeOutput(fullTagPath, val, writeConfirm, valueType)

    else:
        # The 'Tag" is either a simple memory tag or an simple OPC tag
        log.trace("Simple write of %s to %s..." % (str(val), fullTagPath))
        if writeConfirm:
            success, errorMessage = writeDatum(fullTagPath, val, writeConfirm)
        else:
            success, errorMessage = writeWithNoCheck(fullTagPath, val)
        

    return success, errorMessage


# Dispatch the RESET command to the appropriate output/controller.  This should work for outputs and  EPKS or TDC3000 controllers.
# This is called from Python and runs in the client.  Because this only rests memory tags and confirmation does not apply, all
# tag writes are called from the client and they should be very fast.
def reset(tagname):
    log.trace("Resetting %s" % (tagname))
    
    # Get the name of the Python class that corresponds to this UDT.
    pythonClass = system.tag.read(tagname + "/pythonClass").value
    pythonClass = pythonClass.lower()+"."+pythonClass

    # Dynamically create an object (that won't live very long) and then call its reset method
    try:
        cmd = "ils.io." + pythonClass + "('"+tagname+"')"
        controller = eval(cmd)
        controller.reset()

    except:
        reason = "ERROR resetting controller to %s, a <%s> (%s)" % (tagname, pythonClass, traceback.format_exc()) 
        log.error(reason)  


# Write a value to a simple memory tag, a simple OPC tag, or one of our simple UDTs but not a controller.  If writing to a UDT, then WriteOutput should be used
# This can run in either the client or the gateway
# The tagPath should contain the provider    
def writeDatum(tagPath, val, writeConfirm):
    log.info("Writing %s to %s (Confirm write: %s)" % (str(val), tagPath, str(writeConfirm)))

# TODO Will this work for a simple OPCFloatBadFlad UDT?

    tagExists = system.tag.exists(tagPath)
    if not(tagExists):
        return False, "%s does not exist" % (tagPath)
    
    if checkIfUDT(tagPath):
        # The 'Tag" is either a simple memory tag or an simple OPC tag
        
        status = system.tag.write(tagPath + '/command', 'RESET')
        if status == 0:
            log.error("ERROR: writing RESET to the command tag for %s" % (tagPath))
            return False, "Failed writing RESET to command tag"
         
        status = system.tag.write(tagPath + '/writeValue', val)
        if status == 0:
            log.error("ERROR: writing %s to the writeValue tag for %s" % (str(val), tagPath))
            return False, "Failed writing %s to writeValue tag" % (str(val))
        
        status = system.tag.write(tagPath + '/command', 'WriteDatum')
        if status == 0:
            log.error("ERROR: writing WRITEWITHNOCHECK to the command tag for %s" % (tagPath))
            return False, "Failed writing WRITEWITHNOCHECK to command tag"
    
        # Without confirming the round trip of the value
        from ils.io.util import waitForWriteComplete
        success, errorMessage = waitForWriteComplete(tagPath)        
        if not(success):
            return False, errorMessage
        
        # The write was successful, now confirm the write by reading the value back
        if writeConfirm:
            confirmed, errorMessage = simpleWriteConfirm(tagPath, val)
            log.trace("Write of %s to %s - Confirmed: %s - %s" % (str(val), tagPath, str(confirmed), errorMessage))
            return confirmed, errorMessage
    else:
        # The 'Tag" is either a simple memory tag or an simple OPC tag
        log.trace("Simple write of %s to %s..." % (str(val), tagPath))
        system.tag.write(tagPath, val)
        if writeConfirm:
            confirmed, errorMessage = simpleWriteConfirm(tagPath, val)
            log.trace("Write of %s to %s - Confirmed: %s - %s" % (str(val), tagPath, str(confirmed), errorMessage))
            return confirmed, errorMessage

    return True, ""

def simpleWriteConfirm(tagPath, val, timeout=60, frequency=1): 
    log = LogUtil.getLogger("com.ils.io")

    if checkIfUDT(tagPath):
        fullTagPath = tagPath + "/value"
        log.trace("Confirming write to a UDT <%s>..." % (fullTagPath))
    else:
        fullTagPath = tagPath
        log.trace("Confirming write to a simple tag <%s>..." % (fullTagPath))
 
    startTime = Date().getTime()
    delta = (Date().getTime() - startTime) / 1000

    while (delta < timeout):
        readbackValue = system.tag.read(fullTagPath).value
        if readbackValue == val:
            return True, ""

        # Time in seconds
        time.sleep(frequency)
        delta = (Date().getTime() - startTime) / 1000

    log.error("Timed out waiting for write confirmation of %s!" % (fullTagPath))
    return False, "Timed out waiting for write confirmation"


# Write a value to an OPC Output.  
# This does not support writes at the UDT layer of a UDT controller
# The tagPath must contain the provider 
def writeWithNoCheck(tagPath, val):
    log.info("Writing %s to %s (writeWithNoCheck)" % (str(val), tagPath))
    success = True
    errorMessage = ""
    
    if checkIfUDT(tagPath):
        status = system.tag.write(tagPath + '/command', 'RESET')
        if status == 0:
            log.error("ERROR: writing RESET to the command tag for %s" % (tagPath))
            return False, "Failed writing RESET to command tag"
         
        status = system.tag.write(tagPath + '/writeValue', val)
        if status == 0:
            log.error("ERROR: writing %s to the writeValue tag for %s" % (str(val), tagPath))
            return False, "Failed writing %s to writeValue tag" % (str(val))
        
        status = system.tag.write(tagPath + '/command', 'WriteWithNoCheck')
        if status == 0:
            log.error("ERROR: writing WRITEWITHNOCHECK to the command tag for %s" % (tagPath))
            return False, "Failed writing WRITEWITHNOCHECK to command tag"
    
        # Without confirming the round trip of the value
        from ils.io.util import waitForWriteComplete
        success, errorMessage = waitForWriteComplete(tagPath)
    else:
        status = system.tag.write(tagPath, val)
        if status == 0:
            log.error("ERROR: writing %s to %s" % (str(val), tagPath))
            return False, "Failed writing %s to %s" % (str(val), tagPath)
        
    return success, errorMessage

#---------------------------------
# Get the name of the Python class that corresponds to this UDT.
#    pythonClass = system.tag.read(parentTagPath + "/pythonClass").value
#    pythonClass = pythonClass.lower()+"."+pythonClass
#---------------------------------

# This is the equivalent of s88-write-output in the old system.  This should work for a EPKS or a TDC3000 controller.
# This assumes that the controller has already been reset.
# This is called by Python and runs in the client.  The actual tag writing occurs in the gateway.
# If writeConfirm is true then this will run for a long time and may block the thread.
def writeOutput(controllerTagname, val, writeConfirm, valType):
    print "In api.writeOutput()"
    if string.upper(valType) in ["SP", "SETPOINT"]:
        tagRoot = controllerTagname + '/sp'
    elif string.upper(valType) in ["OP", "OUTPUT"]:
        tagRoot = controllerTagname + '/op'
    elif string.upper(valType) in ["MODE"]:
        tagRoot = controllerTagname + '/mode'
    else:
        log.error("Unexpected valType: <%s>" % (valType))
        return False, "Unexpected valType: <%s>" % (valType)
    
    log.trace("Writing %s to %s" % (str(val), tagRoot))
    system.tag.write(tagRoot + '/writeValue', val)
    system.tag.write(tagRoot + '/command', 'WRITEDATUM')
    
    # The gateway is going to confirm the write whether we want to or not.   If the caller 
    # doesn't care, then don't wait around for the answer
    if writeConfirm:
        from ils.io.util import waitForWriteConfirm
        confirmed, errorMessage = waitForWriteConfirm(tagRoot)
        log.trace("Write of %s to %s - Confirmed: %s - %s" % (str(val), tagRoot, str(confirmed), errorMessage))
        return confirmed, errorMessage
    
    return True, ""

# This is the equivalent of s88-write-setpoint-ramp in the old system.
# This method makes sequential writes to ramp either the SP or OP of an Experion controller.  
# There is no native output ramping capability in EPKS and this method fills the gap.  
# In addition, it will ramp the SP of a controller that isn't built in G2 as having native EPKS SP Ramp capability.  
# In both cases, the ramp is executed by writing sequentially based on a linear ramp.  
# It assumes that the ramp time is in minutes..   
def writeRamp(controllerTagname, block, val, rampTime, updateFrequency, valType, writeConfirm):
    log.info("Writing a controller ramp for %s" % (controllerTagname))
    payload = {"val": val, "rampTime": rampTime, "updateFrequency": updateFrequency, "writeConfirm": writeConfirm, "valType": valType}
    
    system.tag.write(controllerTagname + '/payload', payload)
    system.tag.write(controllerTagname + '/command', 'WRITERAMP')
    
    # The gateway is going to confirm the write whether we want to or not.   If the caller 
    # doesn't care, then don't wait around for the answer
    if writeConfirm:
        # It is going to be a little tough to come up with the exact path to the tag to be confirmed without using some 
        # knowledge of the controller structure
        from ils.io.util import waitForWriteConfirm
        confirmed, errorMessage = waitForWriteConfirm(controllerTagname)
        return confirmed
    
    return True


# This is the equivalent of s88-confirm-controller-mode in the old system.
# This is a method dispatcher to the method appropriate for the class of controller.
# This is called from Python and runs in the client.
def checkConfig(controllerTagname, block, val, testForZero, checkPathToValue, valType):
    print "In api.checkConfig()"

    # Get the name of the Python class that corresponds to this UDT.
    pythonClass = system.tag.read(controllerTagname + "/pythonClass").value
    pythonClass = pythonClass.lower()+"."+pythonClass

    # Dynamically create an object (that won't live very long) and then call its reset method
    try:
        cmd = "ils.io." + pythonClass + "('"+controllerTagname+"')"
        controller = eval(cmd)
        success, errorMessage = controller.checkConfig(val, testForZero, checkPathToValue, valType)

    except:
        success = False
        errorMessage = "ERROR checking controller configuration to %s, a <%s> (%s)" % (controllerTagname, pythonClass, traceback.format_exc()) 
        log.error(errorMessage)  

    return success, errorMessage

def validateValueType(valueType):
    # Translate some valueTypes where we use one thing in the UI and another in the UDT
    if string.upper(valueType) in ['SP', 'SETPOINT']:
        valueType = "sp"
    if string.upper(valueType) in ['OP', 'OUTPUT']:
        valueType = "op"
    return valueType


# Try and figure out if the thing is a UDT or a simple memory or OPC tag
# There has to be a more direct way to do this but this should work
def checkIfUDT(fullTagPath):    
    tags = system.tag.browseTags(parentPath=fullTagPath)
    if len(tags) > 0:
        isUDT = True
    else:
        isUDT = False
    return isUDT
    
# Get the string that will typically be displayed in the DCS Tag Id column of the download monitor
def getDisplayName(provider, tagPath, valueType, displayAttribute):
    import string 
    
    fullTagPath='[%s]%s' % (provider, tagPath)

    # Check if the tag exists
    tagExists = system.tag.exists(fullTagPath)
    if not(tagExists):
        return "Tag does not exist!"
    
    # Use the last portion of the UDT / tag that we are writing to 
    if string.upper(displayAttribute) == 'NAME':
        displayName=fullTagPath[fullTagPath.rfind('/')+1:]
    
    elif string.upper(displayAttribute) == 'ITEMID':
        # This needs to be smart enough to not blow up if using memory tags (which we will be in isolation)

        valueType=validateValueType(valueType)
        isUDT = checkIfUDT(fullTagPath)

        if isUDT:    
            if string.upper(valueType) == "VALUE":
                displayName = system.tag.read(fullTagPath + '/value.OPCItemPath').value
            else:
                displayName = system.tag.read(fullTagPath + '/' + valueType + '/value.OPCItemPath').value        
        else:
            displayName = system.tag.read(fullTagPath + '.OPCItemPath').value

    else:
        displayName = ''

    return displayName
