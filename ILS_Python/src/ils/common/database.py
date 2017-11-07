'''
Created on Jan 5, 2015

@author: Pete
'''
import system
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.SQL")

# Convert the Python Data Set (PDS) to a list of dictionaries 
def toDict(pds):
    records = []
    if len(pds) > 0:    
        ds = system.dataset.toDataSet(pds)
        for row in range(ds.rowCount):
            record={}
            for col in range(ds.columnCount):
                colName=ds.getColumnName(col)
                val=ds.getValueAt(row,col)
                record[colName]=val
            records.append(record)

    # If the dataset was empty then return an empty list
    return records

# Convert the Python Data Set (PDS) to a list of dictionaries 
def toDictList(pds, records):
    if len(pds) > 0:    
        ds = system.dataset.toDataSet(pds)
        for row in range(ds.rowCount):
            record={}
            for col in range(ds.columnCount):
                colName=ds.getColumnName(col)
                val=ds.getValueAt(row,col)
                record[colName]=val
            records.append(record)

    return records

# Lookup the post id given the name
def getConsoleWindowNameForConsole(consoleName, database=""):
    SQL = "select WindowName from TkConsole where ConsoleName = '%s'" % (consoleName)
    log.trace(SQL)
    consoleWindowName = system.db.runScalarQuery(SQL, database)
    return consoleWindowName

# Lookup the post id given the name
def getPostId(post, database=""):
    SQL = "select PostId from TkPost where Post = '%s'" % (post)
    log.trace(SQL)
    postId = system.db.runScalarQuery(SQL, database)
    return postId

# Lookup the unit id given the name
def getUnitId(unitName, database=""):
    SQL = "select UnitId from TkUnit where UnitName = '%s'" % (unitName)
    log.trace(SQL)
    unitId = system.db.runScalarQuery(SQL, database)
    return unitId

# Lookup the unit name given the id
def getUnitName(unitId, database=""):
    SQL = "select UnitName from TkUnit where UnitId = %s" % ( str(unitId) )
    log.trace(SQL)
    unitName = system.db.runScalarQuery(SQL, database)
    return unitName


def lookup(lookupType, key):
    SQL = "select LookupId from Lookup where LookupTypeCode = '%s' and LookupName = '%s'" % (lookupType, key)
    lookupId=system.db.runScalarQuery(SQL)
    return lookupId 

# This is useful when using the " IN " clause in a select statement
# This is meant for ids (or any integer because string would need to be surrounded by single quotes. 
def idListToString(aList):
    aString=""
    for aVal in aList:
        if aString == "":
            aString="%s" % (str(aVal))
        else:
            aString="%s,%s" % (aString, str(aVal))
    return aString

# Convert the Python Data Set (PDS) to a list of dictionaries 
def toList(pds):
    vals = []
    if len(pds) > 0:    
        ds = system.dataset.toDataSet(pds)
        for row in range(ds.rowCount):
            val=ds.getValueAt(row,0)
            vals.append(val)

    # If the dataset was empty then return an empty list
    return vals