'''
Functions that are shared by custom and pre-defined steps

Created on Oct 30, 2014

@author: rforbes
'''

import ils.sfc.gateway.util
from ils.common.units import Unit
from ils.sfc.common.util import handleUnexpectedError

UNIT = '.unit'

def s88Get(chartProperties, stepProperties, ckey, location, create = False):
    return s88GetWithUnits(chartProperties, stepProperties, ckey, location, create)

def s88GetWithUnits(chartProperties, stepProperties, ckey, location, newUnitNameOrNone, create = False):
    # Get the properties dictionary from the proper location
    # ? is SUPERIOR always just one level?
    from ils.sfc.common.constants import DATABASE
    value = ils.sfc.gateway.util.getPropertiesByLocation(chartProperties, stepProperties, location, create)
    # get value via the key path:
    keys = ckey.split('.')
    for key in keys:
        parent = value
        finalKey = key
        value = value.get(key, None)
        if value == None:
            if create:
                value = dict()
                parent[key] = dict()
            else:
                handleUnexpectedError("null value at key %s in property %s", key, ckey)
                return None
    # Do unit conversion if necessary:
    if newUnitNameOrNone != None:
        existingUnitName = parent.get(finalKey + UNIT, None)
        if existingUnitName != None:
            if existingUnitName != newUnitNameOrNone:
                database = chartProperties[DATABASE]
                existingUnit = Unit.getUnit(existingUnitName, database)
                newUnit = Unit.getUnit(newUnitNameOrNone, database)
                if existingUnit != None and newUnit != None:
                    value = existingUnit.convertTo(newUnit, value)
                else:
                    handleUnexpectedError("No unit found for %s and/or %s", existingUnitName, newUnitNameOrNone)                   
        else:
            handleUnexpectedError("No unit found for property %s when new unit %s was requested", ckey, newUnitNameOrNone)
    return value

def s88Set(chartProperties, stepProperties, ckey, value, location, createIfAbsent = False):
    s88SetWithUnits(chartProperties, stepProperties, ckey, value, location, None, createIfAbsent)
    
def s88SetWithUnits(chartProperties, stepProperties, ckey, value, location, unitsOrNone, createIfAbsent):
    '''
    Set data at the given location with a possible compound (dot-separated) key.
    Intermediate layers in a dot-separated path will be created if not present.
    If units are given, store them as well
    '''
    # Get the properties dictionary from the proper location
    props = ils.sfc.gateway.util.getPropertiesByLocation(chartProperties, stepProperties, location, createIfAbsent)
    # set value via the key path, creating intermediate levels if necessary:
    keys = ckey.split('.')
    finalKey = keys.pop()
    for key in keys:
        subProps = props.get(key, None)
        if subProps == None:
            subProps = dict()
            props[key] = subProps
        props = subProps
    if not (createIfAbsent or props.has_key(finalKey)):
        raise KeyError('key ' + location + ": " +  ckey + "does not exist")
    props[finalKey] = value
    if unitsOrNone != None:
        props[finalKey + UNIT] = unitsOrNone
        
def pauseChart(chartProperties):
    from system.sfc import pauseChart
    from ils.sfc.common.constants import PAUSED, INSTANCE_ID
    from ils.sfc.common.sessions import updateSessionStatus
    chartRunId = str(chartProperties[INSTANCE_ID])
    pauseChart(chartRunId)
    updateSessionStatus(chartProperties, PAUSED)
    
def resumeChart(chartProperties):
    from system.sfc import resumeChart
    from ils.sfc.common.constants import RUNNING, INSTANCE_ID
    from ils.sfc.common.sessions import updateSessionStatus
    chartRunId = str(chartProperties[INSTANCE_ID])
    resumeChart(chartRunId)
    updateSessionStatus(chartProperties, RUNNING)

def cancelChart(chartProperties):
    from system.sfc import cancelChart
    from ils.sfc.common.constants import CANCELED, INSTANCE_ID
    from ils.sfc.common.sessions import updateSessionStatus
    chartRunId = str(chartProperties[INSTANCE_ID])
    cancelChart(chartRunId)
    updateSessionStatus(chartProperties, CANCELED)
