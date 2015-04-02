'''
Created on Mar 29, 2015

@author: Pete
'''
import system
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
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

def fetchLimits(database = ""):
    SQL = "select * from LtLimitView order by ValueName"
    pds = system.db.runQuery(SQL, database)
    return pds