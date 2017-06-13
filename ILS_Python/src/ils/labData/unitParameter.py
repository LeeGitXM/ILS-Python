'''
Created on Jun 15, 2015

@author: Pete
'''
import system, time
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
from ils.labData.common import parseTagPath
from ils.labData.common import getDatabaseForTag
from ils.common.util import formatDateTime
from ils.io import recipe

log = LogUtil.getLogger("com.ils.labData.unitParameters")

'''
This will reset app of the unit parameters for a given unit.  It relies on the standard naming convention of
LabData/UNIT.  This is typically called on a grade change.
'''
def resetUnitParameters(tagProvider, recipeFamily):
    print "Resetting unit parameters for family: ", recipeFamily
    browseTags = system.tag.browseTags(parentPath="[%s]LabData/%s" % (tagProvider, recipeFamily), udtParentType="Lab Data/Unit Parameter")
    tagPaths=[]
    tagValues=[]
    now = system.date.now()
    for browseTag in browseTags:
        tagPaths.append(browseTag.fullPath + "/configurationChangeTime")
        tagValues.append(now)

    system.tag.writeAll(tagPaths, tagValues)

'''
The state of the plant has changed either due to a reactor change or due to to setpoint "Download" or a "No Download".
'''
def configurationChanged(tagPath, currentValue):
    log.infof("Initializing Unit Parameter because the state of the plant has changed: %s", tagPath)
    database=getDatabaseForTag(tagPath)
    tagPathRoot, tagName, tagProvider = parseTagPath(tagPath)

    SQL = "select unitParameterId from TkUnitParameter where UnitParameterTagName = '%s'" % (tagPathRoot)
    unitParameterId = system.db.runScalarQuery(SQL, database)
    if unitParameterId == None:
        log.tracef("No rows found for %s", tagPath)
        return 

    configurationChangeTime = formatDateTime(currentValue.value)
    
    SQL = "delete from TkUnitParameterBuffer where UnitParameterId = %i and SampleTime < '%s'" % (unitParameterId, configurationChangeTime)
    rows = system.db.runUpdateQuery(SQL, database)
    log.tracef("...deleted %d rows", rows)


'''
The size of the buffer has changed.  We only need to worry about correcting from a large buffer to a small buffer
'''
def bufferSizeChanged(tagPath, currentValue, initialChange):
    log.infof("The buffer size has changed for <%s> to <%s>", tagPath, str(currentValue))
    database=getDatabaseForTag(tagPath)
    tagPathRoot, tagName, tagProvider = parseTagPath(tagPath)
    log.trace("In bufferSizeChanged with <%s>, new size = %i (root: %s)" % (tagPath, currentValue.value, tagPathRoot))
    SQL = "select unitParameterId from TkUnitParameter where UnitParameterTagName = '%s'" % (tagPathRoot)
    unitParameterId = system.db.runScalarQuery(SQL, database)
    if unitParameterId == None:
        log.tracef("No rows found for %s", tagPath)
        return 
    SQL = "Delete from TkUnitParameterBuffer where UnitParameterId = %i and BufferIndex >= %i" % (unitParameterId, currentValue.value)
    rows = system.db.runUpdateQuery(SQL, database)
    log.tracef("...deleted %d rows", rows)


'''
There is a new value, update the filtered value.  This uses a circular buffer in the database table.    
'''
def valueChanged(tagPath, currentValue, sampleTime, initialChange, threadName):
    '''
    Not sure we always want to ignore all initial values, we'd really like to check if this initial value has already been received
    '''
    if initialChange:
        return
    
    print "----------"
    print threadName, currentValue, sampleTime
    
    database=getDatabaseForTag(tagPath)
    # The database must exist .
    if database==None or len(database)==0:
        log.warnf("labData.unitParameter.valueChanged: Database is empty for %s", tagPath)
        return
    
    # Check the quality here and only process good values.
    if not(currentValue.quality.isGood()):
        log.warnf("Value %s quality is bad - value will not be propagated!", tagPath)
        return
    
    # Check the quality here and only process good values.
    if threadName in ["rawValue", "sampleTime"] and not(sampleTime.quality.isGood()):
        log.warnf("Sample time %s quality is bad - value will not be propagated!", tagPath)
        return
        
    # We can only process numeric values
    try:
        tagVal = float(currentValue.value)
    except:
        # Silently ignore nulls
        if not (currentValue.value == None):
            log.warnf("The new value <%s> for <%s> is not numeric and cannot be processed", str(currentValue.value), tagPath)
        return
    
    # The first step is to get the tag name out of the full tag name.  This should end in either rawValue or manualRawValue    
    tagPathRoot, tagName, tagProvider = parseTagPath(tagPath)
    if tagPathRoot==None or len(tagPathRoot)==0:
        log.warnf("labData.unitParameter.valueChanged: Empty root path for %s", str(tagPath))
        return
    
    '''
    If the rawValue and the sampleTime were updated simultaneously then this will be called twice.  So make sure that we didn't just add a 
    value in the last couple of seconds.  Note: It wasn't a problem during testing, but I'm concerned that if we get the sample time value first 
    and then the sample value comes in a couple of seconds later, then we will use the new time with the old value.
    '''
    if threadName in ["rawValue", "sampleTime"]:
        syncSeconds = system.tag.read("[%s]Configuration/LabData/unitParameterSyncSeconds" % (tagProvider)).value
        time.sleep(syncSeconds)
    
    log.tracef("In valueChanged with <%s> and value: %f (root: %s)", tagPath, tagVal, tagPathRoot)
    
    # Check if the buffer has ever been initialized
    SQL = "select UnitParameterId from TkUnitParameter where UnitParameterTagName = '%s'" % (tagPathRoot)
    log.trace(SQL)
    unitParameterId = system.db.runScalarQuery(SQL, database)
    if unitParameterId == None:
        SQL = "insert into TkUnitParameter (UnitParameterTagName) values ('%s')" % (tagPathRoot)
        log.trace(SQL)
        unitParameterId = system.db.runUpdateQuery(SQL, database, getKey=1)
        log.infof("Inserted a new unit parameter <%s> with id <%d> into the TkUnitParameter", tagPathRoot, unitParameterId)
    
    # Read the buffer size and bufferindex from the tags
    tags = [tagPathRoot + '/numberOfPoints', tagPathRoot + '/bufferIndex', tagPathRoot + '/rawValue.LastChange', tagPathRoot + '/sampleTime.LastChange', tagPathRoot + '/configurationChangeTime']
    vals=system.tag.readAll(tags)

    numberOfPoints = vals[0].value
    bufferIndex = vals[1].value
    rawValueLastChange = vals[2].value
    sampleTimeLastChange = vals[3].value
    configurationChangeTime = vals[4].value
    
    '''
    If the value was a manual value, then there isn't a notion of a sample time.  The acttual time is passed in as a date,
    not as a qualified value as is normally expected.
    '''
    if threadName == "manualRawValue":
        rawValueLastChange = sampleTime
        sampleTimeLastChange = sampleTime
    else:
        sampleTime = sampleTime.value

    secondsBetween = system.date.secondsBetween(rawValueLastChange, sampleTimeLastChange)
    if secondsBetween < 30 and threadName == "sampleTime":
        print "Exiting the SampleTime thread where both the value and sampleTime were updated."
        return
    
    '''
    Ensure that the data is consistent with the current reactor configuration / state.  If the state changed, it is their responsibility to update the 
    configurationChangeTime of the affected Unit Parameters.  If this datum was collected before the time of the state change then do not store it.
    '''
    if system.date.isBefore(sampleTime, configurationChangeTime):
        log.infof("...filtering out %s collected at %s for %s because it was collected before the sample time.", str(tagVal), str(sampleTime.value), tagPath)
        return

    print "Raw value last change:   ", rawValueLastChange
    print "Sample time Last change: ", sampleTimeLastChange

    if not( vals[0].quality.isGood() and numberOfPoints != None ):
        log.error("The numberOfPoints tag is bad or has the value None")
        return

    if not( vals[1].quality.isGood() and bufferIndex != None ):
        log.error("The bufferIndex is bad or has the value None")
        return
    
    bumpIndex = True
    SQL = "select ReceiptTime from TkUnitParameterBuffer where UnitParameterId = %i and BufferIndex = %i" % (unitParameterId, bufferIndex)
    receiptTime = system.db.runScalarQuery(SQL, database)
    if receiptTime <> None:
        log.tracef("The last sample was received at %s", str(receiptTime))
        syncSeconds = system.tag.read("[%s]Configuration/LabData/unitParameterSyncSeconds" % (tagProvider)).value
        if system.date.secondsBetween(receiptTime, system.date.now()) < syncSeconds:
            log.tracef("A lab value has recently processed - update the last value")
            bumpIndex = False

    # Increment the buffer index
    if bumpIndex:
        if bufferIndex >= numberOfPoints - 1:
            bufferIndex = 0
        else:
            bufferIndex = bufferIndex + 1

    log.tracef("Unit Parameter Id: %d - Number of points: %d - Buffer Index: %d", unitParameterId, numberOfPoints, bufferIndex)
    
    # Now put the new value into the buffer
    sampleTime = formatDateTime(sampleTime)
    SQL = "update TkUnitParameterBuffer set RawValue = %f, receiptTime = getdate(), sampleTime = '%s' "\
        " where UnitParameterId = %i and BufferIndex = %i" % (tagVal, sampleTime, unitParameterId, bufferIndex)
    log.trace(SQL)
    rows=system.db.runUpdateQuery(SQL, database)
    
    # If no rows were updated then it probably means that the buffer has not been filled yet, so insert a row
    if rows == 0:
        SQL = "insert into TkUnitParameterBuffer (UnitParameterId, BufferIndex, RawValue, ReceiptTime, SampleTime) "\
            " values (%i, %i, %f, getdate(), '%s')" % (unitParameterId, bufferIndex, tagVal, sampleTime)
        log.trace(SQL)
        rows=system.db.runUpdateQuery(SQL, database)
        if rows != 1:
            log.errorf("Unable to add value <%f> to the history buffer for tag <%s>", tagVal, tagName)
        
    #  Query the buffer for the Mean
    SQL = "select avg(RawValue) from TkUnitParameterBuffer where UnitParameterId = %s" % (str(unitParameterId))
    log.trace(SQL)
    filteredValue = system.db.runScalarQuery(SQL, database)
    log.tracef("The filtered value is: %f", filteredValue)
    
    # Store the mean into the UnitParameter Final Value
    # These are writing to memory tags so they should be very fast
    system.tag.write(tagPathRoot + '/filteredValue', filteredValue, 1)
    system.tag.write(tagPathRoot + '/bufferIndex', bufferIndex, 1)
    log.tracef("Successfully wrote the filtered value <%f> to <%s>", filteredValue, tagPath)
