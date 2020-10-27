'''
Created on Mar 21, 2017

@author: phass

Scripts in support of the "Grade Master" dialog. It also handles
the popup screen that allows grade creation and deletion
'''

import system
from ils.dbManager.ui import populateRecipeFamilyDropdown
from ils.common.util import getRootContainer
from ils.dbManager.userdefaults import get as getUserDefaults
from ils.common.error import notifyError
log = system.util.getLogger("com.ils.recipe.ui")

# When the screen is first displayed, set widgets for user defaults
# The "active" dropdown is always initialized to "TRUE"
def internalFrameOpened(component):
    log.trace("InternalFrameOpened")
    root = getRootContainer(component)
    active = root.getComponent("ActiveOnlyCheckBox")
    active.selected = True


# When the screen is first displayed, set widgets for user defaults
# The "active" dropdown is always initialized to "TRUE"
def internalFrameActivated(component):
    log.trace("InternalFrameActivated")
    container = getRootContainer(component)
    dropdown = container.getComponent("FamilyDropdown")
    populateRecipeFamilyDropdown(dropdown, includeAll=True)
    requery(container)

# Re-query the database and update the screen accordingly.
# If we get an exception, then rollback the transaction.
def requery(component):
    log.info("grademaster.requery ...")
    rootContainer = getRootContainer(component)
    table = rootContainer.getComponent("DatabaseTable")
    
    where = ""
    family = getUserDefaults("FAMILY")
    if family not in ["", "ALL", "<Family>"]:
        where = " AND F.RecipeFamilyName = '"+family+"'"

    active = rootContainer.getComponent("ActiveOnlyCheckBox")
    if active.selected:
        where = where + " AND Active=1"
    
    SQL = "SELECT F.RecipeFamilyId,F.RecipeFamilyName,GM.Grade,GM.Version,GM.Active, GM.Timestamp"\
        " FROM RtRecipeFamily F, RtGradeMaster GM"\
        " WHERE F.RecipeFamilyId = GM.RecipeFamilyId"\
        " %s "\
        " ORDER BY F.RecipeFamilyName,GM.Grade" % (where)

    log.trace(SQL)
    
    pds = system.db.runQuery(SQL)
    table.data = pds


# Clear the popup screen.
def refreshPopup(component):
    container = getRootContainer(component)
    textbox = container.getComponent("GradeTextField")
    textbox.setText("")
    dropdown = container.getComponent("FamilyDropdown")
    dropdown.setSelectedStringValue(getUserDefaults("FAMILY"))    


# Called from a button on the Grade Master screen
# (I don't think this is ever called)
def deleteGrade(component):
    container = getRootContainer(component)
    dropbox = container.getComponent("GradeDeletionDropdown")
    grade = dropbox.selectedStringValue
    family = getUserDefaults("FAMILY")
    
    confirm = system.gui.confirm("Are you sure that you want to delete grade <%S> from family <%s>?" % (grade, family))
    if confirm:
        tx = system.db.beginTransaction()
        
        try:
            # Take care of the detail, we're deleting all versions
            SQL = "DELETE FROM RtGradeDetail WHERE Grade='"+str(grade)+"' AND RecipeFamilyIdId=(SELECT RecipeFamilyId FROM RtRecipeFamily WHERE RecipeFamilyName='"+family+"')"
            system.db.runUpdateQuery(SQL, tx=tx)
            
            # Take care of the master
            SQL = "DELETE FROM RtGradeMaster WHERE Grade='"+str(grade)+"' AND RecipeFamilyId=(SELECT RecipeFamilyId FROM RtRecipeFamily WHERE RecipeFamilyName='"+family+"')"
            system.db.runUpdateQuery(SQL, tx=tx)
        except:
            system.db.rollbackTransaction(tx)
            notifyError(__name__, "Deleting a grade")
        else:
            system.db.commitTransaction(tx)
            
        system.db.closeTransaction(tx)
        
# By deleting a row, we are deleting a version for the grade.
def deleteRow(button):
    log.info("grademaster.deleteRow ...")
    container = getRootContainer(button)
    table = container.getComponent("DatabaseTable")

    rownum = table.selectedRow
    ds = table.data
    grade = ds.getValueAt(rownum,'Grade')
    familyName = ds.getValueAt(rownum,'RecipeFamilyName')
    familyId = ds.getValueAt(rownum,'RecipeFamilyId')
    vers = ds.getValueAt(rownum,'Version')
    
    confirm = system.gui.confirm("Are you sure that you want to delete grade: <%s> version: <%s> from family <%s>?" % (grade, vers, familyName))
    if confirm:
        tx = system.db.beginTransaction()
        
        try:
            # Take care of the detail, we're deleting all versions
            SQL = "DELETE FROM RtGradeDetail WHERE Grade='"+str(grade)+"' AND RecipeFamilyId="+str(familyId)+" AND Version="+str(vers)
            log.trace(SQL)
            rows = system.db.runUpdateQuery(SQL, tx=tx)
            log.trace("%i rows were deleted" % (rows))
        
            SQL = "DELETE FROM RtGradeMaster WHERE Grade='"+str(grade)+"' AND RecipeFamilyId="+str(familyId)+" AND Version="+str(vers)
            log.trace(SQL)
            rows = system.db.runUpdateQuery(SQL, tx=tx)
            log.trace("%i rows were deleted" % (rows))

        except:
            system.db.rollbackTransaction(tx)
            notifyError(__name__, "Deleing a grade")
            
        else:
            system.db.commitTransaction(tx)
            
            # Update the table
            ds = system.dataset.deleteRow(ds,rownum)
            table.data = ds
            table.selectedRow = -1
            button.setEnabled(False)
            
        system.db.closeTransaction(tx)         

#
# Add a new row to the table. The data element is a DataSet (not python)
# When complete, the button will re-query
def duplicateRow(button):
    log.info("grademaster.duplicateRow ...")
    container = getRootContainer(button)
    table = container.getComponent("DatabaseTable")
    rownum = table.selectedRow
    ds = table.data
    grade = ds.getValueAt(rownum,"Grade")
    familyId = ds.getValueAt(rownum,"RecipeFamilyId")
    vers = nextVersion(familyId,grade)
    log.infof("Duplicating family: %s, grade: %s, version: %s...", str(familyId), str(grade), str(vers - 1))

    tx = system.db.beginTransaction()
    try:
        SQL = "INSERT INTO RtGradeMaster(RecipeFamilyId,Grade,Version,Active) VALUES("+str(familyId)+",'"+str(grade)+"',"+str(vers)+",0)"
        log.trace(SQL)
        rows = system.db.runUpdateQuery(SQL, tx=tx)
        log.trace("Inserted %i rows" % (rows))
    
        # Insert rows into GradeDetail
        SQL="INSERT INTO RtGradeDetail(RecipeFamilyId, Grade, ValueId, Version, RecommendedValue, LowLimit, HighLimit) " \
            "SELECT %s, '%s', ValueId, %i, RecommendedValue, LowLimit, HighLimit FROM RtGradeDetail " \
            "WHERE RecipeFamilyId=%s and Grade='%s' and version=%i" % (str(familyId), grade, vers, str(familyId), grade, vers - 1)
        log.trace(SQL)
        rows=system.db.runUpdateQuery(SQL, tx=tx)
        log.trace("Inserted %i rows into RtGradeDetail" % (rows))
    
    except:
        system.db.rollbackTransaction(tx)
        notifyError(__name__, "Inserting a grade")
        
    else:
        system.db.commitTransaction(tx)
        
    system.db.closeTransaction(tx)
    
    checkBox=container.getComponent("ActiveOnlyCheckBox")
    if checkBox.selected:
        system.gui.messageBox("The new version was created as Inactive - in order to see it you must uncheck the 'Active Only' checkbox.")

#     
def nextVersion(familyId,grade):
    SQL = "SELECT MAX(Version) FROM RtGradeMaster WHERE Grade='"+str(grade)+"' AND RecipeFamilyId="+str(familyId)
    val = system.db.runScalarQuery(SQL)
    val = val + 1
    return val

# Called from the client startup script: View menu
# Note: No attempt is made at this point to reconcile with any tab strip
def showWindow():
    window = "DBManager/GradeMaster"
    system.nav.openWindow(window)
    system.nav.centerWindow(window)
    
'''
Update database for a cell edit. 
We only allow edits of the active flag.
Cell does a re-query
'''
def update(table,row,colname,value):
    log.info("grademaster.update, row:%d, column:%s, value:%s ..." % (row, colname, str(value)))
    
    ds = table.data
    recipeFamilyId = ds.getValueAt(row,"RecipeFamilyId")
    grade = ds.getValueAt(row,"Grade")
    vers = ds.getValueAt(row,"Version")
    print "Grade: ", grade

    # If we're clearing a value, it's easy
    if str(value) == "0":
        SQL = "UPDATE RtGradeMaster SET ACTIVE=0 WHERE RecipeFamilyId="+str(recipeFamilyId)+" AND Grade='"+str(grade)+"' AND Version="+str(vers)
        print SQL
        rows = system.db.runUpdateQuery(SQL)
        print "Updated %d rows" % (rows)
    
    else:
        # Before setting the value, we need to make all other versions inactive
        SQL = "UPDATE RtGradeMaster SET ACTIVE=0 WHERE RecipeFamilyId="+str(recipeFamilyId)+" AND Grade='"+str(grade)+"'"
        system.db.runUpdateQuery(SQL)
        
        SQL = "UPDATE RtGradeMaster SET ACTIVE=1"
        SQL = SQL+" WHERE RecipeFamilyId="+str(recipeFamilyId)+" AND Grade='"+str(grade)+"' AND Version="+str(vers)
        system.db.runUpdateQuery(SQL)


def exportCallback(event):
    entireTable = system.gui.confirm("<HTML>You can export the entire table or just the selected family and active flag.  <br>Would you like to export the <b>entire</b> table?")
    
    rootContainer = event.source.parent
    
    andWhere = ""
    if not(entireTable):
        family = getUserDefaults("FAMILY")
        if family != "ALL":
            andWhere = " AND F.RecipeFamilyName = '"+family+"'"
    
        active = rootContainer.getComponent("ActiveOnlyCheckBox")
        if active.selected:
            andWhere = andWhere + " AND Active=1"
    
    SQL = "SELECT F.RecipeFamilyId,F.RecipeFamilyName,GM.Grade,GM.Version,GM.Active, GM.Timestamp"\
        " FROM RtRecipeFamily F, RtGradeMaster GM"\
        " WHERE F.RecipeFamilyId = GM.RecipeFamilyId"\
        " %s "\
        " ORDER BY F.RecipeFamilyName, GM.Grade" % (andWhere)
    
    log.trace(SQL)

    pds = system.db.runQuery(SQL)
    csv = system.dataset.toCSV(pds)
    filePath = system.file.saveFile("GradeMaster.csv", "csv", "Comma Separated Values")
    if filePath:
        system.file.writeFile(filePath, csv)
