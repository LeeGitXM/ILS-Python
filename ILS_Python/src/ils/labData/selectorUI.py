'''
Created on Jul 14, 2015

@author: Pete
'''

import system
from ils.labData.synchronize import createLabSelector, deleteLabSelector, createLabLimit, deleteLabLimit, deleteDcsLabValue

# Open transaction when window is opened
def internalFrameOpened(rootContainer):
    print "In %s.internalFrameOpened()..." % (__name__)
    
    unitDropdown = rootContainer.getComponent("UnitName")
    unitDropdown.selectedValue = -1
    unitDropdown.selectedStringValue = "<Select One>"

# Refresh when window is activated
def internalFrameActivated(rootContainer):
    print "In %s.internaFrameActived()..." % (__name__)
    rootContainer.selectedValueId = 0
    
    print "Calling update() from internalFrameActivated()"
    update(rootContainer)
 
# Close transaction when window is closed
def internalFrameClosing(rootContainer):
    print "In %s.internalFrameClosing()..." % (__name__)

            
#remove the selected row
def removeDataRow(rootContainer):
    print "In %s.removeDataRow()..." % (__name__)
    
    unitName = rootContainer.getComponent("UnitName").selectedStringValue
    
    #get valueId of the data to be deleted
    valueId = rootContainer.selectedValueId
    valueName = rootContainer.selectedValueName

    #check for derived lab data references
    # Not sure if a selector can be referenced by derived data, I guess why not?
    SQL = "SELECT count(*) FROM LtDerivedValue WHERE TriggerValueId = %i" %(valueId)
    triggerRows = system.db.runScalarQuery(SQL)
    SQL = "SELECT count(*) FROM LtRelatedData WHERE RelatedValueId = %i" %(valueId)
    relatedRows = system.db.runScalarQuery(SQL)
        
    '''
    If there is derived lab data based on this lab data, then inform the operator and make sure they want to delete  the
    derived data along with this data
    '''
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
            pds = system.db.runQuery(SQL)
            
            for record in pds:
                derivedValueId=record["ValueId"]
                SQL = "delete from LtRelatedData where DerivedValueId in "\
                    "(select DerivedValueId from LtDerivedValue where ValueId = %s)" % (str(derivedValueId))
                print SQL
                rows = system.db.runUpdateQuery(SQL)
                print "Deleted %i rows from LtRelatedData" % (rows)
                
                SQL = "DELETE FROM LtDerivedValue WHERE ValueId = %s " % (str(derivedValueId))
                print SQL
                rows = system.db.runUpdateQuery(SQL)
                print "Deleted %i rows from LtDerivedValue" % (rows)
                                
                SQL = "DELETE FROM LtValue WHERE ValueId = %s " % (str(derivedValueId))
                print SQL
                rows = system.db.runUpdateQuery(SQL)
                print "Deleted %i rows from LtValue" % (rows)

    # remove the selected row from either PHD, DCS, or Local
    SQL = "DELETE FROM LtSelector WHERE ValueId = '%s'" % (valueId)
    system.db.runUpdateQuery(SQL)
                
    # delete from LtHistory
    SQL = "DELETE FROM LtHistory WHERE ValueId = '%s'" % (valueId)
    system.db.runUpdateQuery(SQL)
        
    # delete from LtLimit (I don't think a selector has a record in the limit table, but won't hurt to try)
    SQL = "DELETE FROM LtLimit WHERE ValueId = '%s'" % (valueId)
    system.db.runUpdateQuery(SQL)
        
    # delete from LtValue
    SQL = "DELETE FROM LtValue WHERE ValueId = '%s'" % (valueId)
    system.db.runUpdateQuery(SQL)
    
    ''' Delete the UDT, if it exists '''
    deleteLabSelector(unitName, valueName)
        
#add a row to the data table
def insertDataRow(rootContainer):
    print "In %s.insertDataRow()..." % (__name__)
    newName = rootContainer.getComponent("name").text
    if newName == "":
        system.gui.messageBox("You must specify a name for the lab value!", "Warning")
        return False
    
    description = rootContainer.getComponent("description").text
    decimals = rootContainer.getComponent("Spinner").intValue
    unitId = rootContainer.unitId
    unitName = rootContainer.unitName
    if unitId == -1 or unitName == "":
        system.gui.messageBox("You must select a unit for the lab value!", "Warning")
        return False
        
    #insert the user's data as a new row
    SQL = "INSERT INTO LtValue (ValueName, Description, UnitId, DisplayDecimals)"\
        "VALUES ('%s', '%s', %i, %i)" %(newName, description, unitId, decimals)
    print SQL
    valueId = system.db.runUpdateQuery(SQL, getKey=True)
    
    from ils.common.cast import toBit
    hasValidityLimit=toBit(rootContainer.getComponent("ValidityLimitCheckBox").selected)
    hasSQCLimit=toBit(rootContainer.getComponent("SQCLimitCheckBox").selected)
    hasReleaseLimit=toBit(rootContainer.getComponent("ReleaseLimitCheckBox").selected)
    
    SQL = "INSERT INTO LtSelector (ValueId, HasValidityLimit, HasSQCLimit, HasReleaseLimit)"\
            "VALUES (%s, %i, %i, %i)" %(str(valueId), hasValidityLimit, hasSQCLimit, hasReleaseLimit)
    print SQL
    system.db.runUpdateQuery(SQL)
    
    # Create the UDT
    createLabSelector(unitName, newName)
    
    '''
    Create the limit UDTs (SQC, Validity, Release)
    '''
    if hasSQCLimit or hasValidityLimit or hasReleaseLimit:
        
        if hasSQCLimit:
            createLabLimit(unitName, newName, "SQC")
            
        if hasValidityLimit:
            createLabLimit(unitName, newName, "VALIDITY")

        if hasReleaseLimit:
            createLabLimit(unitName, newName, "RELEASE")
    
    return True


#update the window
def update(rootContainer):
    unitId = rootContainer.getComponent("UnitName").selectedValue
    
    SQL = "SELECT V.ValueId, V.ValueName, V.Description, V.DisplayDecimals, V.UnitId, "\
            " S.hasValidityLimit, S.hasSQCLimit, S.hasReleaseLimit "\
            "FROM LtValue V, LtSelector S "\
            "WHERE UnitId = %i "\
            "AND V.ValueId = S.ValueId "\
            "ORDER BY ValueName" % (unitId)
    pds = system.db.runQuery(SQL)
    table = rootContainer.getComponent("Selector_Value")
    table.updateInProgress = True
    table.data = pds
    table.updateInProgress = False
    
    
#update the database when user directly changes table 
def dataCellEdited(table, rowIndex, colName, newValue):
    print "In %s.dataCellEdited() - column %s has been edited so update the database..." % (__name__, colName)
    rootContainer = table.parent
    unitName = rootContainer.getComponent("UnitName").selectedStringValue
    ds = table.data
    valueId =  ds.getValueAt(rowIndex, "ValueId")
    valueName =  ds.getValueAt(rowIndex, "ValueName")
    
    if colName == "ValueName":
        SQL = "UPDATE LtValue SET ValueName = '%s' WHERE ValueId = %i" % (newValue, valueId)
    
    elif colName == "Description":
        SQL = "UPDATE LtValue SET Description = '%s' WHERE ValueId = %i" % (newValue, valueId)
    
    elif colName == "DisplayDecimals":
        SQL = "UPDATE LtValue SET DisplayDecimals = %i WHERE ValueId = %i" % (newValue, valueId)
    
    elif colName == "hasValidityLimit":
        SQL = "UPDATE LtSelector SET hasValidityLimit = %i  WHERE ValueId = %i" % (newValue, valueId)
        if newValue:
            createLabLimit(unitName, valueName, "VALIDITY")
        else:
            deleteLabLimit(unitName, valueName, "VALIDITY")
    
    elif colName == "hasSQCLimit":
        SQL = "UPDATE LtSelector SET hasSQCLimit = %i WHERE ValueId = %i" % (newValue, valueId)
        if newValue:
            createLabLimit(unitName, valueName, "SQC")
        else:
            deleteLabLimit(unitName, valueName, "SQC")
    
    elif colName == "hasReleaseLimit":
        SQL = "UPDATE LtSelector SET hasReleaseLimit = %i WHERE ValueId = %i" % (newValue, valueId)
        if newValue:
            createLabLimit(unitName, valueName, "RELEASE")
        else:
            deleteLabLimit(unitName, valueName, "RELEASE")
            
    print SQL
    system.db.runUpdateQuery(SQL)
