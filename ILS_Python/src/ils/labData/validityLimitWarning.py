'''
Created on Mar 31, 2015

@author: Pete
'''
import system
from ils.labData.common import postMessage
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.labData.limits")

# This is called by the limit checking module.  It sends a message to all of the clients to specify a lab limit
# validity error.
def notify(post, unitName, valueName, valueId, rawValue, sampleTime, tagProvider, database, upperLimit, lowerLimit):
    
    # Look for a connected operator - if one doesn't exist then automatically accept the value
    foundConsole=False
    pds=system.util.getSessionInfo()
    for record in pds:
        username=record["username"]
        if username==post:
            foundConsole=True
    
    if not(foundConsole):
        txt="The %s - %s - %s lab datum, which failed validity limit checks, was automatically accepted because the %s console was not connected!" % (str(valueName), str(rawValue), str(sampleTime), post)
        log.trace(txt)
        postMessage(txt)
        accept(valueId, unitName, valueName, rawValue, sampleTime, "Failed Validity Auto Accept", tagProvider, database)
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
        "unitName": unitName
        }
    print "Packing the payload: ", payload
    
    topMessage = "Sample value failed validity testing." 
    bottomMessage = "Result sample is " + valueName
    buttonLabel = "Acknowledge"
    callback = "ils.labData.validityLimitWarning.launcher"
    timeoutEnabled = True
    timeoutSeconds = 20

    from ils.common.ocAlert import sendAlert
    sendAlert(project, post, topMessage, bottomMessage, buttonLabel, callback, payload, timeoutEnabled, timeoutSeconds)
    return foundConsole

# This is a callback from the Acknowledge button in the middle of the loud workspace.
def launcher(payload):    
    system.nav.openWindow("Lab Data/Validity Limit Warning", payload)

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

def accept(valueId, unitName, valueName, rawValue, sampleTime, status, tagProvider, database):
    print "Accepting a value which failed validity checks :: valueId: %i, valueName: %s, rawValue: %s, SampleTime: %s, database: %s, provider: %s" % (valueId, valueName, str(rawValue), sampleTime, database, tagProvider)
    
    from ils.labData.scanner import storeValue
    storeValue(valueId, valueName, rawValue, sampleTime, database)
    
    # Update the Lab Data UDT tags 
    tagName="[%s]LabData/%s/%s" % (tagProvider, unitName, valueName)
    
    print "Writing to tag <%s>" % (tagName)
    # The operator has accepted the value so write it and the sample time to the UDT - I'm not sure what should happen to the badValue tag
    tags=[tagName + "/value", tagName + "/sampleTime", tagName + "/badValue", tagName + "/status"]
    tagValues=[rawValue, sampleTime, False, status]
    system.tag.writeAll(tags, tagValues)

# There is nothing that needs to be done if the operator determines that the value is not valid, by doing nothing we ignore 
# the value.
def rejectValue(rootContainer):
    print "Rejecting the value"
    valueName=rootContainer.valueName
    rawValue=rootContainer.rawValue
    sampleTime=rootContainer.sampleTime
    postMessage("The operator rejected %s - %s, which failed validity limit checks, sample time: %s" % (str(valueName), str(rawValue), str(sampleTime)))

# If the operator does not respond to the notification in a timely manner, then by default accept the value.  The burden is on
# the operator to reject the value but the presumption is that the measurement is accurate.
def timeOutValue(rootContainer):
    print "Bad value handling timed out waiting for a decision from the operator"
    acceptValue(rootContainer, True)