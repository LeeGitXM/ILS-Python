'''
Created on Jul 13, 2015

@author: Pete
'''

import system

#open transaction when window is opened
def internalFrameOpened(rootContainer):
    print "Reserving a transaction Id... "
    txId = system.db.beginTransaction(timeout=3600000)
    rootContainer.txId = txId
    
    SQL = "select AssociationType from TkAssociationType order by AssociationType"
    pds = system.db.runQuery(SQL)
    rootContainer.associationTypeDataset = pds
    
#refresh when window is activated
def internalFrameActivated(rootContainer):
    print "Calling update() from internalFrameActivated()..."
    update(rootContainer)

#open transaction when window is opened
def internalFrameClosing(rootContainer):
    try:
        txId=rootContainer.txId
        system.db.rollbackTransaction(txId)
        print "Closing the transaction"
        system.db.closeTransaction(txId)
    except:
        print "Caught an error trying to close the transaction"
        
#update the window
def update(rootContainer):
    print "...updating..."
    txId = rootContainer.txId
    table = rootContainer.getComponent("Power Table")
    
    #update associations table
    SQL = "SELECT A.AssociationId, A.Source, A.Sink, T.AssociationType "\
        " FROM TkAssociation A, TkAssociationType T "\
        " WHERE A.AssociationTypeId = T.AssociationTypeId"
    print SQL
    pds = system.db.runQuery(SQL, tx=txId)
    table.data = pds
    
# Delete the selected row from the database and then update the table from the database
def deleteRowCallback(rootContainer):
    txId = rootContainer.txId
    table = rootContainer.getComponent("Power Table")
    ds = table.data
    
    row = table.selectedRow
    associationId = ds.getValueAt(row, "AssociationId")
            
    #remove the selected row
    SQL = "DELETE FROM TkAssociation "\
        " WHERE AssociationId = %d "\
        % (associationId)
    system.db.runUpdateQuery(SQL, tx=txId)
    
    update(rootContainer)

# Insert an empty row into the table that the user can edit in place
def addRowCallback(rootContainer):
    print "Adding a new row..."
    table = rootContainer.getComponent("Power Table")
    ds = table.data
    ds = system.dataset.addRow(ds, [-1,"","",""])
    table.data = ds

def saveRow(table, row, colName, oldValue, newValue):
    #--------------------------------------------------
    def insertRow(table, row, txId):    
        source = ds.getValueAt(row,"Source")
        sink = ds.getValueAt(row,"Sink")
        associationType = ds.getValueAt(row,"AssociationType")
        if source == None or source == "":
            print "Missing source"
            return
        if sink == None or sink == "":
            print "Missing sink"
            return
        if associationType == None or associationType == "":
            print "Missing association"
            return
        
        from ils.common.associations import lookupAssociationType
        associationTypeId = lookupAssociationType(associationType)
        
        SQL = "INSERT INTO TkAssociation (Source, Sink, AssociationTypeId)"\
            "VALUES ('%s', '%s', %s)" % (source, sink, str(associationTypeId))
        print SQL
        system.db.runUpdateQuery(SQL, tx=txId)
    #--------------------------------------------------
    def updateRow(table, row, colName, associationId, newValue, txId):
        if colName == "AssociationType":
            colName = "AssociationTypeId"
            from ils.common.associations import lookupAssociationType
            newValue = lookupAssociationType(newValue) 
            
        SQL = "UPDATE TkAssociation set %s = '%s' where AssociationId = %s" % (colName, newValue, associationId)
        print SQL
        system.db.runUpdateQuery(SQL, tx=txId)
    #--------------------------------------------------

    print "Saving the row..."
    rootContainer = table.parent
    txId = rootContainer.txId
    ds = table.data
    associationId = ds.getValueAt(row,"AssociationId")
    
    if associationId == -1:
        insertRow(table, row, txId)
    else:
        updateRow(table, row, colName, associationId, newValue, txId)
    