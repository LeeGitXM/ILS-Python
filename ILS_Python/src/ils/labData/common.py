'''
Created on Mar 29, 2015

@author: Pete
'''
import system
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
from java.util import Calendar
from java.util import Date
import time
log = LogUtil.getLogger("com.ils.labData.SQL")

# Lookup the id of an interface given its name
def fetchInterfaceId(interfaceName, database=""):
    SQL = "select InterfaceId from LtHDAInterface where InterfaceName = '%s'" % (interfaceName)
    log.trace(SQL)
    interfaceId = system.db.runScalarQuery(SQL, database)
    return interfaceId

# Lookup the id of a value given its name
def fetchValueId(valueName, database=""):
    SQL = "select ValueId from LtValue where ValueName = '%s'" % (valueName)
    log.trace(SQL)
    valueId = system.db.runScalarQuery(SQL, database)
    return valueId

def postMessage(txt, status="Info", database=""):
    from ils.queue.message import insert
    insert("LABDATA", status, txt, database)  

# The tagPath must begin with the provider surrounded by square brackets
def parseTagPath(tagPath):
    end = tagPath.rfind(']')
    provider = tagPath[1:end]
    end = tagPath.rfind('/')
    tagPathRoot = tagPath[:end]
    end = tagPath.rfind('/')
    tagName = tagPath[end + 1:]
    return tagPathRoot, tagName, provider

def getDatabaseForTag(tagPath):
    tagPathRoot, tagName, tagProvider = parseTagPath(tagPath)

    import system.ils.blt.diagram as blt
    productionTagProvider=blt.getToolkitProperty("Provider")
    
    if tagProvider == productionTagProvider:
        database=blt.getToolkitProperty("Database")
    else:
        database=blt.getToolkitProperty("SecondaryDatabase")
        
    return database

def queryLabHistoryValues(valueName, startDate, endDate, database = ""):
    print "Fetching lab history for %s..." % (valueName)
    
    SQL = "select RawValue from LtHistory H, LtValue V "\
        " where V.ValueName = '%s' "\
        " and H.valueId = V.ValueId "\
        " and SampleTime > ? "\
        " and SampleTime < ? " % (valueName)
    
    records = system.db.runPrepQuery(SQL, [startDate, endDate], database)
    
    vals=[]
    for record in records:
        vals.append(record["RawValue"])
    
    print "Returning values: ", vals
    
    return vals