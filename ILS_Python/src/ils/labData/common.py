'''
Created on Mar 29, 2015

@author: Pete
'''
import system
from ils.log import getLogger
log = getLogger(__name__)

# Lookup the id of an interface given its name
def fetchInterfaceId(interfaceName, database=""):
    SQL = "select InterfaceId from LtHDAInterface where InterfaceName = '%s'" % (interfaceName)
    log.trace(SQL)
    interfaceId = system.db.runScalarQuery(SQL, database)
    return interfaceId

# Lookup the id of a value given its name
def fetchValueId(valueName, database=""):
    SQL = "select ValueId, StringValue from LtValue where ValueName = '%s'" % (valueName)
    log.trace(SQL)
    pds = system.db.runQuery(SQL, database)
    record = pds[0]
    valueId = record["ValueId"]
    stringValue = record["StringValue"]
    return valueId, stringValue

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
    from ils.config.common import getProductionTagProviderFromInternalDatabase, getProductionDatabaseFromInternalDatabase, getIsolationDatabaseFromInternalDatabase
    tagPathRoot, tagName, tagProvider = parseTagPath(tagPath)

    # TODO - Really bad hard code of project name here! (PH 3/22/2023)
    # It looks like this is only called by the unitParameter utility
    projectName = "XOM"
    productionTagProvider=getProductionTagProviderFromInternalDatabase(projectName)

    if tagProvider == productionTagProvider:
        database=getProductionDatabaseFromInternalDatabase(projectName)
    else:
        database=getIsolationDatabaseFromInternalDatabase(projectName)

    return database

def queryLabHistoryValues(valueName, startDate, endDate, database = ""):
    log.trace("Fetching lab history for %s..." % (valueName))
    
    SQL = "select RawValue from LtHistory H, LtValue V "\
        " where V.ValueName = '%s' "\
        " and H.valueId = V.ValueId "\
        " and SampleTime > ? "\
        " and SampleTime < ? " % (valueName)
    
    records = system.db.runPrepQuery(SQL, [startDate, endDate], database)
    
    vals=[]
    for record in records:
        vals.append(record["RawValue"])
    
    log.trace("Returning values: %s" % (str(vals)))
    
    return vals