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
    
    # Now lookup the id of this interface in the RtWriteLocation table
    
    SQL = "select WriteLocationId from RtWriteLocation where ServerName = '%s' and ScanClass = '%s'" % (serverName, scanClass)
    pds = system.db.runQuery(SQL)
    if len(pds) != 1:
        print "Error up the translated derver and scan class (%s, %s) in RtWriteLocation table" % (serverName, scanClass)
        writeLocationId = -1
    else:
        record = pds[0]
        writeLocationId=record["WriteLocationId"]
    
    return serverName, scanClass, writeLocationId