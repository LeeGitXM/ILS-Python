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

# The timeout here is in seconds, the default time to wait is 1 minute, the refresh interval is always 1 second.
def waitForConsistency(tag1, tag2, timeout=60):
    cal = Calendar.getInstance()
    now = Date()
    cal.setTime(now)
    cal.add(Calendar.SECOND, timeout)
    endTime = cal.getTime()
        
    consistent=checkConsistency(tag1, tag2)
    
    while not(consistent):
        time.sleep(1)
        consistent=checkConsistency(tag1, tag2)
        
        # check if we have exceeded the timeout
        now = Date()
        if now > endTime and not(consistent):
            return "Timeout"

    return "Consistent"

def checkConsistency(tag1, tag2):
    vals=system.tag.readAll([tag1, tag2])
    qv1=vals[0]
    qv2=vals[1]
    
    if qv2.timestamp >= qv1.timestamp:
        consistent=True
    else:
        consistent=False
    
    return consistent    