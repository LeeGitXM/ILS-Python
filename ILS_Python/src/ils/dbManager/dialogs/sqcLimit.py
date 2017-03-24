'''
Created on Mar 21, 2017

@author: phass

Scripts in support of the "SQC Limits" dialog
'''

import sys, system
from ils.dbManager.ui import populateRecipeFamilyDropdown, populateGradeForFamilyDropdown
from ils.dbManager.sql import getRootContainer, getTransactionForComponent, rollbackTransactionForComponent, closeTransactionForComponent, commitTransactionForComponent, idForFamily
from ils.dbManager.userdefaults import get as getUserDefaults
log = system.util.getLogger("com.ils.recipe.sqclimit")

#
# Re-query the database and update the screen accordingly.
# If we get an exception, then rollback the transaction.
def requery(component):
    log.info("sqclimit.requery ...")
    container = getRootContainer(component)
    table = container.getComponent("DatabaseTable")
    whereExtension = getWhereExtension(component)
    SQL = "SELECT F.RecipeFamilyId, F.RecipeFamilyName, L.Grade, P.Parameter, L.LowerLimit, L.UpperLimit, P.ParameterId "\
        " FROM RtRecipeFamily F, RtSQCParameter P, RtSQCLimit L "\
        " WHERE L.ParameterId = P.ParameterId "\
        " AND P.RecipeFamilyId = F.RecipeFamilyId %s "\
        " ORDER BY F.RecipeFamilyName, L.Grade, P.Parameter" % (whereExtension)
    txn = getTransactionForComponent(table)
    log.trace(SQL)
    try:
        pds = system.db.runQuery(SQL,tx=txn)
        table.data = pds
    except:
        # type,value,traceback
        type,value,trace = sys.exc_info()
        log.info("sqclimit.requery: SQL Exception ...",value) 
        rollbackTransactionForComponent(table)
        system.gui.messageBox("Error initializing the SQC limit data")


# Given the current state of the table, make sure that other widgets
# on the screen are in-synch.
def refresh(component):
    container = getRootContainer(component)
    # Update the dropdown lists
    dropdown = container.getComponent("FamilyDropdown")
    populateRecipeFamilyDropdown(dropdown)
    dropdown = container.getComponent("GradeDropdown")
    populateGradeForFamilyDropdown(dropdown)


# By deleting a row, we are deleting the parameter for every grade for the unit.
def deleteRow(button):
    log.info("sqclimit.deleteRow ...")
    container = getRootContainer(button)
    table = container.getComponent("DatabaseTable")
    txn = getTransactionForComponent(button)
    rownum = table.selectedRow
    ds = table.data
    pid = ds.getValueAt(rownum,'ParameterId')
    
    SQL = "DELETE FROM RtSQCLimit WHERE ParameterId = %i" % (pid)
    log.trace(SQL)
    rows = system.db.runUpdateQuery(SQL,tx=txn)
    log.info("Deleted %i rows from RtSQCLimit" % (rows))
    
    SQL = "DELETE FROM RtSQCParameter WHERE ParameterId = %i" % (pid)
    log.trace(SQL)
    rows = system.db.runUpdateQuery(SQL,tx=txn)
    log.info("Deleted %i rows from RtSQCParameter" % (rows))
    
    ds = system.dataset.deleteRow(ds,rownum)
    table.data = ds
    table.selectedRow = -1

# Enhance the joining where clause with the selection from the family dropdown.
def getWhereExtension(component):
    where = ""

    family = getUserDefaults("FAMILY")
    if family != "ALL":
        where = " AND F.RecipeFamilyName = '"+family+"'"
    root = getRootContainer(component)
    grade = root.grade
    if grade != "ALL":
        where = where+ " AND L.Grade = '"+grade+"'"
    return where

# When the screen is first displayed, set widgets for user defaults
# The "active" dropdown is always initialized to "TRUE"
def internalFrameOpened(rootContainer):
    log.trace("InternalFrameOpened")
    
    # Clear the current transaction.
    rollbackTransactionForComponent(rootContainer)
            
    dropdown = rootContainer.getComponent("FamilyDropdown")
    dropdown.setSelectedStringValue(getUserDefaults("FAMILY"))
        
    dropdown = rootContainer.getComponent("GradeDropdown")
    dropdown.setSelectedStringValue(getUserDefaults("GRADE"))
    
# When the screen is first displayed, set widgets for user defaults
# The "active" dropdown is always initialized to "TRUE"
def internalFrameActivated(rootContainer):
    log.trace("InternalFrameActivated")
    requery(rootContainer)
    dropdown = rootContainer.getComponent("FamilyDropdown")
    populateRecipeFamilyDropdown(dropdown)
                                
# Called from the client startup script: View menu
# Note: No attempt is made at this point to reconcile with any tab strip
def showWindow():
    window = "DBManager/SQCLimits"
    system.nav.openWindow(window)
    system.nav.centerWindow(window)
    
# Update database for a cell edit. We only allow edits of parameter name or 
# limits.
def update(table,row,colname,value):
    log.info("sqclimit.update (%d:%s)=%s ..." %(row,colname,str(value)))
    txn = getTransactionForComponent(table)
    ds = table.data
    #column is LowerLimit or UpperLimit. Others are not editable.
    paramid=ds.getValueAt(row,"ParameterId")
    grade=ds.getValueAt(row,"Grade")
    SQL = "UPDATE RtSQCLimit SET %s = %s WHERE ParameterId = %i and Grade = '%s'" % (colname, str(value), paramid, grade)
    log.trace(SQL)
    system.db.runUpdateQuery(SQL,tx=txn)