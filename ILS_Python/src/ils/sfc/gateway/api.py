'''
Functions that are shared by custom and pre-defined steps

Created on Oct 30, 2014

@author: rforbes
'''

from ils.common.units import Unit
from ils.sfc.gateway.util import handleUnexpectedGatewayError

UNIT = '.unit'

def s88Get(chartProperties, stepProperties, ckey, location, create = False):
    return s88GetWithUnits(chartProperties, stepProperties, ckey, location, None, create)

def s88GetWithUnits(chartProperties, stepProperties, ckey, location, newUnitNameOrNone, create = False):
    from ils.sfc.gateway.recipe import getRecipeScope, pathGet
    scopeDict = getRecipeScope(chartProperties, stepProperties, location)
    value = pathGet(scopeDict, ckey)
    existingUnitName = None
    # TODO: fix the unit access
    # Do unit conversion if necessary:
    if newUnitNameOrNone != None:
        if existingUnitName != None:
            if existingUnitName != newUnitNameOrNone:
                existingUnit = Unit.getUnit(existingUnitName)
                newUnit = Unit.getUnit(newUnitNameOrNone)
                if existingUnit != None and newUnit != None:
                    value = existingUnit.convertTo(newUnit, value)
                else:
                    handleUnexpectedGatewayError(chartProperties, "No unit found for %s and/or %s" % (existingUnitName, newUnitNameOrNone))                   
        else:
            handleUnexpectedGatewayError(chartProperties, "No unit found for property %s when new unit %s was requested" % (ckey, newUnitNameOrNone))
    return value

def s88Set(chartProperties, stepProperties, ckey, value, location, createIfAbsent = False):
    s88SetWithUnits(chartProperties, stepProperties, ckey, value, location, None, createIfAbsent)
    
def s88SetWithUnits(chartProperties, stepProperties, ckey, value, location, unitsOrNone, createIfAbsent):
    '''
    Set data at the given location with a possible compound (dot-separated) key.
    Intermediate layers in a dot-separated path will be created if not present.
    If units are given, store them as well
    '''
    from ils.sfc.gateway.recipe import getRecipeScope, pathSet
    scopeDict = getRecipeScope(chartProperties, stepProperties, location)
    value = pathSet(scopeDict, ckey, value)
        
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
