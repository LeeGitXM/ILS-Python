'''
Created on Mar 7, 2016

@author: ils
'''

import system
from ils.common.config import getDatabaseClient

def internalFrameOpened(rootContainer):
    print "In internalFrameOpened"
    database=getDatabaseClient()
    txId=system.db.beginTransaction(database, timeout=600000)
    rootContainer.txId=txId
    refreshMaster(rootContainer)
    refreshDetails(rootContainer)

# This is called from a timer on the window and is called to keep the transaction open.
def refreshTransaction(rootContainer):
    txId=rootContainer.txId
    print "Refreshing the database transaction..."
    SQL = "select count(*) from SfcRecipeDataKeyMaster"
    rows=system.db.runScalarQuery(SQL,tx=txId) 
    print "There are %i key families" % (rows)
    
def ok(event):
    print "In ok"
    rootContainer=event.source.parent
    txId=rootContainer.txId
    system.db.commitTransaction(txId)
    system.db.closeTransaction(txId)
    system.nav.closeParentWindow(event)

def applyCallback(event):
    print "In applyCallback"
    rootContainer=event.source.parent
    txId=rootContainer.txId
    system.db.commitTransaction(txId)

def cancel(event):
    print "In cancel"
    rootContainer=event.source.parent
    txId=rootContainer.txId
    system.db.rollbackTransaction(txId)
    system.db.closeTransaction(txId)
    system.nav.closeParentWindow(event)
    
def refreshMaster(rootContainer):
    print "...refreshing master..."
    SQL = "SELECT KeyName FROM SfcRecipeDataKeyMaster ORDER BY KeyName"
    print SQL
    txId=rootContainer.txId
    pds=system.db.runQuery(SQL, tx=txId)
    masterList=rootContainer.getComponent("Left List")
    masterList.data=pds

def addMaster(rootContainer):
    masterKey = system.gui.inputBox("New Family Name:", "")
    if masterKey == None or masterKey == "":
        return
    
    txId=rootContainer.txId
    SQL = "insert into SFCRecipeDataKeyMaster (KeyName) values ('%s')" % (masterKey)
    print SQL
    system.db.runUpdateQuery(SQL,tx=txId)
    refreshMaster(rootContainer)

def deleteMaster(rootContainer):
    masterList=rootContainer.getComponent("Left List")
    
    if masterList.selectedIndex < 0:
        return
    
    ds=masterList.data
    selectedKey=ds.getValueAt(masterList.selectedIndex, 0)
    
    txId=rootContainer.txId
    SQL = "delete from SFCRecipeDataKeyMaster where KeyName = '%s'" % (selectedKey)
    print SQL
    
    system.db.runUpdateQuery(SQL,tx=txId)
    refreshMaster(rootContainer)
    refreshDetails(rootContainer)

def selectMaster(rootContainer):
    print "... in selectMaster..."
    refreshDetails(rootContainer)

def refreshDetails(rootContainer):
    print "...refreshing details..."
    masterList=rootContainer.getComponent("Left List")
    detailList=rootContainer.getComponent("Right List")
    
    if masterList.selectedIndex < 0:
        return
    
    txId=rootContainer.txId
    ds=masterList.data
    selectedKey=ds.getValueAt(masterList.selectedIndex, 0)
    print "The user selected:", selectedKey
    
    SQL = "select KeyValue, KeyIndex "\
        " from SfcRecipeDataKeyDetail D, SfcRecipeDataKeyMaster M " \
        " where KeyName = '%s' and D.KeyId = M.KeyId" \
        " order by KeyIndex" % (selectedKey)
    print SQL
    
    pds=system.db.runQuery(SQL, tx=txId)
    detailList.data=pds
    detailList.rowCount=len(pds)
    
def addDetail(rootContainer):
    keyValue = system.gui.inputBox("New Key:", "")
    if keyValue == None or keyValue == "":
        return
    
    txId=rootContainer.txId
    
    # Get the Id for the family - there should be something selected.
    masterList=rootContainer.getComponent("Left List")
    if masterList.selectedIndex < 0:
        return
    ds=masterList.data
    keyName=ds.getValueAt(masterList.selectedIndex, 0)
    keyId=system.db.runScalarQuery("select KeyId from SfcRecipeDataKeyMaster where KeyName = '%s' " % keyName,tx=txId)
    
    # Get the number of the elements in the right list and this will be 
    detailList=rootContainer.getComponent("Right List")
    ds=detailList.data
    idx=ds.rowCount
    
    SQL = "insert into SFCRecipeDataKeyDetail (KeyId, KeyValue, KeyIndex) "\
        "values (%i, '%s', %i)" % (keyId, keyValue, idx)
    print SQL

    system.db.runUpdateQuery(SQL,tx=txId)
    refreshMaster(rootContainer)

def deleteDetail(rootContainer):
    masterList=rootContainer.getComponent("Left List")
    if masterList.selectedIndex < 0:
        return
    
    detailList=rootContainer.getComponent("Right List")
    if detailList.selectedIndex < 0:
        return
    
    txId=rootContainer.txId
    
    # Get the id of the family key
    ds=masterList.data
    keyName=ds.getValueAt(masterList.selectedIndex, 0)
    keyId=system.db.runScalarQuery("select KeyId from SfcRecipeDataKeyMaster where KeyName = '%s' " % keyName,tx=txId)

    ds=detailList.data
    selectedKey=ds.getValueAt(detailList.selectedIndex, 0)
    print "The selected key is:", selectedKey
    
    SQL = "delete from SFCRecipeDataKeyDetail where KeyId = %i and KeyValue = '%s'" % (keyId, selectedKey)
    print SQL
    
    system.db.runUpdateQuery(SQL,tx=txId)
    refreshDetails(rootContainer)
    
def moveUp(rootContainer):
    print "...move up..."
    
    masterList=rootContainer.getComponent("Left List")
    if masterList.selectedIndex < 0:
        return
    
    detailList=rootContainer.getComponent("Right List")
    if detailList.selectedIndex < 1:
        return

    txId=rootContainer.txId

    # Get the id of the family key
    ds=masterList.data
    keyName=ds.getValueAt(masterList.selectedIndex, 0)
    keyId=system.db.runScalarQuery("select KeyId from SfcRecipeDataKeyMaster where KeyName = '%s' " % keyName,tx=txId)

    ds=detailList.data
    keyValue=ds.getValueAt(detailList.selectedIndex, 0)
    print "The selected key is:", keyValue
    
    idx=detailList.selectedIndex
    
    # Swap the selected row and the row above it, first move the selected row up
    SQL = "update SfcRecipeDataKeyDetail set KeyIndex = %i "\
        " where keyValue = '%s' and keyId = %i" % (idx-1, keyValue, keyId)
    print SQL
    system.db.runUpdateQuery(SQL, tx=txId)
    
    # Now move the previous row down 1
    keyValue=ds.getValueAt(detailList.selectedIndex - 1, 0)
    SQL = "update SfcRecipeDataKeyDetail set KeyIndex = %i "\
        " where keyValue = '%s' and keyId = %i" % (idx, keyValue, keyId)
    print SQL
    system.db.runUpdateQuery(SQL, tx=txId)

    refreshDetails(rootContainer)
    detailList.selectedIndex = idx - 1

def moveDown(rootContainer):
    print "...move down..."
    
    masterList=rootContainer.getComponent("Left List")
    if masterList.selectedIndex < 0:
        return
    
    detailList=rootContainer.getComponent("Right List")
    if detailList.selectedIndex < 0 or detailList.selectedIndex > detailList.data.rowCount - 2:
        return

    txId=rootContainer.txId

    # Get the id of the family key
    ds=masterList.data
    keyName=ds.getValueAt(masterList.selectedIndex, 0)
    keyId=system.db.runScalarQuery("select KeyId from SfcRecipeDataKeyMaster where KeyName = '%s' " % keyName,tx=txId)

    ds=detailList.data
    keyValue=ds.getValueAt(detailList.selectedIndex, 0)
    print "The selected key is:", keyValue
    
    idx=detailList.selectedIndex
    
    # Swap the selected row and the row above it, first move the selected row down
    SQL = "update SfcRecipeDataKeyDetail set KeyIndex = %i "\
        " where keyValue = '%s' and keyId = %i" % (idx+1, keyValue, keyId)
    print SQL
    system.db.runUpdateQuery(SQL, tx=txId)
    
    # Now move the next row up 1
    keyValue=ds.getValueAt(detailList.selectedIndex + 1, 0)
    SQL = "update SfcRecipeDataKeyDetail set KeyIndex = %i "\
        " where keyValue = '%s' and keyId = %i" % (idx, keyValue, keyId)
    print SQL
    system.db.runUpdateQuery(SQL, tx=txId)

    refreshDetails(rootContainer)
    detailList.selectedIndex = idx + 1
    