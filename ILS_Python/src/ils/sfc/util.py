'''
Created on Sep 30, 2014

@author: rforbes
'''
import system.util
from system.ils.sfc import *
from ils.common.units import Unit
import logging

logger = logging.getLogger('ilssfc')

# Chart states:
Aborted = 0
Aborting = 1
Canceled = 2
Canceling = 3
Initial = 4
Paused = 5
Pausing = 6
Resuming = 7
Running = 8
Starting = 9
Stopped = 10
Stopping = 11
    
# Chart scope keys
MESSAGE_QUEUE = 'messageQueue'
PARENT_SCOPE = 'chart.parent'
CHART_STATE = 'chart.state'
PROJECT = 'project'
DATABASE = 'database'
RESPONSE = 'response'
LOCATION = 'location'
BY_NAME = 'byName'
UNIT = '.unit'
INSTANCE_ID = 'instanceId'

# client message handlers
SHOW_QUEUE_HANDLER = 'sfcShowQueue'
YES_NO_HANDLER = 'sfcYesNo'
CONTROL_PANEL_MSG_HANDLER = 'sfcControlPanelMessage'
TIMED_DELAY_HANDLER = 'sfcTimedDelay'

counter = 0

def s88Get(stepName, chartProperties, ckey, location):
    return s88GetWithUnits(stepName, chartProperties, ckey, location, None)

def s88GetWithUnits(stepName, chartProperties, ckey, location, newUnitNameOrNone):
    # Get the properties dictionary from the proper location
    value = getPropertiesByLocation(stepName, chartProperties, location)
    # get value via the key path:
    keys = ckey.split('.')
    for key in keys:
        parent = value
        finalKey = key
        value = property.get(key, None)
        if value == None:
            logger.warn("null value at key %s in property %s in step %s", key, ckey, stepName)
            return None
    # Do unit conversion if necessary:
    if newUnitNameOrNone != None:
        existingUnitName = parent.get(finalKey + UNIT, None)
        if existingUnitName != None:
            if existingUnitName != newUnitNameOrNone:
                existingUnit = Unit.getUnit(existingUnitName)
                newUnit = Unit.getUnit(newUnitNameOrNone)
                if existingUnit != None and newUnit != None:
                    value = existingUnit.convertTo(newUnit, value)
                else:
                    logger.error("No unit found for %s and/or %s", existingUnitName, newUnitNameOrNone)                   
        else:
            logger.error("No unit found for property %s in step %s when new unit %s was requested", ckey, stepName, newUnitNameOrNone)
    return value

def s88Set(stepName, chartProperties, ckey, value, location):
    s88SetWithUnits(stepName, chartProperties, ckey, value, location, None)
    
def s88SetWithUnits(stepName, chartProperties, ckey, value, location, unitsOrNone):
    '''
    Set data at the given location with a possible compound (dot-separated) key.
    Intermediate layers in a dot-separated path will be created if not present.
    If units are given, store them as well
    '''
    # Get the properties dictionary from the proper location
    props = getPropertiesByLocation(stepName, chartProperties, location)
    # set value via the key path, creating intermediate levels if necessary:
    keys = ckey.split('.')
    finalKey = keys.pop()
    for key in keys:
        subProps = props.get(key, None)
        if subProps == None:
            subProps = dict()
            props[key] = subProps
        props = subProps
    props[finalKey] = value
    if unitsOrNone != None:
        props[finalKey + UNIT] = unitsOrNone

def printCounter():
    global counter
    print counter
    counter = counter + 1
    
def getWithPath(properties, key):
    '''
    Get a value using a potentially compound key
    '''
    
def getPropertiesByLocation(stepName, chartProperties, location):
    '''
    Get the property dictionary of the element at the given location.
    '''
    if location == SUPERIOR:
        return chartProperties[PARENT_SCOPE]       
    elif location == PROCEDURE or location == PHASE or location == OPERATION:
        return getPropertiesByLevel(chartProperties, location)
    elif location == LOCAL:
        props = chartProperties[BY_NAME].get(stepName, None)
        if props == None:
            props = dict()
            chartProperties[BY_NAME][stepName] = props
        return props
    elif location == NAMED:
        return chartProperties[BY_NAME]
    elif location == PREVIOUS:
        return chartProperties[BY_NAME].get(PREVIOUS, None)
    else:
        logger.error("unknown property location type %s", location)
        
def getPropertiesByLevel(chartProperties, location):
    ''' Use of PROCEDURE, PHASE, and OPERATION depends on the charts at
        those levels setting the LOCATION property 
    '''
    thisLocation = chartProperties.get(LOCATION, None)
    if location == thisLocation:
        return chartProperties
    else:
        parentProperties = chartProperties[PARENT_SCOPE]
        if parentProperties != None:
            return getPropertiesByLevel(parentProperties, location)
        else:
            return None
        
def createUniqueId():
    '''
    create a unique id
    '''
    import uuid
    return str(uuid.uuid4())
    
def sendMessage(project, handler, payload):
    # TODO: check returned list of recipients
    # TODO: restrict to a particular client session
    messageId = createUniqueId()
    payload[MESSAGE_ID] = messageId
    print 'sending message to clients', project, handler
    system.util.sendMessage(project, handler, payload, "C")
    return messageId
    
def getStepProperty(stepProperties, pname):
    # Why isn't there a dictionary so we don't have to loop ?!
    for prop in stepProperties.getProperties():
        if prop.getName() == pname:
            return stepProperties.getOrDefault(prop)
    return None

def transferStepPropertiesToMessage(stepProperties, payload):
    for prop in stepProperties.getProperties():
        payload[prop.getName()] = prop.getValue()
 
def waitOnResponse(requestId, chartScope):
    '''
    Sleep until a response to the given request
    has been received. Callers should be
    prepared for a None return, which means
    the chart has been canceled/paused/aborted
    '''
    import time
    response = None
    while response == None:
        time.sleep(10);
        # chartState = chartScope[CHART_STATE]
        # if chartState == Canceling or chartState == Pausing or chartState == Aborting:
            # TODO: log that we're bailing
        # return None
        response = getResponse(requestId)
    return response

def sendResponse(requestPayload, responsePayload):
    '''
    This method is called from CLIENT scope to 
    send a reply to the Gateway
    '''
    messageId = requestPayload[MESSAGE_ID]
    responsePayload[MESSAGE_ID] = messageId    
    project = system.util.getProjectName()
    system.util.sendMessage(project, RESPONSE_HANDLER, responsePayload, "G")
    
def sendControlPanelMessage(chartProperties, stepProperties):
    payload = dict()
    transferStepPropertiesToMessage(stepProperties,payload)
    project = chartProperties[PROJECT];
    sendMessage(project, CONTROL_PANEL_MSG_HANDLER, payload)
