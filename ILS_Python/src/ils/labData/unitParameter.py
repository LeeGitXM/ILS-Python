'''
Created on Jun 15, 2015

@author: Pete
'''
import system
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
from com.sun.xml.internal.bind.v2.runtime.unmarshaller import TagName
log = LogUtil.getLogger("com.ils.labData.unitParameters")

def parseTagPath(tagPath):
    end = tagPath.rfind('/')
    tagPathRoot = tagPath[:end]
    end = tagPath.rfind('/')
    tagName = tagPath[end + 1:]
    return tagPathRoot, tagName

# The size of the buffer has changed.  We only need to worry about correcting from a large buffer to a small buffer
def bufferSizeChanged(tagPath, currentValue, initialChange):
    log.info("The buffer size has changed for <%s> to <%s>" % (tagPath, str(currentValue)))
    
    #TODO - Un-hardcode this
    database="XOM"
    
    tagPathRoot, tagName = parseTagPath(tagPath)
    log.trace("In bufferSizeChanged with <%s>, new size = %i (root: %s)" % (tagPath, currentValue.value, tagPathRoot))
    SQL = "select unitParameterId from TkUnitParameter where UnitParameterTagName = '%s'" % (tagPathRoot)
    unitParameterId = system.db.runScalarQuery(SQL, database)
    if unitParameterId == None:
        log.trace("No rows found for %s" % (tagPath))
        return 
    SQL = "Delete from TkUnitParameterBuffer where UnitParameterId = %i and BufferIndex >= %i" % (unitParameterId, currentValue.value)
    rows = system.db.runUpdateQuery(SQL, database)
    log.trace("...deleted %i rows" % rows)
    
def valueChanged(tagPath, currentValue, initialChange):
    
    #TODO - Un-hardcode this
    database="XOM"
    
    # Check the quality here and only process good values.
    if not(currentValue.quality.isGood()):
        log.warn("%s quality is %s - value will not be propagated!" % (tagPath, currentValue.quality))
        return
    
    # We can only process numeric values
    try:
        tagVal = float(currentValue.value)
    except:
        log.warn("The new value <%s> for <%s> is not numeric and cannot be processed" % (str(currentValue.value), tagPath))
        return
    
    # The first step is to get the tag name out of the full tag name.  This should end in either rawValue or manualRawValue    
    tagPathRoot, tagName = parseTagPath(tagPath)
    log.trace("In valueChanged with <%s> and value: %f (root: %s)" % (tagPath, tagVal, tagPathRoot))
    
    # Check if the buffer has ever been initialized
    SQL = "select UnitParameterId from TkUnitParameter where UnitParameterTagName = '%s'" % (tagPathRoot)
    log.trace(SQL)
    unitParameterId = system.db.runScalarQuery(SQL, database)
    if unitParameterId == None:
        SQL = "insert into TkUnitParameter (UnitParameterTagName) values ('%s')" % (tagPathRoot)
        log.trace(SQL)
        unitParameterId = system.db.runUpdateQuery(SQL, database, getKey=1)
        log.info("Inserted a new unit parameter <%s> with id <%i> into the TkUnitParameter" % (tagPathRoot, unitParameterId))
    
    # Read the buffer size and bufferindex from the tags
    
    tags = [tagPathRoot + '/numberOfPoints', tagPathRoot + '/bufferIndex']
    vals=system.tag.readAll(tags)
    numberOfPoints = vals[0].value
    bufferIndex = vals[1].value

    log.trace("Unit Parameter Id: %i - Number of points: %i - Buffer Index: %i" % (unitParameterId, numberOfPoints, bufferIndex))
    
    # Now put the new value into the buffer
    SQL = "update TkUnitParameterBuffer set RawValue = %f "\
        " where UnitParameterId = %i and BufferIndex = %i" % (tagVal, unitParameterId, bufferIndex)
    log.trace(SQL)
    rows=system.db.runUpdateQuery(SQL, database)
    
    # If no rows were updated then it probably means that the buffer has not been filled yet, so insert a row
    if rows == 0:
        SQL = "insert into TkUnitParameterBuffer (UnitParameterId, BufferIndex, RawValue) values (%i, %i, %f)" % (unitParameterId, bufferIndex, tagVal)
        log.trace(SQL)
        rows=system.db.runUpdateQuery(SQL, database)
        if rows != 1:
            log.error("Unable to add value <%f> to the history buffer for tag <%s>" % (tagVal, tagName))
        
    #  Query the buffer for the Mean
    SQL = "select avg(RawValue) from TkUnitParameterBuffer where UnitParameterId = %s" % (str(unitParameterId))
    log.trace(SQL)
    filteredValue = system.db.runScalarQuery(SQL, database)
    log.trace("The filtered value is: %f" % (filteredValue))
    
    # Increment the buffer index so it is ready for the next value
    if bufferIndex >= numberOfPoints - 1:
        bufferIndex = 0
    else:
        bufferIndex = bufferIndex + 1
    
    # Store the mean into the UnitParameter Final Value
    try:
        # These are writing to memory tags so they should be very fast
        system.tag.writeSynchronous(tagPathRoot + '/filteredValue', filteredValue, 1)
        system.tag.writeSynchronous(tagPathRoot + '/bufferIndex', bufferIndex, 1)
        log.trace("Successfully wrote the filtered value <%f> to <%s>" % (filteredValue, tagPath))
    except:
        log.error("Error writing filtered value <%f> to <%s>" % (filteredValue, tagPath))

