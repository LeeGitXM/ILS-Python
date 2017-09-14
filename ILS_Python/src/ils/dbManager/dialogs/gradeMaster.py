'''
Created on Mar 21, 2017

@author: phass

Scripts in support of the "Grade Master" dialog. It also handles
the popup screen that allows grade creation and deletion
'''

import sys, system, traceback
from ils.dbManager.ui import populateRecipeFamilyDropdown
from ils.dbManager.sql import getRootContainer, getTransactionForComponent, rollbackTransactionForComponent, closeTransactionForComponent, commitTransactionForComponent, idForFamily
from ils.dbManager.userdefaults import get as getUserDefaults
log = system.util.getLogger("com.ils.recipe.grademaster")

# Re-query the database and update the screen accordingly.
# If we get an exception, then rollback the transaction.
def requery(component):
    log.info("grademaster.requery ...")
    container = getRootContainer(component)
    table = container.getComponent("DatabaseTable")
    
    SQL = "SELECT F.RecipeFamilyId,F.RecipeFamilyName,GM.Grade,GM.Version,GM.Active, GM.Timestamp"
    SQL = SQL+" FROM RtRecipeFamily F, RtGradeMaster GM"
    SQL = SQL+" WHERE F.RecipeFamilyId = GM.RecipeFamilyId"    
    SQL = SQL + getWhereExtension(component)
    SQL = SQL + " ORDER BY F.RecipeFamilyName,GM.Grade"
    
    log.trace(SQL)
    
    txn = getTransactionForComponent(table)
    try:
        pds = system.db.runQuery(SQL,tx=txn)
        table.data = pds
    except:
        # type,value,traceback
        type,value,trace = sys.exc_info()
        print "**************"
        print traceback.format_exception(type, value,trace,100)
        print "***************"
        log.info("grademaster.requery: SQL Exception ... %s" % (str(value))) 
        rollbackTransactionForComponent(table)
        system.gui.messageBox("Error querying GradeMaster table")

    # Refresh the unit and grade dropdowns as well
#    dropdown = container.getComponent("UnitDropdown")
#    project.recipe.ui.populateUnitDropdown(dropdown)
#    dropdown = container.getComponent("GradeDropdown")
#    project.recipe.ui.populateGradeForUnitDropdown(dropdown)

# Clear the popup screen.
def refreshPopup(component):
    container = getRootContainer(component)
    textbox = container.getComponent("GradeTextField")
    textbox.setText("")
    dropdown = container.getComponent("FamilyDropdown")
    dropdown.setSelectedStringValue(getUserDefaults("FAMILY"))    


# Called from a button on the Grade Master screen
def deleteGrade(component):
    container = getRootContainer(component)
    dropbox = container.getComponent("GradeDeletionDropdown")
    grade = dropbox.selectedStringValue
    family = getUserDefaults("FAMILY")
    txn = getTransactionForComponent(component)
    # Take care of the detail, we're deleting all versions
    SQL = "DELETE FROM RtGradeDetail WHERE Grade='"+str(grade)+"' AND RecipeFamilyIdId=(SELECT RecipeFamilyId FROM RtRecipeFamily WHERE RecipeFamilyName='"+family+"')"
    system.db.runUpdateQuery(SQL,tx=txn)
    # Take care of the master
    SQL = "DELETE FROM RtGradeMaster WHERE Grade='"+str(grade)+"' AND RecipeFamilyId=(SELECT RecipeFamilyId FROM RtRecipeFamily WHERE RecipeFamilyName='"+family+"')"
    system.db.runUpdateQuery(SQL,tx=txn)
    
# By deleting a row, we are deleting a version for the grade.
def deleteRow(button):
    log.info("grademaster.deleteRow ...")
    container = getRootContainer(button)
    table = container.getComponent("DatabaseTable")
    txn = getTransactionForComponent(button)
    rownum = table.selectedRow
    ds = table.data
    grade = ds.getValueAt(rownum,'Grade')
    familyId = ds.getValueAt(rownum,'RecipeFamilyId')
    vers = ds.getValueAt(rownum,'Version')
    
    # Take care of the detail, we're deleting all versions
    SQL = "DELETE FROM RtGradeDetail WHERE Grade='"+str(grade)+"' AND RecipeFamilyId="+str(familyId)+" AND Version="+str(vers)
    log.trace(SQL)
    rows = system.db.runUpdateQuery(SQL,tx=txn)
    log.trace("%i rows were deleted" % (rows))

    SQL = "DELETE FROM RtGradeMaster WHERE Grade='"+str(grade)+"' AND RecipeFamilyId="+str(familyId)+" AND Version="+str(vers)
    log.trace(SQL)
    rows = system.db.runUpdateQuery(SQL,tx=txn)
    log.trace("%i rows were deleted" % (rows))
    
    # Update the table
    ds = system.dataset.deleteRow(ds,rownum)
    table.data = ds
    table.selectedRow = -1
    button.setEnabled(False)
#
# Add a new row to the table. The data element is a DataSet (not python)
# When complete, the button will re-query
def duplicateRow(button):
    log.info("grademaster.duplicateRow ...")
    container = getRootContainer(button)
    table = container.getComponent("DatabaseTable")
    txn = getTransactionForComponent(button)
    rownum = table.selectedRow
    ds = table.data
    grade = ds.getValueAt(rownum,"Grade")
    familyId = ds.getValueAt(rownum,"RecipeFamilyId")
    vers = nextVersion(familyId,grade,txn)
    log.infof("Duplicating family: %s, grade: %s, version: %s...", str(familyId), str(grade), str(vers - 1))
    SQL = "INSERT INTO RtGradeMaster(RecipeFamilyId,Grade,Version,Active) VALUES("+str(familyId)+",'"+str(grade)+"',"+str(vers)+",0)"
    log.trace(SQL)
    rows = system.db.runUpdateQuery(SQL,tx=txn)
    log.trace("Inserted %i rows" % (rows))

    # Insert rows into GradeDetail
    SQL="INSERT INTO RtGradeDetail(RecipeFamilyId, Grade, ValueId, Version, RecommendedValue, LowLimit, HighLimit) " \
        "SELECT %s, '%s', ValueId, %i, RecommendedValue, LowLimit, HighLimit FROM RtGradeDetail " \
        "WHERE RecipeFamilyId=%s and Grade='%s' and version=%i" % (str(familyId), grade, vers, str(familyId), grade, vers - 1)
    log.trace(SQL)
    rows=system.db.runUpdateQuery(SQL,tx=txn)
    log.trace("Inserted %i rows into RtGradeDetail" % (rows))
    
    checkBox=container.getComponent("ActiveOnlyCheckBox")
    if checkBox.selected:
        system.gui.messageBox("The new version was created as Inactive - in order to see it you must uncheck the 'Active Only' checkbox.")


def getWhereExtension(component):
    where = ""
    family = getUserDefaults("FAMILY")
    if family != "ALL":
        where = " AND F.RecipeFamilyName = '"+family+"'"
    root = getRootContainer(component)
    grade = root.grade
    if grade!="ALL":
        where = where + " AND Grade='"+grade+"'"
    active = root.getComponent("ActiveOnlyCheckBox")
    if active.selected:
        where = where + " AND Active=1"
    return where

# When the screen is first displayed, set widgets for user defaults
# The "active" dropdown is always initialized to "TRUE"
def internalFrameOpened(component):
    log.trace("InternalFrameOpened")
    container = getRootContainer(component)

    # Clear the current transaction.
    rollbackTransactionForComponent(container)
        
    dropdown = container.getComponent("FamilyDropdown")
    dropdown.setSelectedStringValue(getUserDefaults("FAMILY"))
    
    dropdown = container.getComponent("GradeDropdown")
    dropdown.setSelectedStringValue(getUserDefaults("GRADE"))

    root = getRootContainer(component)
    active = root.getComponent("ActiveOnlyCheckBox")
    active.selected = True


# When the screen is first displayed, set widgets for user defaults
# The "active" dropdown is always initialized to "TRUE"
def internalFrameActivated(component):
    log.trace("InternalFrameActivated")
    container = getRootContainer(component)
    dropdown = container.getComponent("FamilyDropdown")
    populateRecipeFamilyDropdown(dropdown)
    requery(container)

#     
def nextVersion(familyId,grade,txn):
    SQL = "SELECT MAX(Version) FROM RtGradeMaster WHERE Grade='"+str(grade)+"' AND RecipeFamilyId="+str(familyId)
    val = system.db.runScalarQuery(SQL,tx=txn)
    val = val + 1
    return val

# Called from the client startup script: View menu
# Note: No attempt is made at this point to reconcile with any tab strip
def showWindow():
    window = "DBManager/GradeMaster"
    system.nav.openWindow(window)
    system.nav.centerWindow(window)
    
#
# Update database for a cell edit. We only allow edits of the active flag.
# Cell does a re-query
def update(table,row,colname,value):
    log.info("grademaster.update (%d:%s)=%s ..." %(row,colname,str(value)))
    txn = getTransactionForComponent(table)
    ds = table.data
    #column is LowerLimit or UpperLimit. Others are not editable.
    recipeFamilyId = ds.getValueAt(row,"RecipeFamilyId")
    grade= ds.getValueAt(row,"Grade")
    vers= ds.getValueAt(row,"Version")
    # If we're clearing a value, it's easy
    if value==0:
        SQL = "UPDATE RtGradeMaster SET ACTIVE=0"
        SQL = SQL+" WHERE RecipeFamilyId="+str(recipeFamilyId)+" AND Grade='"+str(grade)+"' AND Version="+str(vers)
        system.db.runUpdateQuery(SQL,tx=txn)
    # Before setting the value, we need to make all other versions inactive
    else:
        SQL = "UPDATE RtGradeMaster SET ACTIVE=0"
        SQL = SQL+" WHERE RecipeFamilyId="+str(recipeFamilyId)+" AND Grade='"+str(grade)+"'"
        system.db.runUpdateQuery(SQL,tx=txn)
        
        SQL = "UPDATE RtGradeMaster SET ACTIVE=1"
        SQL = SQL+" WHERE RecipeFamilyId="+str(recipeFamilyId)+" AND Grade='"+str(grade)+"' AND Version="+str(vers)
        system.db.runUpdateQuery(SQL,tx=txn)
