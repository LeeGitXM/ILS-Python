'''
Created on Nov 30, 2014

@author: Pete
'''
import string, system, time, traceback
from ils.io.util import isUDT, getOuterUDT

# These next three lines may have warnings in eclipse, but they ARE needed!
import ils.io
import ils.io.opcoutput
import ils.io.opcconditionaloutput
import ils.io.recipedetail
import ils.io.controller
import ils.io.pkscontroller
import ils.io.pksacecontroller
import ils.io.tdccontroller

log = system.util.getLogger("com.ils.io.api")

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

    if isUDT(fullTagPath):
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

# Given an recipe data specified by the PV Key of the PV monitoring blocks config data, figure out the tag path
# that we are monitoring.  I'm not exactly sure what all of the possibilities are for things in the PV key but I think 
# it must be either an INPUT or OUTPUT recipe data.  So I'm going to use these assumptions:
#  1) If the recipe data is an output then we monitor the value tag of the controller
#  2) If the recipe data is an input then just monitor the tag 
def getMonitoredTagPath(targetStepUUID, pvKey, tagProvider, db):
#    from system.ils.sfc.common.Constants import TAG_PATH

    from ils.sfc.recipeData.api import s88GetRecord
    recipeDataRecord = s88GetRecord(targetStepUUID, pvKey, db)
    recipeDataType = recipeDataRecord["RECIPEDATATYPE"]
    tagPath = recipeDataRecord["TAG"]
    tagPath = "[" + tagProvider + "]" + tagPath

    log.tracef("The monitored item for %s is a %s", pvKey, recipeDataType)

    if string.upper(recipeDataType) == "OUTPUT":
        log.tracef("The recipe data IS an OUTPUT class (for %s)", tagPath)
        outputType = string.upper(recipeDataRecord["OUTPUTTYPE"])
        if outputType == "MODE":
            attributePath = "/mode/value"
        elif outputType == "SETPOINT":
            attributePath = "/value"
        elif outputType == "OUTPUT":
            attributePath = "/op/value"
        else:
            attributePath = "/value"

        tagPath = tagPath + attributePath
    else:
        # this is the default path for just a plain old tag
        pass

    log.trace("The monitored tag path is: %s" % (tagPath))
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
            log.info("   Confirmed writing %s to %s" % (str(val), tagPath))
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

# This is the equivalent of s88-write-setpoint-ramp in the old system.
# This method makes sequential writes to ramp either the SP or OP of a controller.  
# There is no native output ramping capability in EPKS and this method fills the gap.  
# In addition, it will ramp the SP of a controller that isn't built in G2 as having native EPKS SP Ramp capability.  
# In both cases, the ramp is executed by writing sequentially based on a linear ramp.  
# Ramp time is in minutes, update frequency is in seconds.
def writeRamp(tagPath, val, valType, rampTime, updateFrequency, writeConfirm):
    log.info("Writing a controller ramp for %s" % (tagPath))
        
    errorMessage=""
    confirmed = False
    
    tagExists = system.tag.exists(tagPath)
    if not(tagExists):
        return False, "%s does not exist" % (tagPath)
    
    if isUDT(tagPath):
        log.trace("The target is a UDT - resetting...")
        
        # Get the name of the Python class that corresponds to this UDT.
        pyc = system.tag.read(tagPath + "/pythonClass").value
        pkg = "ils.io.%s"%pyc.lower()
        pythonClass = pyc.lower()+"."+pyc

        # Dynamically create an object (that won't live very long)
        try:
            # This requires that I explicitly import everything up above
            cmd = "ils.io." + pythonClass + "('"+tagPath+"')"
            log.trace("Creating a tag object using: <%s>" % (cmd))
            tag = eval(cmd)

            confirmed, errorMessage = tag.writeRamp(val, valType, rampTime, updateFrequency, writeConfirm)

        except:
            reason = "ERROR writing to %s, a <%s> (%s)" % (tagPath, pythonClass, traceback.format_exc()) 
            log.error(reason)
            return False, reason
        
    else:
        # The 'Tag" is either a simple memory tag or an simple OPC tag
        log.error("Ramps have not been implemented to simple tags (%s)..." % (tagPath))
        return False, "Ramps have not been implemented for a simple tag."
    
    return confirmed, errorMessage

# This is an interface for the Recipe Toolkit.  A recipe detail coordinates writes to a controller and 
# guarantees the correct order of writing when the limits and the target all change ensuring that there isn't
# a momentary limit violation.
def writeRecipeDetail(tagPath, newValue, newHighLimit, newLowLimit):
    log.trace("In writeRecipeDetail with %s-%s-%s-%s" % (tagPath, str(newValue), str(newHighLimit),str(newLowLimit)))
      
    errorMessage=""
    success = False
    
    tagExists = system.tag.exists(tagPath)
    if not(tagExists):
        return False, "%s does not exist" % (tagPath)
    
    if isUDT(tagPath):

        # Dynamically create an object (that won't live very long)
        try:
            # This requires that I explicitly import everything up above
            cmd = "ils.io.recipedetail.RecipeDetail('"+tagPath+"')"
            log.trace("Creating a tag object using: <%s>" % (cmd))
            tag = eval(cmd)
                        
            success, errorMessage = tag.writeRecipeDetail(newValue, newHighLimit, newLowLimit)

        except:
            reason = "ERROR writing to %s, a recipeDetail (%s)" % (tagPath, traceback.format_exc()) 
            log.error(reason)
            return False, reason
        
    else:
        success = False
        errorMessage = "WriteRecipeDetail is only appropriate for recipe detail UDTs"

    return success, errorMessage


# This implements the common core write logic.  It is used by both WriteDatum and WriteWithNoCheck.
# The reason for not just making this WriteWithNoCheck is so that I can make distinct log messages.
def writer(tagPath, val, valueType=""):
    log.trace("In writer with %s-%s-%s" % (tagPath, str(val), valueType))
    
    command = "writeDatum"
    
    errorMessage=""
    success = False
    
    tagExists = system.tag.exists(tagPath)
    if not(tagExists):
        return False, "%s does not exist" % (tagPath)
    
    if isUDT(tagPath):
        log.trace("The target is a UDT - resetting...")
        
        # Get the name of the Python class that corresponds to this UDT.
        pyc = system.tag.read(tagPath + "/pythonClass").value
        pythonClass = pyc.lower()+"."+pyc

        # Dynamically create an object (that won't live very long)
        try:
            # This requires that I explicitly import everything up above
            cmd = "ils.io." + pythonClass + "('"+tagPath+"')"
            log.trace("Creating a tag object using: <%s>" % (cmd))
            tag = eval(cmd)
                
            if string.upper(command) == "WRITEDATUM":
                success, errorMessage = tag.writeDatum(val, valueType)
            elif string.upper(command) == "WRITEWITHNOCHECK":
                success, errorMessage = tag.writeWithNoCheck()
            elif string.upper(command) == "WRITERAMP":
                success, errorMessage = tag.writeRamp()
            elif string.upper(command) == "RESET":
                success, errorMessage = tag.reset()
            else:
                errorMessage = "Unrecognized command: "+command
                log.error(errorMessage)
        except:
            reason = "ERROR writing to %s, a <%s> (%s)" % (tagPath, pythonClass, traceback.format_exc()) 
            log.error(reason)
            return False, reason
        
    else:
        # The 'Tag" is either a simple memory tag or an simple OPC tag
        log.trace("Checking the basic configuration for a simple write to %s..." % (tagPath))
        
        # Check that the tag exists and writing is enabled
        from ils.io.util import checkConfig
        configOK, errorMessage = checkConfig(tagPath)
        
        if not(configOK):
            return configOK, errorMessage
        
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
    if isUDT(tagPath):
        pythonClass = system.tag.read(tagPath + "/pythonClass").value
        if pythonClass in ["PKSController", "PKSACEController"]:
            if string.upper(valueType) in ["SP", "SETPOINT"]:
                fullTagPath = tagPath + '/sp/value'
            elif string.upper(valueType) in ["OP", "OUTPUT"]:
                fullTagPath = tagPath + '/op/value'
            elif string.upper(valueType) in ["MODE"]:
                fullTagPath = tagPath + '/mode/value'
        
        elif pythonClass in ["OPCOutput", "OPCTag"]:
            fullTagPath = tagPath + "/value"
        else:
            fullTagPath = tagPath + "/value"
            
        log.trace("Confirming write to a UDT <%s>..." % (fullTagPath))
    else:
        fullTagPath = tagPath
        log.trace("Confirming write to a simple tag <%s>..." % (fullTagPath))

    from ils.io.util import confirmWrite
    confirmation, errorMessage = confirmWrite(fullTagPath, val)

    return confirmation, errorMessage

# This is the equivalent of s88-confirm-controller-mode in the old system.
# This is a method dispatcher to the method appropriate for the class of controller.
# This is called from Python and runs in the client.
# I used to trap errors here, but I think it is best to let errors pass up to a higher level where they can be dealt 
# with better (7/20/16_
def confirmControllerMode(tagpath, val, testForZero, checkPathToValve, valueType):
    log.trace("In %s, checking %s" % (__name__, tagpath))

    controllerUDTType, controllerTagpath=getOuterUDT(tagpath)
    
    if controllerUDTType == None:
        log.trace("The target is not a controller so assume it is reachable")
        return True, "The target is not a Controller"

    log.trace("The UDT is: %s, the path to the UDT is: %s" % (controllerUDTType, controllerTagpath))
    # Get the name of the Python class that corresponds to this UDT.
    pythonClass = system.tag.read(controllerTagpath + "/pythonClass").value
    pythonClass = pythonClass.lower() + "." + pythonClass

    # Dynamically create an object (that won't live very long) and then call its reset method
    cmd = "ils.io." + pythonClass + "('" + controllerTagpath + "')"
    log.trace("Command: %s" % (cmd))
    controller = eval(cmd)
    success, errorMessage = controller.confirmControllerMode(val, testForZero, checkPathToValve, valueType)

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
    fullTagPath='[%s]%s' % (provider, tagPath)
    log.tracef("In getDisplayName(), the full tag path is: %s, the displayAttribute is: %s", fullTagPath, displayAttribute)

    # Check if the tag exists
    tagExists = system.tag.exists(fullTagPath)
    if not(tagExists):
        return "Tag does not exist!"
    
    # Use the last portion of the UDT / tag that we are writing to 
    if string.upper(displayAttribute) == 'NAME':
        displayName=fullTagPath[fullTagPath.rfind('/')+1:]
    
    elif string.upper(displayAttribute) == 'ITEMID':
        log.trace("Using Item Id...")
        # This needs to be smart enough to not blow up if using memory tags (which we will be in isolation)
        if isUDT(fullTagPath):
            pythonClass = system.tag.read(fullTagPath + '/pythonClass').value
            if string.upper(pythonClass) in ["OPCTAG", "OPCConditionalOutput"]:
                displayName = system.tag.read(fullTagPath + '/value.OPCItemPath').value
            elif string.upper(pythonClass) in ["PKSCONTROLLER", "PKSACECONTROLLER"]:
                displayName = system.tag.read(fullTagPath + '/sp//value.OPCItemPath').value
            else:
                raise ValueError, "Unknown I/O class: %s" % (pythonClass)      
        else:
            displayName = system.tag.read(fullTagPath + '.OPCItemPath').value

    else:
        displayName = ''

    return displayName

'''
The purpose of this message handler is to perform the actual write from the gateway even though it is initiated from a client.
There is an impression that writes work better from the gateway and perform faster from a threading point of view than from a client.
The design of this handler is that a list of writes can be sent in a single message and the handler will perform them sequentially.
This handler is not designed to do the writes in parallel, but the most strenuous use case is recipe download which uses 
WriteWithNoCheck which should be a fast operation.  Of course on Mike's real system this might be a problem and some refactoring 
may be required.
'''
def writeMessageHandler(payload):
    command = payload.get("command", "writeDatum")    
    tagList = payload.get("tagList", [])
    log.info("----------------------------------------------------")
    log.info("Handling a %s writeMessage with %i tags" % (command, len(tagList)))
    log.trace("%s" % (str(payload)))
    log.info( "----------------------------------------------------")
    
    for tagDict in tagList:
    
        try:
            log.trace(str(tagDict))
            if command == "writeDatum":
                tagPath = tagDict.get("tagPath", "")
                tagValue = tagDict.get("tagValue", "")
                valueType = tagDict.get("valueType", "value")
                writeDatum(tagPath, tagValue, valueType)
            elif command == "writeWithNoCheck":
                tagPath = tagDict.get("tagPath", "")
                tagValue = tagDict.get("tagValue", "")
                valueType = tagDict.get("valueType", "value")
                writeWithNoCheck(tagPath, tagValue, valueType)
            elif command == "writeRamp":
                tagPath = tagDict.get("tagPath", "")
                tagValue = tagDict.get("tagValue", "")
                valueType = tagDict.get("valueType", "value")
                rampTime = tagDict.get("rampTime", 1.0)
                updateFrequency = tagDict.get("updateFrequency", 1.0)
                writeConfirm = tagDict.get("writeConfirm", True)
                writeRamp(tagPath, tagValue, valueType, rampTime, updateFrequency, writeConfirm)
            elif command == "writeRecipeDetail":
                tagPath = tagDict.get("tagPath", "")
                newValue = tagDict.get("newValue", "")
                newHighLimit = tagDict.get("newHighLimit", "")
                newLowLimit = tagDict.get("newLowLimit", "")
                writeRecipeDetail(tagPath, newValue, newHighLimit, newLowLimit)
            else:
                log.error("Unrecognized command: %s in ils.io.api.writeMessageHandler" % (command))
        except:
            log.error("Caught an error in ils.io.api.writeMessageHandler")
        
        # This is just a short dwell that may or may not be necessary, it definetly seemed to help during 
        # testing from the standpoint of keeping log messages from getting intertwined.
        time.sleep(0.2)
    
    log.info("-------------------------------------------------")
    log.info("   completed writing to %i tags" % (len(tagList)))
    log.info("-------------------------------------------------")
