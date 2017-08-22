'''
Created on Mar 21, 2017

@author: phass

Scripts in support of the "Full Definition" dialog.
For a unit these are the parameters that the operator expects.
An empty description serves as a separator on the screen.
'''

import sys, system
from ils.dbManager.ui import populateRecipeFamilyDropdown
from ils.dbManager.sql import getTransactionForComponent, rollbackTransactionForComponent, closeTransactionForComponent, commitTransactionForComponent, idForFamily, getRootContainer
from ils.dbManager.userdefaults import get as getUserDefaults
log = system.util.getLogger("com.ils.recipe.definition")

# When the screen is first displayed, set widgets for user defaults
def internalFrameOpened(component):
    log.trace("InternalFrameOpened")

    # Make sure the transaction is alive.
    getTransactionForComponent(component)
    
    # When the screen is first displayed, set widgets for user defaults
    container = getRootContainer(component)
    dropdown = container.getComponent("FamilyDropdown")
    populateRecipeFamilyDropdown(dropdown)
    dropdown.setSelectedStringValue(getUserDefaults("FAMILY"))

    requery(component)

# Re-query the database and update the screen accordingly.
# If we get an exception, then rollback the transaction.
def requery(component):
    log.info("definiton.requery ...")
    container = getRootContainer(component)
    table = container.getComponent("DatabaseTable")
    whereExtension = getWhereExtension()
    print "The where extension was: ", whereExtension
        
    SQL = "SELECT F.RecipeFamilyId,F.RecipeFamilyName,VD.PresentationOrder,VD.ValueId, "\
        " VD.Description,VD.StoreTag,VD.CompareTag,VD.ChangeLevel,VD.ModeAttribute,VD.ModeValue, WL.Alias, VT.ValueType"\
        " FROM RtValueDefinition VD INNER JOIN "\
        " RtValueType VT ON VT.ValueTypeId = VD.ValueTypeId INNER JOIN "\
        " RtRecipeFamily F ON F.RecipeFamilyId = VD.RecipeFamilyId LEFT OUTER JOIN "\
        " TkWriteLocation WL ON WL.WriteLocationId = VD.WriteLocationId "\
        " %s ORDER BY F.RecipeFamilyName,VD.PresentationOrder" % (whereExtension)
    log.trace(SQL)

    txn = getTransactionForComponent(table)

    try:
        pds = system.db.runQuery(SQL,tx=txn)
        table.data = pds
        refresh(table)
    except:
        # type,value,traceback
        type,value,trace = sys.exc_info()
        log.info("definiton.requery: SQL Exception ...",value) 
        rollbackTransactionForComponent(table)

# Given the current state of the table, make sure that other widgets
# on the screen are in-synch. 
def refresh(component):
    container = getRootContainer(component)
    table = container.getComponent("DatabaseTable")
    
    button = container.getComponent("DeleteButton")
    if button!=None:
        button.setEnabled(table.selectedRow>=0 and table.selectedRow<table.data.getRowCount())
    
    button = container.getComponent("AddButton")
    if button!=None:
        unit = getUserDefaults("UNIT")
        button.setEnabled((table.selectedRow>=0 or table.data.rowCount == 0) and unit!="ALL")    

# When we delete a row, we need to fix the presentation order
# for the following rows. Button must requery to sync display.
def deleteRow(button):
    log.info("definiton.deleteRow ...")
    container = getRootContainer(button)
    table = container.getComponent("DatabaseTable")
    txn = getTransactionForComponent(button)
    rownum = table.selectedRow
    ds = table.data
    familyid = ds.getValueAt(rownum,'RecipeFamilyId')
    presOrder = ds.getValueAt(rownum,'PresentationOrder')
    vid = ds.getValueAt(rownum,'ValueId')
    SQL = "DELETE FROM RtValueDefinition WHERE RecipeFamilyId="+str(familyid)+" AND PresentationOrder="+str(presOrder)
    system.db.runUpdateQuery(SQL,tx=txn)
    # Now fix the remaining order
    SQL = "UPDATE RtValueDefinition SET presentationOrder = presentationOrder-1 "
    SQL = SQL + " WHERE RecipeFamilyId ="+str(familyid)+" AND PresentationOrder>"+str(presOrder)
    system.db.runUpdateQuery(SQL,tx=txn)
    # Finally remove any references in the GradeDetail
    SQL = "DELETE RtGradeDetail Where ValueId = "+str(vid)
    system.db.runUpdateQuery(SQL,tx=txn)

# Add a new row to the table. The data element is a DataSet (not python)
# When complete, the button will re-query
def duplicateRow(button):
    log.info("definiton.duplicateRow ...")
    container = getRootContainer(button)
    table = container.getComponent("DatabaseTable")
    txn = getTransactionForComponent(button)
    
    defaultValueTypeId = system.db.runScalarQuery("select ValueTypeId from RtValueType where ValueType = 'Float'", tx=txn) 
    
    ds = table.data
    if ds.rowCount == 0:
        print "Adding the first row"
        family = container.getComponent("FamilyDropdown").selectedStringValue
        familyid = idForFamily(family, txn)
        print "The selected family is: ", family, " - id: ", familyid
        presOrder = 1
        SQL = "INSERT INTO RtValueDefinition(RecipeFamilyId,PresentationOrder,ChangeLevel,ValueTypeId) VALUES (%s,%s,'CC',%s)" % (str(familyid), str(presOrder), str(defaultValueTypeId))
        log.trace(SQL)
        vid=system.db.runUpdateQuery(SQL,tx=txn,getKey=True)
    else:
        rownum = table.selectedRow
        familyid  = ds.getValueAt(rownum,"RecipeFamilyId")
        presOrder = ds.getValueAt(rownum,'PresentationOrder')

        # First fix the order of following rows
        SQL = "UPDATE RtValueDefinition SET presentationOrder = presentationOrder+1 "\
            " WHERE RecipeFamilyId ="+str(familyid)+" AND PresentationOrder>="+str(presOrder)
        log.trace(SQL)
        rows = system.db.runUpdateQuery(SQL,tx=txn)
        log.infof("Renumbered %d rows", rows)
        
        # Now insert the new row in the vacated spot
        SQL = "INSERT INTO RtValueDefinition(RecipeFamilyId,PresentationOrder,ChangeLevel,ValueTypeId) VALUES (%s,%s,'CC',%s)" % (str(familyid), str(presOrder), str(defaultValueTypeId))
        log.trace(SQL)
        vid=system.db.runUpdateQuery(SQL,tx=txn,getKey=True)
        log.infof("Inserted a record into RtValueDefinition with id: %s", str(vid))
        
    # Now add a new grade detail row for each grade
    SQL = "INSERT INTO RtGradeDetail(RecipeFamilyId, Grade, ValueId, Version) "\
        " SELECT DISTINCT RecipeFamilyId, Grade, %s, Version " \
        " FROM RtGradeDetail WHERE recipeFamilyId = %s " % (str(vid), str(familyid))
    log.trace(SQL)
    rows=system.db.runUpdateQuery(SQL,tx=txn)
    log.info("Inserted %d rows into RtGradeDetail" % (rows))
    
# Enhance the joining where clause with the selection
# from the processing unit dropdown.
def getWhereExtension():
    where = ""
    family = getUserDefaults("FAMILY")
    if family != "ALL" and family != "":
        where = " WHERE F.RecipeFamilyName = '"+family+"'"
    return where

# We are guaranteed that the rows come from the same table.
# In addition they are contiguous
def moveRows(table,rows,rowData,dropIndex):
    minOrder = rowData.getValueAt(0,"PresentationOrder")
    maxOrder = rowData.getValueAt(len(rows)-1,"PresentationOrder")
    if minOrder>maxOrder:
        tmp = minOrder
        minOrder = maxOrder
        maxOrder = tmp
        
    # Now we have the range. The drop index can be 0-n.
    ds = table.data
    familyid  = ds.getValueAt(dropIndex,"RecipeFamilyId")
    dropOrder = ds.getValueAt(dropIndex,'PresentationOrder')
    # Nothing to do if drop zone within selected range
    if dropOrder>=minOrder and dropOrder<=maxOrder:
        return
    
    if dropOrder>maxOrder:
        dropOrder = dropOrder - 1
    txn = getTransactionForComponent(table)
    # First of all collapse rows greater than our range
    SQL = "UPDATE RtValueDefinition SET presentationOrder = presentationOrder-"+str(len(rows))
    SQL = SQL + " WHERE RecipeFamilyId ="+str(familyid)+" AND PresentationOrder>"+str(maxOrder)
    system.db.runUpdateQuery(SQL,tx=txn)
    # Now create the space for the moved row
    SQL = "UPDATE RtValueDefinition SET presentationOrder = presentationOrder+"+str(len(rows))
    SQL = SQL + " WHERE RecipeFamilyId ="+str(familyid)+" AND PresentationOrder>="+str(dropOrder)
    system.db.runUpdateQuery(SQL,tx=txn)
    # Finally update the presentation order for the rows that were moved
    po = dropOrder
    for row in range(rowData.rowCount):
        vid = rowData.getValueAt(row,"ValueId")
        SQL = "UPDATE RtValueDefinition SET presentationOrder = "+str(po)
        SQL = SQL + " WHERE RecipeFamilyId ="+str(familyid)+" AND ValueId="+str(vid)
        system.db.runUpdateQuery(SQL,tx=txn)
        po = po + 1
                
# Called from the client startup script: View menu
# Note: No attempt is made at this point to reconcile with any tab strip
def showWindow():
    window = "DBManager/ValueDefinition"
    system.nav.openWindow(window)
    system.nav.centerWindow(window)
    
# Update database for a cell edit.
def update(table,row,colname,value):
    log.info("definiton.update (%d:%s)=%s ..." %(row,colname,str(value)))
    txn = getTransactionForComponent(table)
    ds = table.data
    # All editable columns are strings.
    familyid = ds.getValueAt(row,"RecipeFamilyId")
    pid = ds.getValueAt(row,"PresentationOrder")
    
    # The Alias and valueType columns requires a lookup
    if colname == "Alias":
        colname = "WriteLocationId"
        value = system.db.runScalarQuery("select WriteLocationId from TkWriteLocation where Alias = '%s'" % (value))

    elif colname == "ValueType":
        colname = "ValueTypeId"
        value = system.db.runScalarQuery("select ValueTypeId from RtValueType where ValueType = '%s'" % (value))

    SQL = "UPDATE RtValueDefinition SET "+colname+" = '"+str(value)+"'"
    SQL = SQL+" WHERE RecipeFamilyId="+str(familyid)+" AND PresentationOrder="+str(pid)
    system.db.runUpdateQuery(SQL,tx=txn)