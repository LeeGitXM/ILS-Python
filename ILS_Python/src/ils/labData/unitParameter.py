'''
Created on Jun 15, 2015

@author: Pete
'''
import system
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.labData.unitParameters")

def valueChanged(tagPath, currentValue, initialChange):
    # We could/should check the quality here and only process good values.
    log.trace("In valueChanged with <%s> and value: %f " % (tagPath, currentValue.value))
    database="XOM"
    
    # The first step is to get the tag name out of the tagpath.  This should end in either rawValue or manualRawValue
    end = tagPath.rfind('/')
    tagPath = tagPath[:end]
    end = tagPath.rfind('/')
    tagPathRoot = tagPath[:end]
    tagName = tagPath[end + 1:]
    
    # Check if the buffer has ever been initialized
    SQL = "select UnitParameterId, BufferSize, BufferIndex from TkUnitParameter where UnitParameterName = '%s'" % (tagName)
    log.trace(SQL)
    pds = system.db.runQuery(SQL, database)
    if len(pds) == 0:
        log.error("Error: The unit parameter <%s> was not found in the TkUnitParameter table!" % (tagName))
        return
    
    record = pds[0]
    unitParameterId = record['UnitParameterId']
    bufferSize = record['BufferSize']
    bufferIndex = record['BufferIndex']
    
    log.trace("Unit Parameter Id: %i - Buffer Size: %i - Buffer Index: %i" % (unitParameterId, bufferSize, bufferIndex))
    
    # Now put the new value into the buffer
    SQL = "update TkUnitParameterBuffer set RawValue = %f "\
        " where UnitParameterId = UnitParameterId and BufferIndex = %i" % (currentValue.value, bufferIndex)
    log.trace(SQL)
    system.db.runUpdateQuery(SQL, database)
    
    # Query the buffer for the Mean
    SQL = "select avg(RawValue) from TkUnitParameterBuffer where UnitParameterId = %s" % (str(unitParameterId))
    log.trace(SQL)
    filteredValue = system.db.runScalarQuery(SQL, database)
    log.trace("The filtered value is: %f" % (filteredValue))
    
    # Increment the buffer index so it s ready for the next value
    if bufferIndex >= bufferSize - 1:
        bufferIndex = 0
    else:
        bufferIndex = bufferIndex + 1
        
    SQL = "update TkUnitParameter set BufferIndex = %s where UnitParameterId = %s" % (str(bufferIndex), str(unitParameterId))
    log.trace(SQL)
    system.db.runUpdateQuery(SQL, database)
    
    # Store the mean into the UnitParameter Final Value
    tagPath = tagPathRoot + '/' + tagName + '/filteredValue'
    retVal = system.tag.write(tagPath, filteredValue)
    if retVal == 1:
        log.trace("Successfully wrote the filtered value <%f> to <%s>" % (filteredValue, tagPath))
    elif retVal == 0:
        log.error("Error writing filtered value <%f> to <%s>" % (filteredValue, tagPath))
    else:
        log.warn("Error writing filtered value <%f> to <%s>" % (filteredValue, tagPath))
