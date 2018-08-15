'''
Created on Jul 26, 2018

@author: phass
'''

import system
from ils.common.config import getDatabaseClient

def internalFrameOpened(rootContainer):
    print "In %s.internalFrameOpened()..." % (__name__)
    refreshOpcServers(rootContainer)
    refreshHdaServers(rootContainer)
    

def internalFrameActivated(rootContainer):
    print "In %s.internaFrameActived()..." % (__name__)


def internalFrameClosing(rootContainer):
    print "In %s.internalFrameClosing()" % (__name__)
            
    
'''
------------------  OPC Server ------------------
'''

def browseOpcServers(event):
    rootContainer = event.source.parent
    print "In %s.browseOpcServers()" % (__name__)
    servers = system.opc.getServers()
    
    table = rootContainer.getComponent("OPC Servers")
    ds = table.data
    
    for server in servers:
        print "Checking ", server
        found = False
        for row in range(ds.rowCount):
            if server == ds.getValueAt(row, "InterfaceName"):
                found = True
        if not(found):
            insertOpcServer(server)
            ds = system.dataset.addRow(ds, [-1, server])

    refreshOpcServers(rootContainer)

def addOpcServer(event):
    rootContainer = event.source.parent
    print "In %s.addOpcServers()" % (__name__)
    serverName = system.gui.inputBox("Enter the OPC server name:")
    if serverName != None:
        insertOpcServer(serverName)
        refreshOpcServers(rootContainer)
    
def deleteOpcServer(event):
    rootContainer = event.source.parent
    print "In %s.deleteOpcServers()" % (__name__)

    table = rootContainer.getComponent("OPC Servers")
    ds = table.data
    selectedRow = table.selectedRow
    serverName = ds.getValueAt(selectedRow, "InterfaceName")
    removeOpcServer(serverName)
    refreshOpcServers(rootContainer)
    
def insertOpcServer(serverName):
    SQL = "insert into LtOpcInterface (InterfaceName) values ('%s')" % (serverName)
    db = getDatabaseClient()
    system.db.runUpdateQuery(SQL, db)
    
def removeOpcServer(serverName):
    SQL = "delete from LtOpcInterface where InterfaceName = '%s'" % (serverName)
    db = getDatabaseClient()
    system.db.runUpdateQuery(SQL, db)

def refreshOpcServers(rootContainer):
    SQL = "select InterfaceId, InterfaceName from LtOpcInterface order by InterfaceName"
    db = getDatabaseClient()
    pds = system.db.runQuery(SQL, db)
    table = rootContainer.getComponent("OPC Servers")
    table.data = pds
    

'''
--------------  HDA Servers ------------------
'''
    
def browseHdaServers(event):
    rootContainer = event.source.parent
    print "In %s.browseHdaServers()" % (__name__)
    servers = system.opchda.getServers()
    
    table = rootContainer.getComponent("HDA Servers")
    ds = table.data
    
    for server in servers:
        print "Checking ", server
        found = False
        for row in range(ds.rowCount):
            if server == ds.getValueAt(row, "InterfaceName"):
                found = True
        if not(found):
            insertHdaServer(server)
            ds = system.dataset.addRow(ds, [-1, server])

    refreshHdaServers(rootContainer)
    
def addHdaServer(event):
    rootContainer = event.source.parent
    print "In %s.addHdaServers()" % (__name__)
    serverName = system.gui.inputBox("Enter the HDA server name:")
    if serverName != None:
        insertHdaServer(serverName)
        refreshHdaServers(rootContainer)
    
def deleteHdaServer(event):
    rootContainer = event.source.parent
    print "In %s.deleteHdaServers()" % (__name__)

    table = rootContainer.getComponent("HDA Servers")
    ds = table.data
    selectedRow = table.selectedRow
    serverName = ds.getValueAt(selectedRow, "InterfaceName")
    removeHdaServer(serverName)
    refreshHdaServers(rootContainer)
    
def insertHdaServer(serverName):
    SQL = "insert into LtHdaInterface (InterfaceName) values ('%s')" % (serverName)
    db = getDatabaseClient()
    system.db.runUpdateQuery(SQL, db)

def removeHdaServer(serverName):
    SQL = "delete from LtHdaInterface where InterfaceName = '%s'" % (serverName)
    db = getDatabaseClient()
    system.db.runUpdateQuery(SQL, db)

def refreshHdaServers(rootContainer):
    SQL = "select InterfaceId, InterfaceName from LtHdaInterface order by InterfaceName"
    db = getDatabaseClient()
    pds = system.db.runQuery(SQL, db)
    table = rootContainer.getComponent("HDA Servers")
    table.data = pds
