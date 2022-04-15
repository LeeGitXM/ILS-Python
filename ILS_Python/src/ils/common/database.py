'''
Created on Jan 5, 2015

@author: Pete
'''
import system

from ils.log import getLogger
log = getLogger(__name__)

def version():
    SQL = "select VersionId, Version, ReleaseDate from Version where VersionId = (select MAX(VersionId) from Version)"
    pds = system.db.runQuery(SQL)
    record = pds[0]
    version = record["Version"]
    releaseDate = record["ReleaseDate"]
    releaseDate = system.date.format(releaseDate, "MMMM d, yyyy")
    return version, releaseDate

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

def toDateString(aDate):
    ''' Format a datetime value into a string that is compatible with SQLServers automatic string to date conversion '''
    
    aDateString = system.date.format(aDate,"yyyy-MM-dd HH:mm:ss")
    return aDateString

def getConsoleWindowNameForConsole(consoleName, database=""):
    ''' Lookup the post id given the name '''
    SQL = "select WindowName from TkConsole where ConsoleName = '%s'" % (consoleName)
    log.trace(SQL)
    consoleWindowName = system.db.runScalarQuery(SQL, database)
    return consoleWindowName

def getConsoleWindowNameForPost(post, database=""):
    ''' Lookup the post id given the name '''
    SQL = "select WindowName from TkConsole C, TkPost P "\
        "where P.Post = '%s' and P.PostId = C.PostId" % (post)
    log.trace(SQL)
    consoleWindowName = system.db.runScalarQuery(SQL, database)
    return consoleWindowName

# Lookup the post id given the name
def getPostId(post, database=""):
    SQL = "select PostId from TkPost where Post = '%s'" % (post)
    log.trace(SQL)
    postId = system.db.runScalarQuery(SQL, database)
    return postId

def getPostForUnitId(unitId, database=""):
    '''
    Lookup the post id and name for a given unit id
    '''
    SQL = "select PostId, Post from TkPost P, TkUnit U "\
        "where U.PostId = P.PostId "\
        " and U.UnitId = %d" % (unitId)
    log.trace(SQL)
    pds = system.db.runQuery(SQL, database)
    
    if len(pds) == 0 or len(pds) > 1:
        return None, None
    record = pds[0]
    return record["PostId"], record["Post"]

# Lookup the unit id given the name
def getUnitId(unitName, database=""):
    SQL = "select UnitId from TkUnit where UnitName = '%s'" % (unitName)
    log.trace(SQL)
    unitId = system.db.runScalarQuery(SQL, database)
    return unitId

# Lookup the unit name given the id
def getUnitName(unitId, database=""):
    SQL = "select UnitName from TkUnit where UnitId = %s" % ( str(unitId) )
    log.tracef(SQL)
    unitName = system.db.runScalarQuery(SQL, database)
    log.tracef("Fetched unit name <%s> for id <%s>", unitName, str(unitId))
    return unitName


def lookup(lookupType, key, database=""):
    ''' ---Depricated--- '''
    lookupId=lookupIdFromKey(lookupType, key, database)
    return lookupId

def lookupIdFromKey(lookupType, key, database=""):
    SQL = "select LookupId from Lookup where LookupTypeCode = '%s' and LookupName = '%s' " % (lookupType, key)
    lookupId=system.db.runScalarQuery(SQL, database)
    return lookupId 

def lookupKeyFromId(lookupType, lookupId, database=""):
    if lookupType == None or lookupId == None:
        return None
    SQL = "select LookupName from Lookup where LookupTypeCode = '%s' and LookupId = %s " % (lookupType, str(lookupId))
    log.infof("SQL: %s", SQL)
    key = system.db.runScalarQuery(SQL, database)
    log.infof("Fetched: %s", str(key))
    return key 

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