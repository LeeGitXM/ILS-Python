'''
Created on Aug 1, 2015

@author: Pete
'''
import system
from ils.labData.common import postMessage
from ils.common.ocAlert import sendAlert
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.labData.limits")

#------------------------------
# Custom Validation Failure
#------------------------------

# This is called by the limit checking module.  It sends a message to all of the clients to specify a lab limit
# validity error.
def notifyCustomValidationViolation(post, unitName, valueName, valueId, rawValue, sampleTime, tagProvider, database):
    
    # Look for a connected operator - if one doesn't exist then automatically accept the value
    foundConsole=False
    pds=system.util.getSessionInfo()
    for record in pds:
        username=record["username"]
        if username==post:
            foundConsole=True
    
    if not(foundConsole):
        txt="The %s - %s - %s lab datum, which failed release limit checks, was automatically accepted because the %s console was not connected!" % (str(valueName), str(rawValue), str(sampleTime), post)
        log.trace(txt)
        postMessage(txt)
        accept(valueId, unitName, valueName, rawValue, sampleTime, "Failed Validity Limit Auto Accept", tagProvider, database)
        return foundConsole
    
    # The console is connected, so post the alert window.
    project = system.util.getProjectName()
    
    # This is the payload that will get passed through to the validity limit window
    payload = {
        "valueId": valueId,
        "valueName": valueName,
        "rawValue": rawValue,
        "sampleTime": sampleTime,
        "tagProvider": tagProvider,
        "unitName": unitName,
        "limitType": "validity"
        }
    print "Packing the payload: ", payload
    
    topMessage = "Sample value failed validity testing." 
    bottomMessage = "Result sample is " + valueName
    mainMessage = ""
    buttonLabel = "Acknowledge"
    callback = "ils.labData.limitWarning.validityLimitActionLauncher"
    timeoutEnabled = True
    timeoutSeconds = 20

    sendAlert(project, post, topMessage, bottomMessage, mainMessage, buttonLabel, callback, payload, timeoutEnabled, timeoutSeconds)
    return foundConsole

# This is a callback from the Acknowledge button in the middle of the loud workspace.
def customValidationActionLauncher(event, payload):
    system.nav.closeParentWindow(event)    
    system.nav.openWindow("Lab Data/Custom Validation Limit Warning", payload)

#------------------------------
# Validity Limits
#------------------------------

# This is called by the limit checking module.  It sends a message to all of the clients to specify a lab limit
# validity error.
def notifyValidityLimitViolation(post, unitName, valueName, valueId, rawValue, sampleTime, tagProvider, database, upperLimit, lowerLimit):
    
    # Look for a connected operator - if one doesn't exist then automatically accept the value
    foundConsole=False
    pds=system.util.getSessionInfo()
    for record in pds:
        username=record["username"]
        if username==post:
            foundConsole=True
    
    if not(foundConsole):
        txt="The %s - %s - %s lab datum, which failed release limit checks, was automatically accepted because the %s console was not connected!" % (str(valueName), str(rawValue), str(sampleTime), post)
        log.trace(txt)
        postMessage(txt)
        accept(valueId, unitName, valueName, rawValue, sampleTime, "Failed Validity Limit Auto Accept", tagProvider, database)
        return foundConsole
    
    # The console is connected, so post the alert window.
    project = system.util.getProjectName()
    
    # This is the payload that will get passed through to the validity limit window
    payload = {
        "valueId": valueId,
        "valueName": valueName,
        "rawValue": rawValue,
        "sampleTime": sampleTime,
        "upperLimit": upperLimit,
        "lowerLimit": lowerLimit,
        "tagProvider": tagProvider,
        "unitName": unitName,
        "limitType": "validity"
        }
    print "Packing the payload: ", payload
    
    topMessage = "Sample value failed validity testing." 
    bottomMessage = "Result sample is " + valueName
    mainMessage = ""
    buttonLabel = "Acknowledge"
    callback = "ils.labData.limitWarning.validityLimitActionLauncher"
    timeoutEnabled = True
    timeoutSeconds = 20

    sendAlert(project, post, topMessage, bottomMessage, mainMessage, buttonLabel, callback, payload, timeoutEnabled, timeoutSeconds)
    return foundConsole



# This is a callback from the Acknowledge button in the middle of the loud workspace.
def validityLimitActionLauncher(event, payload):
    system.nav.closeParentWindow(event)    
    system.nav.openWindow("Lab Data/Validity Limit Warning", payload)

#------------------
# Release Limits
#------------------

# This is called by the limit checking module.  It sends a message to all of the clients to specify a lab limit
# validity error.
def notifyReleaseLimitViolation(post, unitName, valueName, valueId, rawValue, sampleTime, tagProvider, database, upperLimit, lowerLimit):
    
    # Look for a connected operator - if one doesn't exist then automatically accept the value
    foundConsole=False
    pds=system.util.getSessionInfo()
    for record in pds:
        username=record["username"]
        if username==post:
            foundConsole=True
    
    if not(foundConsole):
        txt="The %s - %s - %s lab datum, which failed release limit checks, was automatically accepted because the %s console was not connected!" % (str(valueName), str(rawValue), str(sampleTime), post)
        log.trace(txt)
        postMessage(txt)
        accept(valueId, unitName, valueName, rawValue, sampleTime, "Failed Release Limit Auto Accept", tagProvider, database)
        return foundConsole
    
    # The console is connected, so post the alert window.
    project = system.util.getProjectName()
    
    # This is the payload that will get passed through to the validity limit window
    payload = {
        "valueId": valueId,
        "valueName": valueName,
        "rawValue": rawValue,
        "sampleTime": sampleTime,
        "upperLimit": upperLimit,
        "lowerLimit": lowerLimit,
        "tagProvider": tagProvider,
        "unitName": unitName,
        "limitType": "release"
        }
    print "Packing the payload: ", payload
    
    topMessage = "Sample value failed release limit validation." 
    bottomMessage = "Result sample is " + valueName
    mainMessage = ""
    buttonLabel = "Acknowledge"
    callback = "ils.labData.limitWarning.releaseLimitActionLauncher"
    timeoutEnabled = True
    timeoutSeconds = 20

    sendAlert(project, post, topMessage, bottomMessage, mainMessage, buttonLabel, callback, payload, timeoutEnabled, timeoutSeconds)
    return foundConsole

# This is a callback from the Acknowledge button in the middle of the loud workspace.
def releaseLimitActionLauncher(event, payload):
    system.nav.closeParentWindow(event)    
    system.nav.openWindow("Lab Data/Release Limit Warning", payload)
#-----------------
# Common for both validity limits and release limits
#-----------------

# This is called when the operator presses the accept button on the operator review screen or when that dialog times out.
def acceptValue(rootContainer, timeout=False):
    print "Accepting the value"
    
    valueId=rootContainer.valueId
    valueName=rootContainer.valueName
    rawValue=rootContainer.rawValue
    sampleTime=rootContainer.sampleTime
    tagProvider=rootContainer.tagProvider
    unitName=rootContainer.unitName
    database=""
    
    if timeout:
        postMessage("The value was accept because of a timeout waiting for an operator response %s - %s, which failed validity limit checks, sample time: %s" % (str(valueName), str(rawValue), str(sampleTime)))
    else:
        postMessage("The operator accepted %s - %s, which failed validity limit checks, sample time: %s" % (str(valueName), str(rawValue), str(sampleTime)))

    accept(valueId, unitName, valueName, rawValue, sampleTime, "Failed Validity Operator Accept", tagProvider, database)

#
# This is called when the operator presses the "Accept With UIR" button on the operator review screen or when that dialog times out.
def acceptValueWithUIR(rootContainer, timeout=False):
    print "Accepting the value and creating a UIR"
    
    valueId=rootContainer.valueId
    valueName=rootContainer.valueName
    rawValue=rootContainer.rawValue
    sampleTime=rootContainer.sampleTime
    tagProvider=rootContainer.tagProvider
    unitName=rootContainer.unitName
    database=""
    
    if timeout:
        postMessage("The value was accept because of a timeout waiting for an operator response %s - %s, which failed validity limit checks, sample time: %s" % (str(valueName), str(rawValue), str(sampleTime)))
    else:
        postMessage("The operator accepted %s - %s, which failed validity limit checks, sample time: %s" % (str(valueName), str(rawValue), str(sampleTime)))

    accept(valueId, unitName, valueName, rawValue, sampleTime, "Failed Validity Operator Accept", tagProvider, database)
    
    # The post is the same as the username
    post=system.security.getUsername()
    
    import ils.common.grade as grade
    grade = grade.get()
     
    window = system.nav.openWindow('UIR Vistalon/UIR Entry', {'post' : post, 'editable' : 'True', 'grade' : grade})
    system.nav.centerWindow(window)


def accept(valueId, unitName, valueName, rawValue, sampleTime, status, tagProvider, database):
    print "Accepting a value which failed validity checks :: valueId: %i, valueName: %s, rawValue: %s, SampleTime: %s, database: %s, provider: %s" % (valueId, valueName, str(rawValue), sampleTime, database, tagProvider)
    
    from ils.labData.scanner import storeValue
    storeValue(valueId, valueName, rawValue, sampleTime, unitName, log, tagProvider, database)
        
    # Update the Lab Data UDT tags 
    tagName="[%s]LabData/%s/%s" % (tagProvider, unitName, valueName)

    # The operator has accepted the value so write it and the sample time to the UDT - I'm not sure what should happen to the badValue tag
    system.tag.write(tagName + "/value", rawValue)
    system.tag.write(tagName + "/sampleTime", sampleTime)
    system.tag.write(tagName + "/badValue", False)
    system.tag.write(tagName + "/status", status)


# There is nothing that needs to be done if the operator determines that the value is not valid, by doing nothing we ignore 
# the value.
def rejectValue(rootContainer):
    print "Rejecting the value"
    valueName=rootContainer.valueName
    rawValue=rootContainer.rawValue
    sampleTime=rootContainer.sampleTime
    tagProvider=rootContainer.tagProvider
    unitName=rootContainer.unitName

    postMessage("The operator rejected %s - %s, which failed validity limit checks, sample time: %s" % (str(valueName), str(rawValue), str(sampleTime)))

    # Update the Lab Data UDT tags 
    tagName="[%s]LabData/%s/%s" % (tagProvider, unitName, valueName)
    
    print "Writing to tag <%s>" % (tagName)
    #  The operator has accepted the value so write it and the sample time to the UDT - I'm not sure what should happen to the badValue tag
    system.tag.write(tagName + "/badValue", True)
    system.tag.write(tagName + "/status", "Operator rejected value")    


# If the operator does not respond to the notification in a timely manner, then by default accept the value.  The burden is on
# the operator to reject the value but the presumption is that the measurement is accurate.
def timeOutValue(rootContainer):
    print "Bad value handling timed out waiting for a decision from the operator"
    acceptValue(rootContainer, True)