'''
Created on Jul 14, 2015

@author: Pete
'''

import system

# Open transaction when window is opened
def internalFrameOpened(rootContainer):
    print "In internalFrameOpened(), reserving a cursor..."
    txId = system.db.beginTransaction(timeout=3600000)
    rootContainer.txId = txId

# Refresh when window is activated
def internalFrameActivated(rootContainer):
    print "In internaFrameActived()..."
    rootContainer.selectedValueId = 0
    
    print "Calling update() from internalFrameActivated()"
    update(rootContainer)
 
# Close transaction when window is closed
def internalFrameClosing(rootContainer):
    try:
        txId=rootContainer.txId
        system.db.rollbackTransaction(txId)
        print "Closing the transaction..."
        system.db.closeTransaction(txId)
    except:
        print "Caught an error trying to close the transaction"
            
#remove the selected row
def removeDataRow(event):
    rootContainer = event.source.parent
    txId = rootContainer.txId

    # Get valueId of the data to be deleted
    valueId = rootContainer.selectedValueId

    #check for derived lab data references
    # Not sure if a selector can be referenced by derived data, I guess why not?
    SQL = "SELECT count(*) FROM LtDerivedValue WHERE TriggerValueId = %i" %(valueId)
    triggerRows = system.db.runScalarQuery(SQL, tx=txId)
    SQL = "SELECT count(*) FROM LtRelatedData WHERE RelatedValueId = %i" %(valueId)
    relatedRows = system.db.runScalarQuery(SQL, tx=txId)
        
    # If there is derived lab data based on this lab data, then inform the operator and make sure they want to delete  the
    # derived data along with this data
    if triggerRows > 0 or relatedRows > 0:
        ans = system.gui.confirm("This value has derived values. Do you want to remove this data and all of its derived data?", "Confirm")
        #don't delete anything
        if ans == False:
            return
        #delete everything... not finished as of 6/30
        else:
            print "Deleting lab data that is derived from this lab datum..."
            SQL = "select V.ValueName, V.ValueId "\
                "from LtValue V, LtDerivedValue DV "\
                " where V.ValueId = DV.ValueId "\
                " and TriggerValueId = %s" % (str(valueId))
            print SQL
            pds = system.db.runQuery(SQL, tx=txId)
            
            for record in pds:
                derivedValueId=record["ValueId"]
                SQL = "delete from LtRelatedData where DerivedValueId in "\
                    "(select DerivedValueId from LtDerivedValue where ValueId = %s)" % (str(derivedValueId))
                print SQL
                rows = system.db.runUpdateQuery(SQL, tx=txId)
                print "Deleted %i rows from LtRelatedData" % (rows)
                
                SQL = "DELETE FROM LtDerivedValue WHERE ValueId = %s " % (str(derivedValueId))
                print SQL
                rows = system.db.runUpdateQuery(SQL, tx=txId)
                print "Deleted %i rows from LtDerivedValue" % (rows)
                                
                SQL = "DELETE FROM LtValue WHERE ValueId = %s " % (str(derivedValueId))
                print SQL
                rows = system.db.runUpdateQuery(SQL, tx=txId)
                print "Deleted %i rows from LtValue" % (rows)

    # remove the selected row from either PHD, DCS, or Local
    SQL = "DELETE FROM LtSelector WHERE ValueId = '%s'" % (valueId)
    system.db.runUpdateQuery(SQL, tx=txId)
                
    # delete from LtHistory
    SQL = "DELETE FROM LtHistory WHERE ValueId = '%s'" % (valueId)
    system.db.runUpdateQuery(SQL, tx=txId)
        
    # delete from LtLimit (I don't think a selector has a record in the limit table, but won't hurt to try)
    SQL = "DELETE FROM LtLimit WHERE ValueId = '%s'" % (valueId)
    system.db.runUpdateQuery(SQL, tx=txId)
        
    # delete from LtValue
    SQL = "DELETE FROM LtValue WHERE ValueId = '%s'" % (valueId)
    system.db.runUpdateQuery(SQL, tx=txId)
        
#add a row to the data table
def insertDataRow(event):
    rootContainer = event.source.parent
    txId = rootContainer.txId

    newName = rootContainer.getComponent("name").text
    description = rootContainer.getComponent("description").text
    decimals = rootContainer.getComponent("Spinner").intValue
    unitId = rootContainer.unitId
        
    #insert the user's data as a new row
    SQL = "INSERT INTO LtValue (ValueName, Description, UnitId, DisplayDecimals)"\
        "VALUES ('%s', '%s', %i, %i)" %(newName, description, unitId, decimals)
    print SQL
    valueId = system.db.runUpdateQuery(SQL, tx=txId, getKey = True)
    
    from ils.common.cast import toBit
    hasValidityLimit=toBit(rootContainer.getComponent("ValidityLimitCheckBox").selected)
    hasSQCLimit=toBit(rootContainer.getComponent("SQCLimitCheckBox").selected)
    hasReleaseLimit=toBit(rootContainer.getComponent("ReleaseLimitCheckBox").selected)
    
    SQL = "INSERT INTO LtSelector (ValueId, HasValidityLimit, HasSQCLimit, HasReleaseLimit)"\
            "VALUES (%s, %i, %i, %i)" %(str(valueId), hasValidityLimit, hasSQCLimit, hasReleaseLimit)
    print SQL
    system.db.runUpdateQuery(SQL, tx=txId)
    
#update the window
def update(rootContainer):
    txId = rootContainer.txId
    unitId = rootContainer.getComponent("UnitName").selectedValue
    
    SQL = "SELECT V.ValueId, V.ValueName, V.Description, V.DisplayDecimals, V.UnitId, "\
            " S.hasValidityLimit, S.hasSQCLimit, S.HasReleaseLimit "\
            "FROM LtValue V, LtSelector S "\
            "WHERE UnitId = %i "\
            "AND V.ValueId = S.ValueId "\
            "ORDER BY ValueName" % (unitId)
    pds = system.db.runQuery(SQL, tx=txId)
    table = rootContainer.getComponent("Selector_Value")
    table.updateInProgress = True
    table.data = pds
    table.updateInProgress = False
    
    
#update the database when user directly changes table 
def dataCellEdited(table, rowIndex, colName, newValue):
    print "A cell has been edited so update the database..."
    rootContainer = table.parent.parent
    txId = rootContainer.txId
    ds = table.data
    valueId =  ds.getValueAt(rowIndex, "ValueId")
    
    if colName == "ValueName":
        SQL = "UPDATE LtValue SET ValueName = '%s' "\
            "WHERE ValueId = %i" % (newValue, valueId)
    elif colName == "Description":
        SQL = "UPDATE LtValue SET Description = '%s' "\
            "WHERE ValueId = %i" % (newValue, valueId)
    elif colName == "DisplayDecimals":
        SQL = "UPDATE LtValue SET DisplayDecimals = %i "\
            "WHERE ValueId = %i" % (newValue, valueId)
    elif colName == "hasValidityLimit":
        SQL = "UPDATE LtSelector SET hasValidityLimit = %i "\
            "WHERE ValueId = %i" % (newValue, valueId)
    elif colName == "hasSQCLimit":
        SQL = "UPDATE LtSelector SET hasSQCLimit = %i "\
            "WHERE ValueId = %i" % (newValue, valueId)
    elif colName == "hasReleaseLimit":
        SQL = "UPDATE LtSelector SET hasReleaseLimit = %i "\
            "WHERE ValueId = %i" % (newValue, valueId)
            
    print SQL
    system.db.runUpdateQuery(SQL, tx=txId)
