'''
Created on Jul 3, 2015

@author: Pete
'''

import system
    
# Fetch all of the labBalerService Data associated with the lab data item
def fetchSinks(source, associationType, db=''):

    SQL = "Select A.sink from TkAssociation A, TkAssociationType AT "\
        " where A.source = '%s' "\
        " and A.AssociationTypeId = AT.AssociationTypeId "\
        " and AT.AssocationType = '%s'" % (source, associationType)
    
    pds = system.db.runQuery(SQL, db)
    sinks=[]
    for record in pds:
        sinks.append(record["sink"])
    return sinks

#open transaction when window is opened
def internalFrameOpened(rootContainer):
    txID = system.db.beginTransaction(timeout=300000)
    rootContainer.txID = txID
    update(rootContainer)
    
#refresh when window is activated
def internalFrameActivated(rootContainer):
    update(rootContainer)

#open transaction when window is opened
def internalFrameClosing(rootContainer):
    try:
        txId=rootContainer.txID
        system.db.rollbackTransaction(txId)
        system.db.closeTransaction(txId)
    except:
        print "Caught an error trying to close the transaction"
        
#update the window
def update(rootContainer):
    txID = rootContainer.txID
    table = rootContainer.getComponent("Power Table")
    
    #update associations table
    SQL = "SELECT A.AssociationId, A.Source, A.Sink, A.AssociationTypeId, T.AssociationType "\
        " FROM TkAssociation A, TkAssociationType T "\
        " WHERE A.AssociationTypeId = T.AssociationTypeId"
    print SQL
    pds = system.db.runQuery(SQL, tx=txID)
    table.data = pds
    
#remove the selected row
def removeRow(event):
    rootContainer = event.source.parent
    txID = rootContainer.txID
    table = rootContainer.getComponent("Power Table")
    ds = table.data
    
    row = table.selectedRow
    associationId = ds.getValueAt(row, "AssociationId")
            
    #remove the selected row
    SQL = "DELETE FROM TkAssociation "\
        " WHERE AssociationId = %i "\
        % (associationId)
    system.db.runUpdateQuery(SQL, tx=txID)
    
    update(rootContainer)
    
#add a row
def insertRow(event):
    rootContainer = event.source.parent
    txID = rootContainer.txID
    
    source = rootContainer.getComponent("New Source").text
    sink = rootContainer.getComponent("New Sink").text
    associationTypeId = rootContainer.getComponent("Dropdown").selectedValue
        
    sql = "INSERT INTO TkAssociation (Source, Sink, AssociationTypeId)"\
        "VALUES ('%s', '%s', '%s')" % (source, sink, associationTypeId)
    print sql
    system.db.runUpdateQuery(sql, tx=txID)