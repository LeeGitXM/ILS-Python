'''
Created on Jun 15, 2015

@author: Pete
'''
import system, time, thread
from ils.labData.common import parseTagPath
from ils.labData.common import getDatabaseForTag
from ils.common.util import formatDateTime
from ils.common.error import catchError
from ils.io import recipe
from ils.io.util import writeTag
from system.date import secondsBetween

from ils.log import getLogger
log = getLogger(__name__)

HEADER = ["sampleValue", "sampleTime"]
ADD_VALUE = "addValue"
UPDATE_VALUE = "updateValue"


def resetUnitParameters(tagProvider, recipeFamily):
    '''
    This will reset app of the unit parameters for a given unit.  It relies on the standard naming convention of
    LabData/UNIT.  This is typically called on a grade change.  Updating the configurationChangeTime of a unit parameter
    will trigger processing on that unit parameter; this method does not DIRECTLY initialize the data buffers.
    '''
    log.infof("Resetting unit parameters for family: %s", recipeFamily)
    path = "[%s]LabData/%s" % (tagProvider, recipeFamily)
    browseFilter = {"tagType": "UdtInstance", "typeId": "Lab Data/Unit Parameter", "recursive":True}

    tagPaths=[]
    tagValues=[]
    now = system.date.now()
    
    browseTags = system.tag.browse(path, browseFilter)
    for browseTag in browseTags.getResults():
        tagPaths.append(str(browseTag['fullPath']) + "/configurationChangeTime")
        tagValues.append(now)

    if len(tagPaths) > 0:
        system.tag.writeBlocking(tagPaths, tagValues)

'''
The state of the plant has changed either due to a reactor change or due to to setpoint "Download" or a "No Download".
'''
def configurationChanged(tagPath, currentValue):
    log.infof("Initializing Unit Parameter because the state of the plant has changed: %s", tagPath)
    tagPathRoot, tagName, tagProvider = parseTagPath(tagPath) 

    configurationChangeTime = formatDateTime(currentValue.value)
    log.tracef("The configuration changed at: %s", str(configurationChangeTime))
    
    '''
    Iterate through the data buffer and delete all of the data that is older than the configuration change time
    '''
    tagPath = tagPathRoot + "/buffer"
    vals = system.tag.readBlocking([tagPath])
    buffer = vals[0].value
    
    newVals = []
    for row in range(buffer.rowCount):
        sampleValue = buffer.getValueAt(row, "sampleValue")
        sampleTime = buffer.getValueAt(row, "sampleTime")
        if sampleTime > configurationChangeTime:
            newVals.append([sampleValue, sampleTime])

    ds = system.dataset.toDataSet(HEADER, newVals)
    system.tag.writeBlocking([tagPath], [ds])
    
    log.tracef("Done initializing the buffer!")


'''
The size of the buffer has changed.  We only need to worry about correcting from a large buffer to a small buffer
'''
def bufferSizeChanged(tagPath, previousValue, currentValue, initialChange):
    ''' Not sure we always want to ignore all initial values, we'd really like to check if this initial value has already been received '''
    if initialChange:
        return
    
    log.infof("In %s.bufferSizeChanged - The buffer size has changed for <%s> from <%s> to <%s>", __name__, tagPath, str(previousValue.value), str(currentValue.value))

    tagPathRoot, tagName, tagProvider = parseTagPath(tagPath)
    log.tracef("Root tag path: %s)", tagPathRoot)

    if currentValue.value > previousValue.value:
        log.tracef("...nothing to do since the new value is larger than the old value!")
        return

    if currentValue.value == previousValue.value:
        log.tracef("...nothing to do since the new value is the same as the old value!")
        return

    vals = system.tag.readBlocking([tagPathRoot + "/buffer"])
    buffer = vals[0].value

    rowsToDelete = range(currentValue.value, buffer.rowCount)
    
    buffer = system.dataset.deleteRows(buffer, rowsToDelete)

    #  Calculate the mean - just do brute force, don't worry about overflow
    log.tracef("Recalculating the average...")
    total = 0.0
    for row in range(buffer.rowCount):
        log.tracef("Row: %d - %s", row, str(buffer.getValueAt(row, "sampleValue")))
        total = total + float(buffer.getValueAt(row, "sampleValue"))
    filteredValue = total / buffer.rowCount
    log.tracef("The filtered (average) value is: %s", str(filteredValue))
    
    ''' Write the buffer and updated mean to the UDT '''
    system.tag.writeBlocking([tagPathRoot + "/buffer", tagPathRoot + '/filteredValue'], [buffer, filteredValue])


def valueChanged(tagPath, sampleValue, sampleTime, initialChange, threadName):
    '''
    There is a new value, update the filtered value.  This uses a circular buffer in the database table.    
    '''
    
    ''' Not sure we always want to ignore all initial values, we'd really like to check if this initial value has already been received '''
    if initialChange:
        return
    
    try:
        unitParameter = UnitParameter(tagPath, threadName)
        status = unitParameter.register()
        if status:
            unitParameter.newValue(sampleValue, sampleTime)
            unitParameter.unRegister()
        
    except:
        errorTxt = catchError("%s.valueChanged" % (__name__), "Unit Parameter Handler")
        log.errorf("%s", errorTxt)
        unitParameter.unRegister()


class UnitParameter():
    ''' This is a class level property, one variable that all instances can reference. '''
    tagPathList = []

    def __init__(self, tagPath, threadName):
        ''' Set any default properties.  For this abstract class there aren't many (yet). '''
        tagPathRoot, tagName, tagProvider = parseTagPath(tagPath)
        self.tagPath = str(tagPath)
        self.tagPathRoot = tagPathRoot
        self.tagName = tagName
        self.tagProvider = tagProvider
        self.threadName = str(threadName)

    def __del__(self):
        ''' This is called when the instance is garbage collected, not when I call del(), so I can't use this to do bookkeeping '''
        log.tracef("in delete method...")
        
    def register(self):
        ''' Check for the existence of the tag and the global write flag. '''
        
        log.tracef("Registering <%s> thread: %s - the current list of tags is: %s", self.tagPathRoot, self.threadName, str(UnitParameter.tagPathList))
        
        if self.tagPathRoot in UnitParameter.tagPathList:
            log.tracef("...this UDT is already being processed")
            return False
        
        UnitParameter.tagPathList.append(self.tagPathRoot)
        return True
    
    def unRegister(self):
        if self.tagPathRoot in UnitParameter.tagPathList:
            log.tracef("Unregistering %s...", self.tagPathRoot)
            UnitParameter.tagPathList.remove(self.tagPathRoot)
        
    def newValue(self, sampleValueOriginal, sampleTimeOriginal):
        ''' Check for the existence of the tag and the global write flag. '''
        
        log.infof("In %s.newValue() (%s) with %s - %s...", __name__, self.threadName, str(sampleValueOriginal), str(sampleTimeOriginal))
    
        log.tracef("----------")
        log.tracef("In %s.newValue() with thread: %s", __name__, str(self.threadName))
        log.tracef("   (%s) Tagpath: %s", str(self.threadName), str(self.tagPath))
        log.tracef("   (%s) Value: %s", str(self.threadName), str(sampleValueOriginal))
        log.tracef("   (%s) Sample Time: %s", str(self.threadName), str(sampleTimeOriginal))
    
        # Check the quality here and only process good values.
        if not(sampleValueOriginal.quality.isGood()):
            log.warnf("%s.valueChanged(): Value %s quality is bad - value will not be propagated!", __name__, str(self.tagPath))
            return
    
        # Check the quality here and only process good values.
        if self.threadName in ["rawValue", "sampleTime"] and not(sampleTimeOriginal.quality.isGood()):
            log.warnf("%s.valueChanged(): Sample time %s quality is bad - value will not be propagated!", __name__, str(self.tagPath))
            return
    
        ''' Read the buffer size and bufferindex from the tags '''
        tags = [self.tagPathRoot + '/numberOfPoints', 
                self.tagPathRoot + '/rawValue.LastChange', 
                self.tagPathRoot + '/sampleTime.LastChange', 
                self.tagPathRoot + '/configurationChangeTime',
                self.tagPathRoot + '/ignoreSampleTime',
                self.tagPathRoot + '/buffer',
                "[%s]Configuration/LabData/unitParameterSyncSeconds" % (self.tagProvider)]
    
        vals=system.tag.readBlocking(tags)
    
        numberOfPoints = vals[0].value
        rawValueLastChange = vals[1].value
        sampleTimeLastChange = vals[2].value
        configurationChangeTime = vals[3].value
        ignoreSampleTime = vals[4].value
        buffer = vals[5].value
        syncSeconds = vals[6].value    
    
        log.tracef("(%s) Unit Parameter Configuration: ", str(self.threadName))
        log.tracef("  (%s) Buffer size: %d", str(self.threadName), numberOfPoints)
        log.tracef("  (%s) rawValueLastChange: %s", str(self.threadName), str(rawValueLastChange))
        log.tracef("  (%s) sampleTimeLastChange: %s", str(self.threadName), str(sampleTimeLastChange))
        log.tracef("  (%s) configurationChangeTime: %s", str(self.threadName), str(configurationChangeTime))
        log.tracef("  (%s) ignoreSampleTime: %s", str(self.threadName), str(ignoreSampleTime))
        log.tracef("  (%s) syncSeconds: %s", str(self.threadName), str(syncSeconds))
    
        '''
        If the rawValue and the sampleTime were updated simultaneously then this will be called twice.  So make sure that we didn't just add a 
        value in the last couple of seconds.  Note: It wasn't a problem during testing, but I'm concerned that if we get the sample time value first 
        and then the sample value comes in a couple of seconds later, then we will use the new time with the old value.
        '''
        if not(ignoreSampleTime) and self.threadName in ["rawValue", "sampleTime"]:
            theSecondsBetween = system.date.secondsBetween(rawValueLastChange, sampleTimeLastChange)
            log.tracef("(%s) Seconds between the raw value and the sample time is: %s", str(self.threadName), str(theSecondsBetween))
            if abs(theSecondsBetween) > syncSeconds:
                log.tracef("(%s) The value and sample time are not consistent, waiting for the sync interval", str(self.threadName))
                
                log.tracef("(%s) Sleeping for %s seconds", str(self.threadName), str(syncSeconds))
                time.sleep(syncSeconds)
            
            else:
                log.tracef("(%s) The value and sample time are consistent!", self.threadName)
                
            tags = [self.tagPathRoot + '/rawValue', 
                    self.tagPathRoot + '/sampleTime']

            vals=system.tag.readBlocking(tags)
    
            sampleValue = vals[0].value
            sampleTime = vals[1].value
                
            log.tracef("Refreshed the value and sample time: %s - %s", str(sampleValue), str(sampleTime))
        else:
            sampleValue = sampleValueOriginal.value
            
            '''
            If the value was a manual value, then there isn't a notion of a sample time.  The actual time is passed in as a date,
            not as a qualified value as is normally expected.
            '''
            if self.threadName == "manualRawValue":
                sampleTime = sampleTimeOriginal
            else:
                sampleTime = sampleTimeOriginal.value
                
        ''' We can only process numeric values '''
        try:
            sampleValue = float(sampleValue)
        except:
            # Silently ignore nulls
            if not (sampleValue == None):
                log.warnf("%s.valueChanged(): The new value <%s> for <%s> is not numeric and cannot be processed", __name__, str(sampleValueOriginal.value), self.tagPath)
            return
    
        log.tracef("(%s) Value: %s", str(self.threadName), str(sampleValue))
        log.tracef("(%s) Sample Time: %s", str(self.threadName), str(sampleTime))

        '''
        Ensure that the data is consistent with the current reactor configuration / state.  If the state changed, it is their responsibility to update the 
        configurationChangeTime of the affected Unit Parameters.  If this datum was collected before the time of the state change then do not store it.
        '''
        if system.date.isBefore(sampleTime, configurationChangeTime):
            log.tracef("(%s) ...filtering out %s collected at %s because it was collected before the configuration change time.", str(self.threadName), str(sampleValue), str(sampleTime))
            return
    
        if not( vals[0].quality.isGood() and numberOfPoints != None ):
            log.error("The numberOfPoints tag is bad or has the value None")
            return

        '''
        If just the value was updated, then they are updating a previous value so do not bump the index
        '''
        addOrUpdate = ADD_VALUE
        if not(ignoreSampleTime):
            if buffer.rowCount == 0:
                lastSampleTime = None
                log.tracef("(%s) The data buffer is empty, setting the lastSampleTime to None", str(self.threadName))
            else:
                lastSampleTime = buffer.getValueAt(0, "sampleTime")
                theSecondsBetween = system.date.secondsBetween(sampleTime, lastSampleTime)
                log.tracef("(%s) Comparing the sample time (%s) to the last sample time (%s) to see if an existing value is being updated (delta = %s)", str(self.threadName), str(sampleTime), str(lastSampleTime), str(theSecondsBetween))
                if abs(theSecondsBetween) < 5:
                    log.tracef("(%s) The sample time is the same as the last sample time so overwrite the last value (do not bump the index)", str(self.threadName))
                    addOrUpdate = UPDATE_VALUE

        # Increment the buffer index
        if addOrUpdate == ADD_VALUE:
            log.tracef("(%s) Adding a new value...", str(self.threadName))
            vals = []
            vals.append([sampleValue, sampleTime])
            
            for row in range(buffer.rowCount):
                log.tracef("(%s)   Row: %d", str(self.threadName), row)
                if row < numberOfPoints - 1:
                    log.tracef("(%s) Transferring a point from the old buffer to the new...", str(self.threadName))
                    vals.append([buffer.getValueAt(row, "sampleValue"), buffer.getValueAt(row, "sampleTime")])
            buffer = system.dataset.toDataSet(HEADER, vals)
        else:
            log.tracef("(%s) Updating an existing value...", str(self.threadName))
            buffer = system.dataset.setValue(buffer, 0, "sampleValue", sampleValue)
            buffer = system.dataset.setValue(buffer, 0, "sampleTime", sampleTime)
            
        log.tracef("(%s) Number of points currently in buffer: %d", str(self.threadName), buffer.rowCount)
        
        #  Calculate the mean - just do brute force, don't worry about overflow
        log.tracef("(%s) Calculating the average...", str(self.threadName))
        total = 0.0
        for row in range(buffer.rowCount):
            log.tracef("(%s) Row: %d - %s", str(self.threadName), row, str(buffer.getValueAt(row, "sampleValue")))
            total = total + float(buffer.getValueAt(row, "sampleValue"))
        filteredValue = total / buffer.rowCount
        log.tracef("(%s) The filtered (average) value is: %s", str(self.threadName), str(filteredValue))
        
        # Store the mean into the UnitParameter Final Value
        # These are writing to memory tags so they should be very fast
        tagPaths = []
        tagValues = []
    
        tagPaths.append(self.tagPathRoot + '/filteredValue')
        tagValues.append(filteredValue)
        
        tagPaths.append(self.tagPathRoot + '/buffer')
        tagValues.append(buffer)
        
        log.tracef("(%s) Writing tagPaths: %s", str(self.threadName), str(tagPaths))
        log.tracef("(%s) Writing values: %s", str(self.threadName), str(tagValues))
    
        system.tag.writeBlocking(tagPaths, tagValues)