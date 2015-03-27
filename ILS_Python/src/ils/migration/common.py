'''
Created on Mar 12, 2015

@author: Pete
'''
import system

def lookupOPCServerAndScanClass(site, gsiInterface):
    SQL = "select newServerName, newScanClass from InterfaceTranslation where site = '%s' and oldInterfaceName = '%s'" % (site, gsiInterface)
    pds = system.db.runQuery(SQL, "XOMMigration")
    if len(pds) != 1:
        print "Error looking up GSI interface <%s> in the InterfaceTranslation table" % (gsiInterface)
        return -1, -1
    record = pds[0]
    serverName=record["newServerName"]
    scanClass=record["newScanClass"]
    return serverName, scanClass