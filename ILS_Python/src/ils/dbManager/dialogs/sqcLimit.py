'''
Created on Mar 21, 2017

@author: phass

Scripts in support of the "SQC Limits" dialog
'''

import system
from ils.dbManager.ui import populateRecipeFamilyDropdown, populateGradeForFamilyDropdown
from ils.common.util import getRootContainer
from ils.dbManager.userdefaults import get as getUserDefaults
from ils.common.error import notifyError
log = system.util.getLogger("com.ils.recipe.ui")

# When the screen is first displayed, set widgets for user defaults
# The "active" dropdown is always initialized to "TRUE"
def internalFrameOpened(rootContainer):
    log.trace("InternalFrameOpened")
            
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
    
#
# Re-query the database and update the screen accordingly.
# If we get an exception, then rollback the transaction.
def requery(component):
    log.info("sqclimit.requery ...")
    rootContainer = getRootContainer(component)
    table = rootContainer.getComponent("DatabaseTable")
    whereExtension = getWhereExtension(component)
    SQL = "SELECT F.RecipeFamilyId, F.RecipeFamilyName, L.Grade, P.Parameter, L.LowerLimit, L.UpperLimit, P.ParameterId "\
        " FROM RtRecipeFamily F, RtSQCParameter P, RtSQCLimit L "\
        " WHERE L.ParameterId = P.ParameterId "\
        " AND P.RecipeFamilyId = F.RecipeFamilyId %s "\
        " ORDER BY F.RecipeFamilyName, L.Grade, P.Parameter" % (whereExtension)
    log.trace(SQL)
    try:
        pds = system.db.runQuery(SQL)
        table.data = pds
    except:
        notifyError(__name__, "Error fetching SQC limit data")


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
    tx = system.db.beginTransaction()
    rownum = table.selectedRow
    ds = table.data
    pid = ds.getValueAt(rownum,'ParameterId')
    
    try:
        SQL = "DELETE FROM RtSQCLimit WHERE ParameterId = %i" % (pid)
        log.trace(SQL)
        rows = system.db.runUpdateQuery(SQL,tx=tx)
        log.info("Deleted %i rows from RtSQCLimit" % (rows))
        
        SQL = "DELETE FROM RtSQCParameter WHERE ParameterId = %i" % (pid)
        log.trace(SQL)
        rows = system.db.runUpdateQuery(SQL,tx=tx)
        log.info("Deleted %i rows from RtSQCParameter" % (rows))
    except:
        system.db.rollbackTransaction(tx)
        notifyError(__name__, "Error deleting a SQC Limit")
    else:
        system.db.commitTransaction(tx)
        ds = system.dataset.deleteRow(ds,rownum)
        table.data = ds
        table.selectedRow = -1
    
    system.db.closeTransaction(tx)

# Enhance the joining where clause with the selection from the family dropdown.
def getWhereExtension(rootContainer):
    where = ""

    family = getUserDefaults("FAMILY")
    if family != "ALL":
        where = " AND F.RecipeFamilyName = '"+family+"'"
    grade = rootContainer.getComponent("GradeDropdown").selectedStringValue
    if grade != "ALL":
        where = where+ " AND L.Grade = '"+grade+"'"
    return where

    
# Update database for a cell edit. We only allow edits of parameter name or 
# limits.
def update(table,row,colname,value):
    log.info("sqclimit.update (%d:%s)=%s ..." %(row,colname,str(value)))
    ds = table.data
    #column is LowerLimit or UpperLimit. Others are not editable.
    paramid=ds.getValueAt(row,"ParameterId")
    grade=ds.getValueAt(row,"Grade")
    try:
        SQL = "UPDATE RtSQCLimit SET %s = %s WHERE ParameterId = %i and Grade = '%s'" % (colname, str(value), paramid, grade)
        log.trace(SQL)
        system.db.runUpdateQuery(SQL)
    except:
        notifyError(__name__, "Error updating a SQC limit")