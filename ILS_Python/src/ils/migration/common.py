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
        return -1, -1, -1
    record = pds[0]
    serverName=record["newServerName"]
    scanClass=record["newScanClass"]
    
    # Now lookup the id of this interface in the RtWriteLocation table
    
    SQL = "select WriteLocationId from TkWriteLocation where ServerName = '%s' and ScanClass = '%s'" % (serverName, scanClass)
    pds = system.db.runQuery(SQL)
    if len(pds) != 1:
        print "Error looking up the translated server and scan class (%s, %s) in RtWriteLocation table" % (serverName, scanClass)
        writeLocationId = -1
    else:
        record = pds[0]
        writeLocationId=record["WriteLocationId"]
    
    return serverName, scanClass, writeLocationId

def lookupHDAServer(site, gsiInterface):
    SQL = "select newServerName from HDAInterfaceTranslation where site = '%s' and oldInterfaceName = '%s'" % (site, gsiInterface)
    pds = system.db.runQuery(SQL, "XOMMigration")
    if len(pds) != 1:
        print "Error looking up GSI interface <%s> in the InterfaceTranslation table" % (gsiInterface)
        return -1, -1, -1
    record = pds[0]
    serverName=record["newServerName"]
    
    # Now lookup the id of this interface in the LtHDAInterface table
    SQL = "select InterfaceId from LtHDAInterface where InterfaceName = '%s'" % (serverName)
    pds = system.db.runQuery(SQL)
    if len(pds) != 1:
        print "Error looking up the translated server (%s) in LtHDAInterface table" % (serverName)
        interfaceId = -1
    else:
        record = pds[0]
        interfaceId=record["InterfaceId"]
    
    return serverName, interfaceId

#
def lookupMessageQueue(oldQueueName):
    SQL = "select newName from QueueTranslation where oldName = '%s'" % (oldQueueName)
    pds = system.db.runQuery(SQL, "XOMMigration")
    if len(pds) != 1:
        print "Error looking up Queue <%s> in the QueueTranslation table" % (oldQueueName)
        SQL = "insert into QueueTranslation (oldName) values ('%s')" % (oldQueueName)
        system.db.runUpdateQuery(SQL, "XOMMigration")
        return "", -1
    record = pds[0]
    newQueueName=record["newName"]
    
    # Now lookup the id of this interface in the RtWriteLocation table

    SQL = "select QueueId from QueueMaster where QueueKey = '%s' " % (newQueueName)
    pds = system.db.runQuery(SQL)
    if len(pds) != 1:
        print "Error looking up the translated queue named (%s) in QueueMaster table" % (newQueueName)
        return newQueueName, -1

    record = pds[0]
    queueId=record["QueueId"]
    
    return newQueueName, queueId

#
def lookupFeedbackMethod(oldName):
    SQL = "select newName from FeedbackMethodTranslation where oldName = '%s'" % (oldName)
    pds = system.db.runQuery(SQL, "XOMMigration")
    if len(pds) != 1:
        print "Error looking up old name <%s> in the FeedbackMethodTranslation table" % (oldName)
        SQL = "insert into FeedbackMethodTranslation (oldName) values ('%s')" % (oldName)
        system.db.runUpdateQuery(SQL, "XOMMigration")
        return "", -1
    record = pds[0]
    newName=record["newName"]
    
    # Now lookup the id of this interface in the Lookup table

    SQL = "select LookupId from Lookup where LookupTypeCode = 'FeedbackMethod' and LookupName = '%s' " % (newName)
    pds = system.db.runQuery(SQL)
    if len(pds) != 1:
        print "Error looking up the translated name (%s) in FeedbackMethodTranslation table" % (newName)
        return newName, -1

    record = pds[0]
    lookupId=record["LookupId"]
    
    return newName, lookupId