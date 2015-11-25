'''
Created on Nov 30, 2014

@author: Pete
'''
import string
import system
import time
import traceback
from java.util import Date
from ils.io.util import checkIfUDT

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

# This is a convenience function that determines the correct API to use based on the target of the write.
# (If this is a convenience function, why would I ever use the INCONVENIENT functions?)
# If the target is a simple memory tag, an OPC tag or one of our OPC tag UDTs then either writeDatum or writeWithNoCheck 
# will be used.  If the target is a UDT controller then writeOutput or writeRamp will be used.  If writing to a simple tag, 
# then the valueType attribute is ignored.  This can run in either the client or the gateway    
def write(fullTagPath, val, writeConfirm, valueType="value"):
    log.info("(api.write) Writing %s to the %s of %s (Confirm write: %s)" % (str(val), valueType, fullTagPath, str(writeConfirm)))
    
    tagExists = system.tag.exists(fullTagPath)
    if not(tagExists):
        return False, "%s does not exist" % (fullTagPath)

    success = True
    errorMessage = ""

    if checkIfUDT(fullTagPath):
        # This could be collapsed - we don't really need to know the Python class here - leaving it in for now as 
        # an example of how to determine the Python class. 
        pythonClass = system.tag.read(fullTagPath + "/pythonClass").value
        
        if pythonClass in ["Controller", "PKSController", "PKSACEController", "TDCController"]:
            log.trace("...writing to a controller...")
            if writeConfirm:
                success, errorMessage = writeDatum(fullTagPath, val, valueType)
            else:
                success, errorMessage = writeWithNoCheck(fullTagPath, val, valueType)
        else:
            log.trace("...writing to an OPC tag UDT...")
            if writeConfirm:
                success, errorMessage = writeDatum(fullTagPath, val, valueType)
            else:
                success, errorMessage = writeWithNoCheck(fullTagPath, val, valueType)
    else:
        # The 'Tag" is either a simple memory tag or an simple OPC tag
        log.trace("Simple write of %s to %s..." % (str(val), fullTagPath))
        if writeConfirm:
            success, errorMessage = writeDatum(fullTagPath, val)
        else:
            success, errorMessage = writeWithNoCheck(fullTagPath, val)

    return success, errorMessage

# Given an OUTPUT recipe data, which generally specifies a write target, get the monitor target.  For example,
# if the recipe data points to a controller, we generally write to the SP and then monitor the PV. 
def getMonitoredTagPath(outputRecipeData, tagProvider):
    from ils.sfc.common.constants import TAG_PATH, VALUE_TYPE, SETPOINT, VALUE

    tagPath = outputRecipeData.get(TAG_PATH)
    tagPath = "[" + tagProvider + "]" + tagPath
    
    valueType = outputRecipeData.get(VALUE_TYPE)
    
    if valueType in [SETPOINT, VALUE]:
        tagPath = tagPath + "/value"
    else:
        print "Unexpected valueType <%s>" % (valueType)

    log.trace("The monitored tag path for valuetype <%s> is: %s" % (valueType, tagPath))
    return tagPath

# Dispatch the RESET command to the appropriate output/controller.  This should work for outputs and  EPKS or TDC3000 controllers.
# This is called from Python and runs in the client.  Because this only resets memory tags and confirmation does not apply, all
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


# Write a value to a simple memory tag, a simple OPC tag, or any of our I/O UDTs. The valueType argument can be omitted if 
# writing to a simple tag.  A write using writeDatum is always confirmed.
# This can run in either the client or the gateway.
# The tagPath should contain the provider.
def writeDatum(tagPath, val, valueType=""):
    log.info("Writing %s to %s, type=%s (writeDatum)" % (str(val), tagPath, str(valueType)))

    success, errorMessage = writer(tagPath, val, valueType)
    
    if success:
        # The write was successful, now confirm the write by reading the value back
        success, errorMessage = simpleWriteConfirm(tagPath, val, valueType)
        if success:
            log.trace("WriteDatum successfully confirmed writing %s to %s" % (str(val), tagPath))
        else:
            log.error("WriteDatum failed to confirm writing %s to %s because %s" % (str(val), str(tagPath), errorMessage))
    else:
        log.error("WriteDatum failed while writing %s to %s because %s" % (str(val), str(tagPath), errorMessage))
        
    return success, errorMessage
        

# Write a value to a simple memory tag, a simple OPC tag, or any of our I/O UDTs. The valueType argument can be omitted if 
# writing to a simple tag.  A write using writeDatum is always confirmed.
# This can run in either the client or the gateway.
# The tagPath should contain the provider.
def writeWithNoCheck(tagPath, val, valueType=""):
    log.info("Writing %s to %s, type=%s (writeWithNoCheck)" % (str(val), tagPath, str(valueType)))

    success, errorMessage = writer(tagPath, val, valueType)
    
    if success:
        log.trace("WriteWithNoCheck successfully wrote %s to %s" % (str(val), str(tagPath)))
    else:
        log.error("WriteWithNoCheck failed while writing %s to %s because %s" % (str(val), str(tagPath), errorMessage))
        
    return success, errorMessage


# This implements the common core write logic.  It is used by both WriteDatum and WriteWithNoCheck.
# The reason for not just making this WriteWithNoCheck is so that I can make distinct log messages.
def writer(tagPath, val, valueType=""):
    errorMessage=""
    tagExists = system.tag.exists(tagPath)
    if not(tagExists):
        return False, "%s does not exist" % (tagPath)
    
    if checkIfUDT(tagPath):
        
        status = system.tag.write(tagPath + '/command', 'RESET')
        if status == 0:
            log.error("ERROR: writing RESET to the command tag for %s" % (tagPath))
            return False, "Failed writing RESET to command tag"
         
        # Give the reset command a chance to complete
        time.sleep(0.5)
        
        if valueType == "":
            # The 'Tag" is one of the OPC Output classes - not a controller
            log.trace("Writing %s to /writeval..." % (str(val)))
            status = system.tag.write(tagPath + '/writeValue', val)
            if status == 0:
                log.error("ERROR: writing %s to the writeValue tag for %s" % (str(val), tagPath))
                return False, "Failed writing %s to writeValue tag" % (str(val))
        else:
            # The 'Tag" is a controller
            payload = {"val": val, "valueType": valueType}
            log.trace("Writing %s to /payload..." % (str(payload)))
            
            status = system.tag.write(tagPath + '/payload', str(payload))
            if status == 0:
                log.error("ERROR: writing %s to the payload tag for %s" % (str(payload), tagPath))
                return False, "Failed writing %s to payload tag" % (str(val))
        
        log.trace("Writing WriteDatum to /command")
        status = system.tag.write(tagPath + '/command', 'WriteDatum')
        if status == 0:
            log.error("ERROR: writing WriteDatum to the command tag for %s" % (tagPath))
            return False, "Failed writing WriteDatum to command tag"
    
        # Without confirming the round trip of the value
        from ils.io.util import waitForWriteComplete
        success, errorMessage = waitForWriteComplete(tagPath)           
    else:
        # The 'Tag" is either a simple memory tag or an simple OPC tag
        log.trace("Simple write of %s to %s..." % (str(val), tagPath))
        status = system.tag.write(tagPath, val)
        if status == 0:
            success = False
            errorMessage = "Write of %s to %s failed immediately" % (str(val), str(tagPath))
        else:
            success = True

    return success, errorMessage


# This does a simple round trip read confirm by reading the value from the tag and comparing it to the value
# that was written.  It does not check that status of the write command.
# Note: There are two ways I could do this, remember that this is running in the client, and the wrapper is
#       independently confirming the write and putting the results into the writeStatus.  But I suppose that 
#       will not work for a memory tag or an OPC tag...  hmmm... seems liek for one of our UDTs this should 
#       just monitor the write status of the UDT but for a simple tag we need to read the value in the tag.
#       For now ALWAYS read the value in the tag. 
def simpleWriteConfirm(tagPath, val, valueType, timeout=60, frequency=1): 
    log = LogUtil.getLogger("com.ils.io")

    if checkIfUDT(tagPath):
        
        if string.upper(valueType) in ["SP", "SETPOINT"]:
            tagRoot = tagPath + '/sp'
        elif string.upper(valueType) in ["OP", "OUTPUT"]:
            tagRoot = tagPath + '/op'
        elif string.upper(valueType) in ["MODE"]:
            tagRoot = tagPath + '/mode'
        else:
            tagRoot = tagPath
        
        fullTagPath = tagRoot + "/value"
        log.trace("Confirming write to a UDT <%s>..." % (fullTagPath))
    else:
        fullTagPath = tagPath
        log.trace("Confirming write to a simple tag <%s>..." % (fullTagPath))

    from ils.io.util import confirmWrite
    confirmation, errorMessage = confirmWrite(fullTagPath, val)

    return confirmation, errorMessage

#    startTime = Date().getTime()
#    delta = (Date().getTime() - startTime) / 1000

#    while (delta < timeout):
#        readbackValue = system.tag.read(fullTagPath).value
#        log.trace("...read value: %s" % (str(readbackValue)))
#        if readbackValue == val:
#            return True, ""

        # Time in seconds
#        time.sleep(frequency)
#        delta = (Date().getTime() - startTime) / 1000

#    log.error("Timed out waiting for write confirmation of %s!" % (fullTagPath))
#    return False, "Timed out waiting for write confirmation"


# This is the equivalent of s88-write-setpoint-ramp in the old system.
# This method makes sequential writes to ramp either the SP or OP of an Experion controller.  
# There is no native output ramping capability in EPKS and this method fills the gap.  
# In addition, it will ramp the SP of a controller that isn't built in G2 as having native EPKS SP Ramp capability.  
# In both cases, the ramp is executed by writing sequentially based on a linear ramp.  
# It assumes that the ramp time is in minutes..   
# TODO - This can't possible be finished...
def writeRamp(controllerTagpath, val, rampTime, updateFrequency, valType, writeConfirm):
    log.info("Writing a controller ramp for %s" % (controllerTagpath))
    payload = {"val": val, "rampTime": rampTime, "updateFrequency": updateFrequency, "writeConfirm": writeConfirm, "valType": valType}
    
    system.tag.write(controllerTagpath + '/payload', payload)
    system.tag.write(controllerTagpath + '/command', 'WRITERAMP')
    
    # The gateway is going to confirm the write whether we want to or not.   If the caller 
    # doesn't care, then don't wait around for the answer
    if writeConfirm:
        # It is going to be a little tough to come up with the exact path to the tag to be confirmed without using some 
        # knowledge of the controller structure
        from ils.io.util import waitForWriteConfirm
        confirmed, errorMessage = waitForWriteConfirm(controllerTagpath)
        return confirmed
    
    return True


# This is the equivalent of s88-confirm-controller-mode in the old system.
# This is a method dispatcher to the method appropriate for the class of controller.
# This is called from Python and runs in the client.
def confirmControllerMode(controllerTagpath, val, testForZero, checkPathToValve, valueType):
    print "In api.checkConfig()"

    # Get the name of the Python class that corresponds to this UDT.
    pythonClass = system.tag.read(controllerTagpath + "/pythonClass").value
    pythonClass = pythonClass.lower() + "." + pythonClass

    # Dynamically create an object (that won't live very long) and then call its reset method
    try:
        cmd = "ils.io." + pythonClass + "('" + controllerTagpath + "')"
        controller = eval(cmd)
        success, errorMessage = controller.confirmControllerMode(val, testForZero, checkPathToValve, valueType)

    except:
        success = False
        errorMessage = "ERROR checking controller configuration to %s, a <%s> (%s)" % (controllerTagpath, pythonClass, traceback.format_exc()) 
        log.error(errorMessage)  

    return success, errorMessage

def validateValueType(valueType):
    # Translate some valueTypes where we use one thing in the UI and another in the UDT
    if string.upper(valueType) in ['SP', 'SETPOINT']:
        valueType = "sp"
    if string.upper(valueType) in ['OP', 'OUTPUT']:
        valueType = "op"
    return valueType

    
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

