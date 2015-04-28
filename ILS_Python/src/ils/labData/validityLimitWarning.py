'''
Created on Mar 31, 2015

@author: Pete
'''
import system

# This is called by the limit checking module.  It sends a message to all of the clients to specify a lab limit
# validity error.
def notify(post, valueName, valueId, rawValue, sampleTime, tagProvider, upperLimit, lowerLimit):
    project = system.util.getProjectName()
    
    # This is the payload that will get passed through to the validity limit window
    payload = {
        "valueId": valueId,
        "valueName": valueName,
        "rawValue": rawValue,
        "sampleTime": sampleTime,
        "upperLimit": upperLimit,
        "lowerLimit": lowerLimit,
        "tagProvider": tagProvider
        }
    print "Packing the payload: ", payload
    ds=system.dataset.toDataSet(["payload"], [[payload]])
    
    # Now make the payload for the OC alert window
    payload = {
        "post": post,
        "topMessage":"Sample value failed validity testing.", 
        "bottomMessage":"Result sample is " + valueName, 
        "buttonLabel":"Acknowledge",
        "callback": "ils.labData.validityLimitWarning.launcher",
        "ds":ds
        }
    print "Payload: ", payload
    system.util.sendMessage(project, "ocAlert", payload, scope="C")


# This is a callback from the Acknowledge button in the middle of the loud workspace.
def launcher(payload):    
    system.nav.openWindow("Lab Data/Validity Limit Warning", payload)

def acceptValue(rootContainer):
    print "Accepting the value"
    
    valueId=rootContainer.valueId
    valueName=rootContainer.valueName
    rawValue=rootContainer.rawValue
    sampleTime=rootContainer.sampleTime
    tagProvider=rootContainer.tagProvider
    database=""
    valid=False
    
    print "valueId: %i, valueName: %s, rawValue: %f, SampleTime: %s, database: %s, provider: %s" % (valueId, valueName, rawValue, sampleTime, database, tagProvider)
    from ils.labData.scanner import storeValue
    storeValue(valueId, valueName, rawValue, sampleTime, database, tagProvider, valid)

def rejectValue():
    print "Rejecting the value"

    