'''
Created on Mar 21, 2017

@author: phass

Scripts in support of the "Gains" dialog
'''

import sys, system
from ils.dbManager.ui import populateRecipeFamilyDropdown
from ils.dbManager.sql import getRootContainer, getTransactionForComponent, rollbackTransactionForComponent, closeTransactionForComponent, commitTransactionForComponent, idForFamily
from ils.dbManager.userdefaults import get as getUserDefaults
log = system.util.getLogger("com.ils.recipe.gain")

#
# Re-query the database and update the screen accordingly.
# If we get an exception, then rollback the transaction.
def requery(rootContainer):
    log.info("gain.requery ...")
    table = rootContainer.getComponent("DatabaseTable")
    whereExtension = getWhereExtension(rootContainer)
    SQL = "SELECT F.RecipeFamilyName, GG.Grade, G.Parameter, GG.Gain, G.ParameterId " \
        " FROM RtGain G, RtGainGrade GG, RtRecipeFamily F " \
        " WHERE G.ParameterId = GG.ParameterId "\
        " and G.RecipeFamilyId = F.RecipeFamilyId %s " \
        " ORDER BY GG.Grade, G.Parameter" % (whereExtension)
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
        system.gui.messageBox("Error initializing the Gain data")

# By deleting a row, we are deleting the parameter for every grade for the family.
def deleteRow(button):
    log.info("gain.deleteRow ...")
    container = getRootContainer(button)
    table = container.getComponent("DatabaseTable")
    txn = getTransactionForComponent(button)
    rownum = table.selectedRow
    ds = table.data
    pid = ds.getValueAt(rownum,'ParameterId')
    
    SQL = "DELETE FROM RtGainGrade WHERE ParameterId = %i" % (pid)
    log.trace(SQL)
    rows = system.db.runUpdateQuery(SQL,tx=txn)
    log.info("Deleted %i rows from RtGainGrade" % (rows))
    
    SQL = "DELETE FROM RtGain WHERE ParameterId = %i" % (pid)
    log.trace(SQL)
    rows = system.db.runUpdateQuery(SQL,tx=txn)
    log.info("Deleted %i rows from RtGain" % (rows))
    
    ds = system.dataset.deleteRow(ds,rownum)
    table.data = ds
    table.selectedRow = -1

# Enhance the joining where clause with the selects from the dropdowns
def getWhereExtension(rootContainer):
    where = ""

    dropdown = rootContainer.getComponent("FamilyDropdown")
    family = dropdown.selectedLabel
    if family != "ALL" and family != "<Family>":
        where = " AND F.RecipeFamilyName = '"+family+"' "
    
    dropdown = rootContainer.getComponent("GradeDropdown")
    grade = dropdown.selectedLabel
    if grade != "ALL" and grade != "<Grade>":
        where = where+" AND GG.Grade = '"+grade+"'"
                    
    return where

# When the screen is first displayed, set widgets for user defaults
# The "active" dropdown is always initialized to "TRUE"
def internalFrameOpened(rootContainer):
    log.trace("gain.internalFrameOpened")
    
    # Clear the current transaction.
    rollbackTransactionForComponent(rootContainer)

    dropdown = rootContainer.getComponent("GradeDropdown")
    dropdown.setSelectedStringValue(getUserDefaults("GRADE"))
    
# When the screen is first displayed, set widgets for user defaults
# The "active" dropdown is always initialized to "TRUE"
def internalFrameActivated(rootContainer):
    log.trace("gain.internalFrameActivated")
    requery(rootContainer)
    dropdown = rootContainer.getComponent("FamilyDropdown")
    populateRecipeFamilyDropdown(dropdown)
                                
# Called from the client startup script: View menu
# Note: No attempt is made at this point to reconcile with any tab strip
def showWindow():
    window = "DBManager/Gains"
    system.nav.openWindow(window)
    system.nav.centerWindow(window)
    
# Update database for a cell edit. We only allow edits of parameter name or 
# limits.
def update(table,row,colname,value):
    log.info("gain.update (%d:%s)=%s ..." %(row,colname,str(value)))
    txn = getTransactionForComponent(table)
    ds = table.data
    #column is LowerLimit or UpperLimit. Others are not editable.
    paramid=ds.getValueAt(row,"ParameterId")
    grade=ds.getValueAt(row,"Grade")
    SQL = "UPDATE RtGainGrade SET %s = %s WHERE ParameterId = %i and Grade = '%s'" % (colname, str(value), paramid, grade)
    log.trace(SQL)
    system.db.runUpdateQuery(SQL,tx=txn)
    
# Add a new row to the limits table for a new parameter.
# By adding a new parameter, we are adding a new parameter for every grade for the family
# Will get an error if the row exists.
def addGainParameter(button, parameter):
    rootContainer = getRootContainer(button)
    txn = rootContainer.transaction
    
    # Family
    family = rootContainer.getComponent("FamilyDropdown").selectedStringValue
    if family == "" or family == "All":
        system.gui.messageBox("Please select a specific family!")
        return
    familyId = idForFamily(getUserDefaults("FAMILY"),txn)

    # Parameter
    if parameter!=None and len(parameter)>0:
        SQL = "INSERT INTO RtGain (RecipeFamilyId, Parameter) VALUES (%i, '%s')" % (familyId, parameter)
        log.trace(SQL)
        parameterId = system.db.runUpdateQuery(SQL,tx=txn,getKey=True)
            
        # Now add a new limit row for each grade
        SQL = "INSERT INTO RtGainGrade(ParameterId, Grade) " \
            " SELECT DISTINCT %i, Grade FROM RtGradeMaster WHERE RecipeFamilyId = %i " % (parameterId, familyId)
        log.trace(SQL)
        rows=system.db.runUpdateQuery(SQL,tx=txn)
        log.info("Inserted %i rows into RtGainGrade" % (rows))
    else:
        system.gui.messageBox("Please enter a parameter name!")
        return    