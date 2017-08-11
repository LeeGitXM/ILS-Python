'''
Created on Mar 21, 2017

@author: phass

Scripts in support of the "Grade Detail" dialog
'''

import sys, system
from ils.dbManager.ui import populateRecipeFamilyDropdown
from ils.dbManager.sql import getRootContainer, getTransactionForComponent, rollbackTransactionForComponent, closeTransactionForComponent, commitTransactionForComponent, idForFamily
from ils.dbManager.userdefaults import get as getUserDefaults
log = system.util.getLogger("com.ils.recipe.gradedetail")

def internalFrameOpened(component):
    log.trace("InternalFrameOpened")
    root = getRootContainer(component)
    
    dropdown = root.getComponent("FamilyDropdown")
    populateRecipeFamilyDropdown(dropdown)
    dropdown.setSelectedStringValue(getUserDefaults("FAMILY"))
            
    dropdown = root.getComponent("GradeDropdown")
    dropdown.setSelectedStringValue(getUserDefaults("GRADE"))
    root.grade=getUserDefaults("GRADE")
            
    dropdown = root.getComponent("VersionDropdown")
    dropdown.setSelectedStringValue(str(root.version))

def internalFrameActivated(component):
    log.trace("InternalFrameActivated")
    requery(component)

# Re-query the database and update the screen accordingly.
# If we get an exception, then rollback the transaction.
def requery(component):
    log.info("gradedetail.requery ...")
    container = getRootContainer(component)
    table = container.getComponent("DatabaseTable")
    whereExtension = getWhereExtension(container)
    SQL = "SELECT F.RecipeFamilyId,F.RecipeFamilyName,GD.Grade,VD.ValueId,VD.PresentationOrder, "\
        " GD.Version,GM.Active,VD.Description,GD.RecommendedValue,GD.LowLimit,GD.HighLimit, VT.ValueType "\
        " FROM RtRecipeFamily F, RtGradeMaster GM, RtGradeDetail GD, RtValueDefinition VD, RtValueType VT "\
        " WHERE GD.RecipeFamilyId = F.RecipeFamilyId "\
        " AND GM.RecipeFamilyId = F.RecipeFamilyId "\
        " AND VD.RecipeFamilyId = F.RecipeFamilyId "\
        " AND GD.Grade = GM.Grade "\
        " AND GD.Version = GM.Version "\
        " AND GD.ValueId = VD.ValueId %s "\
        " AND VD.ValueTypeId = VT.ValueTypeId "\
        " ORDER BY F.RecipeFamilyName,GM.Grade,VD.PresentationOrder,GM.Version" % (whereExtension)
    log.trace(SQL)
    
    txn = getTransactionForComponent(table)
    try:
        pds = system.db.runQuery(SQL,tx=txn)
        log.info("grade.gradedetail ... SQL="+SQL)
        table.data = pds
        log.info("gradedetail.requery ... COMPLETE")
    except:
        # type,value,traceback
        type,value,trace = sys.exc_info()
        log.info("gradedetail.requery: SQL Exception: %s" % (str(value))) 
        rollbackTransactionForComponent(table)
        system.gui.messageBox("Error querying Grade Detail: %s" % (str(value)))
    
def getWhereExtension(root):
    where = ""
    
    family = getUserDefaults("FAMILY")
    if family != "ALL":
        where = " AND F.RecipeFamilyName = '"+family+"'"
        
    grade = root.grade
    grade = getUserDefaults("GRADE")
    if grade != "ALL":
        where = where+ " AND GM.Grade = '"+grade+"'"
    
    vers = root.version
    if vers != "ALL":
        where = where+ " AND GM.Version = "+ str(vers)
        
    active = root.getComponent("ActiveOnlyCheckBox")
    if active.selected:
        where = where+ " AND GM.Active = 1"    

    return where

# Called from the client startup script: View menu
# Note: No attempt is made at this point to reconcile with any tab strip
def showWindow():
    window = "DBManager/GradeDetail"
    system.nav.openWindow(window)
    system.nav.centerWindow(window)

# Update database for a cell edit. We only allow edits of parameter value or 
# limits.
def update(table,row,colname,value):
    log.info("gradedetail.update (%d:%s)=%s ..." %(row,colname,str(value)))
    txn = getTransactionForComponent(table)
    ds = table.data
    #column is LowerLimit or UpperLimit. Others are not editable.
    familyid = ds.getValueAt(row,"RecipeFamilyId")
    gradeid = ds.getValueAt(row,"Grade")
    version = ds.getValueAt(row,"Version")
    vid = ds.getValueAt(row,"ValueId")
    valueType = ds.getValueAt(row,"ValueType")
    try:
        if valueType == "Float":
            msg = "Value must be a floating point number."
            val = float(value)
        elif valueType == "Integer":
            msg = "Value must be a floating point number."
            val = int(value)

        msg = "Database Error."
        SQL = "UPDATE RtGradeDetail SET %s = '%s' " \
            " WHERE RecipeFamilyId=%i and Grade='%s' and Version = %i and ValueId = %i" \
            % (colname, str(value), familyid, str(gradeid), version, vid)
        log.trace(SQL)
        rows = system.db.runUpdateQuery(SQL,tx=txn)
        log.trace("Updated %i rows" % (rows))
    except:
        system.gui.warningBox(msg)
        ds = system.dataset.setValue(ds,row,colname,'')
        table.data = ds