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


# Write a value to an OPC Output.   
def writeDatum(fullTagPath, val, writeConfirm):
    log.info("Writing %s to %s (Confirm write: %s)" % (str(val), fullTagPath, str(writeConfirm)))

    tagExists = system.tag.exists(fullTagPath)
    if not(tagExists):
        return False, "%s does not exist" % (fullTagPath)
    
    # Try and figure out if the thing is a UDT or a simple memory or OPC tag
    # There has to be a more direct way to do this but this should work
    tags = system.tag.browseTags(parentPath=fullTagPath)
    if len(tags) > 0:
        isUDT = True
    else:
        isUDT = False

    if isUDT:
        # Get the name of the Python class that corresponds to this UDT.
        pythonClass = system.tag.read(fullTagPath + "/pythonClass").value
        pythonClass = pythonClass.lower()+"."+pythonClass

        system.tag.write(fullTagPath + '/command', 'RESET')
        system.tag.write(fullTagPath + '/writeValue', val)
        system.tag.write(fullTagPath + '/command', 'WRITEDATUM')

        # The gateway is going to confirm the write whether we want to or not.   If the caller 
        # doesn't care, then don't wait around for the answer
        if writeConfirm:
            # It is going to be a little tough to come up with the exact path to the tag to be confirmed without using some 
            # knowledge of the controller structure
            from ils.io.util import waitForWriteConfirm
            confirmed, errorMessage = waitForWriteConfirm(fullTagPath)
            log.trace("Write of %s to %s - Confirmed: %s - %s" % (str(val), fullTagPath, str(confirmed), errorMessage))
            return confirmed, errorMessage
    else:
        # The 'Tag" is either a simple memory tag or an simple OPC tag
        log.trace("Simple write of %s to %s..." % (str(val), fullTagPath))
        system.tag.write(fullTagPath, val)
        if writeConfirm:
            confirmed, errorMessage = simpleWriteConfirm(fullTagPath, val)
            log.trace("Write of %s to %s - Confirmed: %s - %s" % (str(val), fullTagPath, str(confirmed), errorMessage))
            return confirmed, errorMessage

    return True, ""

def simpleWriteConfirm(fullTagPath, val, timeout=60, frequency=1): 
    log = LogUtil.getLogger("com.ils.io")

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
def writeWithNoCheck(parentTagPath, val):
    log.info("Writing %s to %s" % (str(val), parentTagPath))

    # Get the name of the Python class that corresponds to this UDT.
    pythonClass = system.tag.read(parentTagPath + "/pythonClass").value
    pythonClass = pythonClass.lower()+"."+pythonClass

    status = system.tag.write(parentTagPath + '/command', 'RESET')
    if status == 0:
        log.error("ERROR: writing RESET to the command tag for %s" % (parentTagPath))
        return False, "Failed writing RESET to command tag"
     
    status = system.tag.write(parentTagPath + '/writeValue', val)
    if status == 0:
        log.error("ERROR: writing %s to the writeValue tag for %s" % (str(val), parentTagPath))
        return False, "Failed writing %s to writeValue tag" % (str(val))
    
    status = system.tag.write(parentTagPath + '/command', 'WriteWithNoCheck')
    if status == 0:
        log.error("ERROR: writing WRITEWITHNOCHECK to the command tag for %s" % (parentTagPath))
        return False, "Failed writing WRITEWITHNOCHECK to command tag"

    # Without confirming the round trip of the value
    from ils.io.util import waitForWriteComplete
    success, errorMessage = waitForWriteComplete(parentTagPath)
    
    return success, errorMessage

# This is the equivalent of s88-write-output in the old system.  This should work for a EPKS or a TDC3000 controller.
# This assumes that the controller has already been reset.
# This is called by Python and runs in the client.  The actual tag writing occurs in the gateway.
# If writeConfirm is true then this will run for a long time and may block the thread.
def writeOutput(controllerTagname, block, val, valType, writeConfirm):
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

